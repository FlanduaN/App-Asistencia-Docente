# Esquema de Base de Datos (Entidades Principales)

## 1. Estructura Académica y Horarios
* **Docente:** Legajo, Usuario asociado (Login), Teléfono.
* **BloqueHorario:** Número de bloque (fijo para toda la institución), Hora Inicio, Hora Fin.
* **Materia:** Nombre, Color Hexadecimal (para UI customizable).
* **Curso:** Nombre (ej. 4to Año A).
* **HorarioDocente (Matriz cruzada):** Relaciona Docente + Día + Bloque + Materia + Curso.

## 2. Gestión de Inasistencias y Licencias
* **TipoLicencia:** Nombre, reglas (ej. requiere adjunto, requiere firma rector).
* **SolicitudLicencia:** * Relaciones: Docente, Tipo de Licencia.
    * Campos de tiempo: Fecha, Bloques afectados (para ausencias parciales).
    * [cite_start]Campos de control: Tardes en minutos, Retiros en minutos[cite: 3].
    * Archivo PDF adjunto (opcional al inicio).
    * Estado (Pendiente, Aprobada, Rechazada, Requiere Firma).
* **Suplencia / Cobertura:** * Relaciona una Licencia aprobada con un Docente Suplente.
    * [cite_start]Marca booleana (True/False) para indicar si "No se perdió la clase" (Equivalente a la "X" en planilla papel)[cite: 12].