from django.db import models
from django.contrib.auth.models import User

# --- MODELO DOCENTE ---
class Docente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    legajo = models.CharField(max_length=20, unique=True)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    debe_cambiar_password = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.last_name}, {self.user.first_name} ({self.legajo})"

# --- MODELO TIPO DE LICENCIA ---
class TipoLicencia(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

# --- MODELO CURSO ---
class Curso(models.Model):
    nombre = models.CharField(max_length=50)
    turno = models.CharField(max_length=20, choices=[('MAÑANA', 'Mañana'), ('TARDE', 'Tarde'), ('NOCHE', 'Noche')])

    def __str__(self):
        return f"{self.nombre} ({self.turno})"


# --- MODELO MATERIA ---
class Materia(models.Model):
    MODALIDADES = [
        ('CATEDRA', 'Cátedra Única (1 Docente)'),
        ('PAREJA', 'Pareja Pedagógica (Absorbible)'),
        ('TALLER', 'Taller / Laboratorio (Por Secciones)'),
    ]

    nombre = models.CharField(max_length=100)
    tipo_modalidad = models.CharField(
        max_length=20, 
        choices=MODALIDADES, 
        default='CATEDRA',
        verbose_name="Tipo de Modalidad"
    )

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_modalidad_display()})"

# --- MODELO BLOQUE HORARIO ---
class BloqueHorario(models.Model):
    numero = models.IntegerField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f"Bloque {self.numero} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"


# --- MODELO HORARIO DOCENTE ---
class HorarioDocente(models.Model):
    ROLES = [
        ('TITULAR', 'Titular / Responsable Primario'),
        ('CO_DOCENTE', 'Co-docente / Pareja Pedagógica'),
        ('JEFE_LAB', 'Jefe de Laboratorio / Apoyo Técnico'),
    ]

    docente = models.ForeignKey('Docente', on_delete=models.CASCADE)
    bloque = models.ForeignKey('BloqueHorario', on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE)
    dia_semana = models.IntegerField(choices=[
        (1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'),
        (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado')
    ])
    
    # Campos para parejas y talleres
    rol = models.CharField(
        max_length=20, 
        choices=ROLES, 
        default='TITULAR',
        verbose_name="Rol en la Clase"
    )
    seccion = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Sección / Subgrupo (Ej: Grupo A, Taller 1)"
    )

    class Meta:
        # Nota: Asegurarse de que NO exista ninguna restricción unique_together 
        # entre (bloque, dia_semana, curso) para permitir múltiples docentes por bloque.
        verbose_name = "Horario Docente"
        verbose_name_plural = "Horarios Docentes"

    def __str__(self):
        sec_str = f" - {self.seccion}" if self.seccion else ""
        return f"{self.docente} - {self.materia.nombre}{sec_str} ({self.get_rol_display()})"

# --- MODELO SOLICITUD DE LICENCIA ---
class SolicitudLicencia(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    TIPO_INCIDENCIA_CHOICES = [
        ('COMPLETO', 'Día Completo'),
        ('TARDE', 'Llegada Tarde'),
        ('RETIRO', 'Retiro Anticipado'),
        ('BLOQUES', 'Bloques Específicos'),
    ]

    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='licencias')
    tipo_licencia = models.ForeignKey(TipoLicencia, on_delete=models.PROTECT)

    fecha_solicitud = models.DateField(verbose_name="Fecha Desde")
    fecha_hasta = models.DateField(null=True, blank=True, verbose_name="Fecha Hasta")
    
    tipo_incidencia = models.CharField(max_length=10, choices=TIPO_INCIDENCIA_CHOICES, default='COMPLETO')
    minutos_tarde = models.PositiveIntegerField(default=0, blank=True, null=True)
    minutos_retiro = models.PositiveIntegerField(default=0, blank=True, null=True)
    bloques_afectados = models.ManyToManyField(BloqueHorario, blank=True, help_text="Solo si aplica a bloques específicos")
    
    dia_completo = models.BooleanField(default=True)
    comprobante_pdf = models.FileField(upload_to='comprobantes/', null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def save(self, *args, **kwargs):
        # Si no se ingresa 'fecha_hasta', la licencia dura 1 solo día
        if not self.fecha_hasta:
            self.fecha_hasta = self.fecha_solicitud
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Licencia {self.docente.user.last_name} - {self.fecha_solicitud} [{self.estado}]"

# --- MODELO SUPLENCIA ---
class Suplencia(models.Model):
    TIPOS_COBERTURA = [
        ('EXTERNA', 'Suplente Externo'),
        ('ABSORCION', 'Absorción por Pareja Pedagógica'),
        ('JEFE_LAB', 'Asumido por Jefe de Laboratorio'),
    ]

    licencia = models.ForeignKey('SolicitudLicencia', on_delete=models.CASCADE)
    horario = models.ForeignKey(HorarioDocente, on_delete=models.CASCADE)
    fecha = models.DateField()
    
    # El docente suplente ahora es Opcional (null=True) en caso de absorción interna
    docente_suplente = models.ForeignKey(
        'Docente', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Docente Suplente (Si aplica)"
    )
    tipo_cobertura = models.CharField(
        max_length=20, 
        choices=TIPOS_COBERTURA, 
        default='EXTERNA',
        verbose_name="Tipo de Cobertura"
    )
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Cobertura {self.fecha} - {self.horario.materia.nombre} ({self.get_tipo_cobertura_display()})"