from django.db import models
from django.contrib.auth.models import User

class Docente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    legajo = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.last_name}, {self.user.first_name} ({self.legajo})"


class TipoLicencia(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Curso(models.Model):
    nombre = models.CharField(max_length=50)
    turno = models.CharField(max_length=20, choices=[('MAÑANA', 'Mañana'), ('TARDE', 'Tarde'), ('NOCHE', 'Noche')])

    def __str__(self):
        return f"{self.nombre} ({self.turno})"


class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    color_hex = models.CharField(max_length=7, default='#3B82F6')

    def __str__(self):
        return self.nombre


class BloqueHorario(models.Model):
    numero = models.IntegerField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f"Bloque {self.numero} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"


class HorarioDocente(models.Model):
    DIAS_SEMANA = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
    ]
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='horarios')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    bloque = models.ForeignKey(BloqueHorario, on_delete=models.CASCADE)
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)

    def __str__(self):
        return f"{self.docente} - {self.materia} - {self.curso} - Día {self.dia_semana}"


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
    fecha_solicitud = models.DateField()
    
    tipo_incidencia = models.CharField(max_length=10, choices=TIPO_INCIDENCIA_CHOICES, default='COMPLETO')
    minutos_tarde = models.PositiveIntegerField(default=0, blank=True, null=True)
    minutos_retiro = models.PositiveIntegerField(default=0, blank=True, null=True)
    bloques_afectados = models.ManyToManyField(BloqueHorario, blank=True, help_text="Solo si aplica a bloques específicos")
    
    dia_completo = models.BooleanField(default=True)
    comprobante_pdf = models.FileField(upload_to='comprobantes/', null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"Licencia {self.docente.user.last_name} - {self.fecha_solicitud} [{self.estado}]"


class Suplencia(models.Model):
    licencia = models.ForeignKey(SolicitudLicencia, on_delete=models.CASCADE, related_name='suplencias')
    horario = models.ForeignKey(HorarioDocente, on_delete=models.CASCADE)
    docente_suplente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='suplencias_realizadas')
    fecha = models.DateField()

    def __str__(self):
        return f"Suplencia: {self.docente_suplente} en {self.horario.curso} ({self.fecha})"