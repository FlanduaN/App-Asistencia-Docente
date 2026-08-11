# Especificación de Arquitectura y Stack Tecnológico

## 1. Stack Base
* **Backend:** Python con framework Django.
* **Base de Datos (Desarrollo):** SQLite (integrada, sin configuración inicial).
* **Base de Datos (Producción):** PostgreSQL.
* **Frontend:** HTML5, CSS3, JavaScript renderizado desde el servidor (SSR) mediante plantillas de Django.
* **Framework CSS:** TailwindCSS (o Bootstrap 5) para garantizar un diseño responsivo y ultraligero en dispositivos móviles.

## 2. Autenticación y Seguridad
* Acceso restringido mediante cuentas de correo institucional.
* Gestión de permisos nativa de Django (Grupos: Docentes, Secretaría, Rectoría, Regencia).

## 3. Procesamiento de Archivos
* **Objetivo:** Estandarizar comprobantes y ahorrar espacio.
* **Herramientas:** Librería `Pillow` (imágenes) y utilidades de conversión de documentos.
* **Flujo:** El backend intercepta subidas (JPG, PNG, DOCX), las convierte automáticamente a PDF y las almacena de forma unificada. Las solicitudes de licencia permitirán adjuntar el archivo de forma diferida (se puede enviar el aviso temprano y adjuntar el PDF más tarde).