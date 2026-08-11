import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from licencias.models import Docente, BloqueHorario, Materia, Curso, HorarioDocente

class Command(BaseCommand):
    help = 'Carga masivamente la matriz horaria desde un archivo Excel (.xlsx)'

    def add_arguments(self, parser):
        # Permitimos pasar el nombre del archivo como argumento en la terminal
        parser.add_argument('archivo', type=str, help='Nombre del archivo Excel a procesar')

    def handle(self, *args, **options):
        archivo_excel = options['archivo']

        # Verificar si el archivo existe
        if not os.path.exists(archivo_excel):
            self.stdout.write(self.style.ERROR(f"Error: El archivo '{archivo_excel}' no existe en la raíz del proyecto."))
            return

        try:
            # 1. LEER EXCEL CON PANDAS
            df = pd.read_excel(archivo_excel)
            
            # Columnas requeridas estrictas
            columnas_esperadas = ['legajo_docente', 'dia_semana', 'numero_bloque', 'materia', 'curso']
            if not all(col in df.columns for col in columnas_esperadas):
                self.stdout.write(self.style.ERROR("Error: La plantilla no contiene las columnas requeridas."))
                return

            errores = []
            nuevos_horarios_registro = []

            # Mapeo en memoria para optimizar velocidad (Evita miles de consultas a la DB)
            dict_docentes = {d.legajo: d for d in Docente.objects.all()}
            dict_bloques = {b.numero: b for b in BloqueHorario.objects.all()}
            registros_vistos = set()

            self.stdout.write(self.style.WARNING("Fase 1: Iniciando validación de consistencia (Dry-Run)..."))

            # 2. FASE DE VALIDACIÓN (Lógica en Memoria)
            for index, row in df.iterrows():
                num_fila = index + 2 # Ajuste para el número real de fila en Excel
                
                legajo = str(row['legajo_docente']).strip()
                dia = int(row['dia_semana'])
                num_bloque = int(row['numero_bloque'])
                nombre_materia = str(row['materia']).strip()
                nombre_curso = str(row['curso']).strip()

                # Control: ¿Existe el docente?
                if legajo not in dict_docentes:
                    errores.append(f"Línea {num_fila}: El legajo '{legajo}' no existe en el sistema.")
                    continue
                
                # Control: Rango de días (Lunes=1 a Viernes=5)
                if dia < 1 or dia > 5:
                    errores.append(f"Línea {num_fila}: Día '{dia}' inválido. Debe ser de 1 a 5.")
                    continue

                # Control: ¿Existe el bloque horario en la escuela?
                if num_bloque not in dict_bloques:
                    errores.append(f"Línea {num_fila}: El Bloque Horario '{num_bloque}' no está configurado en el sistema.")
                    continue

                # Control: Superposición duplicada dentro del mismo Excel
                llave_duplicado = (legajo, dia, num_bloque)
                if llave_duplicado in registros_vistos:
                    errores.append(f"Línea {num_fila}: Conflicto. El docente ya tiene clases asignadas el día {dia}, bloque {num_bloque} en otra fila.")
                    continue
                registros_vistos.add(llave_duplicado)

                # Si pasa los controles, preparamos la carga diferida
                nuevos_horarios_registro.append({
                    'docente_obj': dict_docentes[legajo],
                    'dia': dia,
                    'bloque_obj': dict_bloques[num_bloque],
                    'materia_nombre': nombre_materia,
                    'curso_nombre': nombre_curso
                })

            # Si hay algún error, frenamos por completo el proceso
            if errores:
                self.stdout.write(self.style.ERROR("\n❌ Carga abortada. Se encontraron los siguientes errores técnicos:"))
                for err in errores:
                    self.stdout.write(self.style.ERROR(f"  - {err}"))
                return

            # 3. FASE DE INSERCIÓN ATÓMICA
            self.stdout.write(self.style.SUCCESS("Fase 1 Exitosa: Sin errores detectados. Impactando en Base de Datos..."))
            
            with transaction.atomic():
                objetos_a_crear = []
                cache_materias = {m.nombre.lower(): m for m in Materia.objects.all()}
                cache_cursos = {c.nombre.lower(): c for c in Curso.objects.all()}

                for item in nuevos_horarios_registro:
                    m_nombre_lower = item['materia_nombre'].lower()
                    c_nombre_lower = item['curso_nombre'].lower()

                    # Autocreación de Materia si no existe
                    if m_nombre_lower not in cache_materias:
                        nueva_m = Materia.objects.create(nombre=item['materia_nombre'])
                        cache_materias[m_nombre_lower] = nueva_m
                    materia_obj = cache_materias[m_nombre_lower]

                    # Autocreación de Curso si no existe
                    if c_nombre_lower not in cache_cursos:
                        nuevo_c = Curso.objects.create(nombre=item['curso_nombre'])
                        cache_cursos[c_nombre_lower] = nuevo_c
                    curso_obj = cache_cursos[c_nombre_lower]

                    # Instanciamos el registro de horario
                    objetos_a_crear.append(
                        HorarioDocente(
                            docente=item['docente_obj'],
                            dia_semana=item['dia'],
                            bloque=item['bloque_obj'],
                            materia=materia_obj,
                            curso=curso_obj
                        )
                    )

                # Bulk create: Guarda todo en una sola consulta SQL veloz
                HorarioDocente.objects.bulk_create(objetos_a_crear)

            self.stdout.write(self.style.SUCCESS(f"\n🎉 ¡Éxito total! Se cargaron correctamente {len(objetos_a_crear)} registros de horarios."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error crítico en el procesamiento: {str(e)}"))