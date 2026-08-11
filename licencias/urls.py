from django.urls import path
from . import views

urlpatterns = [
    # Autenticación y Conmutador
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cambiar-perfil/<str:perfil>/', views.cambiar_perfil, name='cambiar_perfil'),

    # Vistas de Perfiles
    path('', views.dashboard_regencia, name='dashboard_regencia'),
    path('grilla/', views.grilla_horaria, name='grilla_horaria'),
    path('secretaria/', views.dashboard_secretaria, name='dashboard_secretaria'),

    # Operaciones
    path('registrar/', views.registrar_inasistencia, name='registrar_inasistencia'),
    path('editar/<int:licencia_id>/', views.editar_inasistencia, name='editar_inasistencia'),
    path('eliminar/<int:licencia_id>/', views.eliminar_inasistencia, name='eliminar_inasistencia'),
]