from django.urls import path
from . import views

urlpatterns = [
    # Autenticación y Gestión de Sesión
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
    path('cambiar-perfil/<str:perfil>/', views.cambiar_perfil, name='cambiar_perfil'),

    # Tableros Principales
    path('', views.dashboard_regencia, name='dashboard_regencia'),
    path('grilla/', views.grilla_horaria, name='grilla_horaria'),
    path('secretaria/', views.dashboard_secretaria, name='dashboard_secretaria'),
    path('mi-panel/', views.dashboard_docente, name='dashboard_docente'),

    # Gestión de Personal (Secretaría)
    path('personal/', views.gestion_docentes, name='gestion_docentes'),
    path('personal/alta/', views.alta_docente, name='alta_docente'),
    path('personal/baja/<int:docente_id>/', views.dar_de_baja_docente, name='dar_de_baja_docente'),
    path('personal/reactivar/<int:docente_id>/', views.reactivar_docente, name='reactivar_docente'),

    # Registro y Modificación de Licencias/Inasistencias
    path('registrar/', views.registrar_inasistencia, name='registrar_inasistencia'),
    path('editar/<int:licencia_id>/', views.editar_inasistencia, name='editar_inasistencia'),
    path('eliminar/<int:licencia_id>/', views.eliminar_inasistencia, name='eliminar_inasistencia'),
]