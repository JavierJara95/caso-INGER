# INGER | Guion de demostración operativa para dirección

Duración sugerida: 6–9 minutos de video, ajustable al tiempo disponible.

**0:00–0:45 · Presentación del problema.** «El prototipo ayuda a consolidar información distribuida entre registros de seguimiento, interconsultas y traslados. Utiliza exclusivamente información ficticia y mantiene la responsabilidad clínica en el profesional».

**0:45–1:30 · Infraestructura y seguridad.** Mostrar solo los nombres (no los valores) de los secretos en Colab: `GROQ_API_KEY` y `LANGSMITH_API_KEY`. Mostrar el código que carga las claves automáticamente. No abrir los valores de las claves ni la consola con tokens.

**1:30–2:30 · Fuentes de Drive.** Mostrar la carpeta `INGER_Gestion_Inteligente`, los cuatro CSV y dos JSON. Explicar la recuperación de identificadores de fuente, el índice FAISS y SQLite sincronizado a Drive.

**2:30–5:30 · Agente en ejecución.** Ejecutar el notebook de forma completa. Mostrar en pantalla la tabla de ocho escenarios y destacar: resumen del caso, memoria en la segunda consulta, ruta adaptativa, validación de permisos, abstención y distinción entre ausencia y pendiente.

**5:30–6:30 · Observabilidad.** Abrir LangSmith y seleccionar el proyecto `INGER-Gestion-Inteligente`. Mostrar una traza del grafo y otra del LLM de Groq: ruta, herramientas y duración. Si no aparecen, no afirmar que la integración funciona; comprobar secretos y proyecto.

**6:30–7:30 · Cierre ejecutivo.** Resumir capacidades disponibles, indicadores a medir y limitaciones. Aclarar que no es una herramienta clínica productiva ni contiene información de pacientes reales.

**Advertencia para grabación:** nunca exponer claves, tokens ni datos identificables de pacientes. Los casos de demostración son ficticios. Comprobar que los escenarios del notebook aparecen como `OK` antes de grabar el recorrido final.
