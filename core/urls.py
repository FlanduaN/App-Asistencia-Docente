from django.contrib import admin
from django.urls import path, include  # <-- Importamos include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('licencias.urls')),  # <-- Conectamos nuestra app
]