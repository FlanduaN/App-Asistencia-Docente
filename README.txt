Sistema de Asistencia y Gestión de Licencias Docentes

Requisitos Previos
Tener instalado Python 3.10 o superior (python.org).

Importante: Al instalar Python en Windows, marcar la casilla "Add Python to PATH".

Pasos de Instalación:

1. Clonar o descargar el proyecto
Abre la terminal en la carpeta raíz del proyecto (app asistencia docente).


2. Crear y activar el entorno virtual
En Windows (PowerShell):

python -m venv venv
.\venv\Scripts\activate
(Si Windows bloquea los scripts en PowerShell, ejecutar una sola vez: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser)


3. Instalar dependencias

pip install -r requirements.txt


4. Aplicar las migraciones de la Base de Datos

python manage.py migrate


5. Crear el usuario Administrador

python manage.py createsuperuser
(Sigue las instrucciones en pantalla para definir usuario y contraseña).


6. (Opcional) Cargar horarios iniciales desde Excel

python manage.py cargar_horarios horarios_colegio.xlsx


7. (Opcional) Generar la estructura del proyecto

ejecutar python mapa.py       ---      Esto generará un archivo estructura_proyecto.txt


8. Iniciar el servidor web

python manage.py runserver

Accede desde el navegador a:

Panel de Regencia: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
Panel de Administrador: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
