# Flujo de Interfaz de Usuario (UI) por Rol

## 1. Perfil Docente
* **Dashboard Principal:** Vista limpia con solicitudes "Pendientes" y "Aprobadas Futuras".
* **Botón Acción:** "Solicitar Nueva Licencia".
* **Formulario Inteligente:** Al elegir fecha, el sistema cruza con la tabla `HorarioDocente` y pregunta si afecta el día completo o bloques específicos (gestión de llegadas tarde/retiros).
* **Historial:** Pestaña secundaria con el archivo histórico de licencias propias.

## 2. Perfil Secretaría / RRHH
* **Dashboard:** Panel de control de solicitudes entrantes. Acciones: "Aprobar", "Rechazar", "Derivar a Rectoría".
* **Buscador/Filtros:** Herramienta para auditar el historial por rango de fechas o por legajo/apellido del docente.

## 3. Perfil Rectoría
* **Dashboard Simplificado:** Solo visualiza las licencias pre-filtradas por Secretaría que requieren aprobación jerárquica (Largas o Especiales). 

## 4. Perfil Regencia / Jefatura de Preceptores
* **Sistema de Visualización A/B (A definir por usuario):**
    * [cite_start]**Vista A (Modo Grilla):** Formato idéntico a la "Planilla Diaria de Asistencia Docente"[cite: 1]. [cite_start]Tabla densa con lectura horizontal (Docente, Motivos, Minutos de Tarde/Retiro, Cursos, Licencias Largas)[cite: 3, 11].
    * **Vista B (Modo Dashboard):** Línea de tiempo vertical organizada por bloques horarios. Tarjetas de alertas de ausencias para la hora actual.
* **Acción principal:** Botones directos para asignar "Suplentes" o marcar "Clase Cubierta" sin salir de la pantalla principal.