from django.contrib import admin
from .models import Docente, BloqueHorario, Materia, Curso, HorarioDocente, TipoLicencia, SolicitudLicencia, Suplencia

# Configuraciones personalizadas para que el panel sea más interactivo
@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ('legajo', 'get_apellido', 'get_nombre', 'telefono')
    search_fields = ('legajo', 'user__last_name', 'user__first_name')

    def get_apellido(self, obj):
        return obj.user.last_name
    get_apellido.short_description = 'Apellido'

    def get_nombre(self, obj):
        return obj.user.first_name
    get_nombre.short_description = 'Nombre'

@admin.register(HorarioDocente)
class HorarioDocenteAdmin(admin.ModelAdmin):
    list_display = ('docente', 'dia_semana', 'bloque', 'materia', 'curso')
    list_filter = ('dia_semana', 'curso', 'materia')
    search_fields = ('docente__user__last_name', 'curso__nombre')

@admin.register(SolicitudLicencia)
class SolicitudLicenciaAdmin(admin.ModelAdmin):
    list_display = ('docente', 'tipo_licencia', 'fecha_solicitud', 'estado', 'dia_completo')
    list_filter = ('estado', 'fecha_solicitud', 'tipo_licencia')
    search_fields = ('docente__user__last_name',)
    date_hierarchy = 'fecha_solicitud'

# Registros simples para el resto de las tablas de configuración
admin.site.register(BloqueHorario)
admin.site.register(Materia)
admin.site.register(Curso)
admin.site.register(TipoLicencia)
admin.site.register(Suplencia)