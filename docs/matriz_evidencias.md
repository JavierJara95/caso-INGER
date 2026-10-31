# Matriz de trazabilidad de la EP2

| IE | Elemento implementado | Evidencia comprobable |
|---|---|---|
| IE1 Herramientas (10%) | `consultar_caso`, `buscar_contexto`, `evaluar_reglas`, `guardar_borrador` con Pydantic. | Rutas del grafo y escenario de escritura. |
| IE2 Frameworks (10%) | `StateGraph`, `ChatGroq`, `SqliteSaver`, `FAISS`, `langsmith`. | Código de `grafo.py`, `requirements.txt`, traza. |
| IE3 Memoria de contenido (10%) | Mensajes/checkpoints SQLite por hilo y memoria persistente de eventos. | Consultas consecutivas mismo hilo; prueba `test_memoria_multiturno_persistente`. |
| IE4 Recuperación semántica (10%) | Modelo de embeddings local + FAISS; filtros exactos. | Consulta documental y de caso; ver código `recuperacion.py`. |
| IE5 Planificación (10%) | Clasificación determinista + rutas condicionales y permiso de escritura. | Escenarios con salidas diferentes y `test_planificacion_adaptativa`. |
| IE6 Informe y diagramas (10%) | Word 5 páginas + `arquitectura.mmd` + README. | Archivo entregado y repositorio. |
| IE7 Adaptación (10%) | Caso con pendiente, caso resuelto, ausencia de datos, escritura autorizada/denegada. | Demostración video. |
| IE8 README/diagrama (10%) | Documentación de comandos y grafo. | `README.md`, `docs/arquitectura.mmd`. |
| IE9 Justificación (10%) | Herramientas ligadas a objetivos de EA1. | Informe y explicación en video. |
| IE10 Comunicación (10%) | Guion técnico y evidencias. | `docs/guion_video.md`. |

**Criterio de honestidad:** pruebas locales verifican lógica, no conectividad. LangSmith y Groq deberán mostrar ejecuciones reales con credenciales válidas.
