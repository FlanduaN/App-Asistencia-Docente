# Especificación de Proceso: Carga Masiva de Horarios

## 1. Objetivo y Arquitectura
* Permitir la carga de la matriz horaria anual en segundos, mitigando el error humano.
* **Librería Core:** `pandas` para análisis en memoria.
* **Seguridad:** Transaccionalidad Atómica (`transaction.atomic()` de Django).

## 2. Estructura de Plantilla (Excel/CSV)
Columnas requeridas:
1. `legajo_docente` (Debe existir previamente)
2. `dia_semana` (1=Lunes a 5=Viernes)
3. `numero_bloque` (Debe existir previamente)
4. `materia` (Creación automática si no existe)
5. `curso` (Creación automática si no existe)

## 3. Fases del Proceso
* **Fase 1 (Dry-Run):** El sistema lee el Excel y evalúa reglas de negocio sin guardar. Valida duplicados (un docente no puede estar en dos cursos en el mismo bloque). Si hay 1 error, se aborta y se muestra en pantalla roja (Fila y motivo).
* **Fase 2 (Bulk Create):** Si la Fase 1 es exitosa (100% libre de errores), se purgan los horarios viejos (si aplica) y se insertan todos los nuevos registros en una única transacción a la base de datos. Pantalla verde de confirmación con métricas.