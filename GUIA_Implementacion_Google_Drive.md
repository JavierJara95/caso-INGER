# INGER | Guía de puesta en marcha del centro de gestión inteligente

**Componentes:** Google Colab, Groq API, LangGraph, FAISS, SQLite, Google Drive y LangSmith.  
**Entorno:** demostración con información íntegramente ficticia. No utilizar datos clínicos reales.

## 1. Inicio sin subir un proyecto

1. Abre [Google Colab](https://colab.research.google.com/) e importa el archivo **`INGER_Centro_Gestion_Inteligente_Colab.ipynb`** desde tu computador (Archivo → Subir notebook). Esta operación se realiza **solo para abrir el notebook**, no para subir el proyecto completo durante su ejecución.
2. Abre **Secretos** (icono de llave del panel izquierdo). Comprueba que ya existen los secretos `GROQ_API_KEY` y `LANGSMITH_API_KEY` y activa su opción **Acceso del notebook**. No copies las claves en celdas.
3. Si tu clave de LangSmith está guardada con el nombre `LANGCHAIN_API_KEY`, el notebook también la reconoce. Los nombres alternativos para Groq son `GROQ_KEY` o `GROQ_API`.
4. Selecciona **Entorno de ejecución → Ejecutar todas**. El notebook instala librerías, lee los secretos, monta Drive, crea las bases ficticias si no existen, construye FAISS, inicia el agente, ejecuta escenarios y guarda resultados.
5. Cuando Google muestre la solicitud de acceso a Drive, **autorízala**. Es el único paso que puede requerir un clic humano; es un control de Google y **no puede eliminarse programáticamente**. El notebook no llama `input()` ni solicita credenciales por teclado.
6. Abre [LangSmith](https://smith.langchain.com/) y revisa el proyecto `INGER-Gestion-Inteligente` o el nombre configurado con el secreto opcional `LANGSMITH_PROJECT`. Las trazas pueden tardar brevemente en aparecer.

**Modelo Groq predeterminado:** `openai/gpt-oss-20b`. Si ya dispones de otro modelo compatible, puedes guardarlo como secreto opcional `GROQ_MODEL` sin modificar el código.

## 2. Estructura automática de Google Drive

En **Mi unidad** se creará la carpeta exacta `INGER_Gestion_Inteligente`:

```text
Mi unidad/
└── INGER_Gestion_Inteligente/
    ├── datos/
    │   ├── ortogeriatria_2024.csv
    │   ├── ortogeriatria_2025.csv
    │   ├── interconsultas_traslados.csv
    │   ├── documentos_referencia.csv
    │   ├── criterios_revision_demo.json
    │   └── MANIFIESTO_DATOS_SIMULADOS.json
    ├── indice_semantico/
    │   ├── indice.faiss                     [creado en ejecución]
    │   └── indice_manifest.json            [creado en ejecución]
    ├── persistencia/
    │   └── inger_memoria.sqlite            [creado en ejecución]
    └── reportes/
        ├── registro_operativo.csv          [creado en ejecución]
        └── resumen_operativo.json          [creado en ejecución]
```

- **`datos/`**: fuentes que el motor consulta; se crean la primera vez y no se sobrescriben en ejecuciones posteriores.
- **`indice_semantico/`**: modelo de embeddings multilingües y huella del corpus para reutilizar FAISS; se regenera cuando cambian las fuentes.
- **`persistencia/`**: SQLite contiene los checkpoints de LangGraph, memorias conversacionales y borradores controlados.
- **`reportes/`**: registros de los escenarios ejecutados, tiempos y errores. Se sobrescribe el resumen de la última ejecución; la memoria continúa.

SQLite se utiliza localmente mientras el notebook corre y se sincroniza a Drive mediante una copia de seguridad consistente. Este enfoque evita operar permanentemente sobre archivos SQLite dentro de la carpeta montada.

## 3. Opción alternativa: cargar previamente las bases ficticias

**No es obligatorio** cargar las bases, porque el notebook las genera automáticamente. Si deseas revisarlas o editarlas antes, utiliza `Bases_Ficticias_Google_Drive.zip`:

1. Descarga y descomprime el ZIP en tu computador. **No subas solo el ZIP**: deben estar los archivos CSV y JSON extraídos.
2. Abre Google Drive, crea `INGER_Gestion_Inteligente/datos/` en **Mi unidad**.
3. Sube los seis archivos situados dentro de la carpeta `datos/` del ZIP, conservando nombres y columnas.
4. Ejecuta el notebook. Este reutilizará los archivos que encuentre y validará sus esquemas.

Las bases se entregan con **ocho casos inventados**, tres documentos simulados y criterios de revisión *administrativa* ficticios. No representan datos reales, protocolos oficiales ni reglas aprobadas por INGER.

### Esquemas exactos

| Archivo | Columnas |
|---|---|
| `ortogeriatria_2024.csv` y `ortogeriatria_2025.csv` | `caso_id`, `fecha_alta`, `fecha_control`, `motivo_control`, `gestion_1_estado`, `gestion_1_detalle`, `gestion_2_estado`, `gestion_2_detalle` |
| `interconsultas_traslados.csv` | `caso_id`, `estado_interconsulta`, `estado_traslado`, `dias_espera_registrados`, `observacion_interconsulta`, `observacion_traslado` |
| `documentos_referencia.csv` | `fuente_id`, `titulo`, `tipo`, `contenido` |

Los `caso_id` deben tener formato `CASO-001`, `CASO-002`, etc. Las planillas originales **no se deben subir sin anonimización y autorización**. Este notebook es un entorno ficticio y no admite columnas como RUT, nombre o diagnósticos clínicos.

## 4. Capacidades demostradas sin escribir preguntas

En la parte de demostración se ejecutan automáticamente ocho escenarios:

1. Resumen y fuentes de `CASO-002`.
2. Seguimiento contextual con la pregunta «¿Y sus gestiones pendientes?» sin repetir identificador.
3. Revisión administrativa de casos según criterios simulados.
4. Consulta de un protocolo ficticio por búsqueda semántica.
5. Escritura autorizada de borrador para `CASO-004`.
6. Intento de escritura bloqueado para usuario lector.
7. Abstención por consulta sobre `CASO-999` inexistente.
8. Diferenciación entre «pendiente» y «sin registro» en `CASO-003`.

La ejecución real muestra la ruta utilizada, el tiempo, el identificador y la respuesta. Las llamadas se hacen a Groq; las trazas de LangGraph y del modelo se envían a LangSmith cuando se habilita el secreto y hay conexión.

## 5. Diagnóstico si falla alguna etapa

| Síntoma | Acción |
|---|---|
| «No se puede leer el secreto GROQ_API_KEY/LANGSMITH_API_KEY» | Verifica nombre exacto y habilita **Acceso del notebook** en el panel Secretos. |
| Aparece autorización de Drive | Autoriza el acceso a tu cuenta; es el comportamiento esperado de Colab. |
| Error descargando modelo de embeddings | Comprueba que Colab tenga Internet y vuelve a ejecutar la celda de FAISS. |
| Error de modelo de Groq | Confirma en Groq que el modelo configurado esté activo en tu cuenta; cambia el secreto opcional `GROQ_MODEL` si es necesario. |
| LangSmith no muestra trazas | Comprueba `LANGSMITH_API_KEY`, proyecto y espacio de trabajo; espera unos momentos tras la ejecución. |
| Cambié un CSV | Ejecuta nuevamente desde la carga y la indexación. El índice se reconstruye según la huella de contenido. |
| SQLite está ocupado | Reinicia el entorno de Colab y ejecuta desde arriba. No abras el mismo SQLite simultáneamente desde varios cuadernos. |
| Error en algunos escenarios | Consulta `reportes/registro_operativo.csv` en Drive y la traza individual en LangSmith. No presentes un escenario con estado `ERROR` como exitoso. |

## 6. Seguridad y alcance institucional

El notebook **no modifica registros de pacientes ni envía información real a APIs**. Groq y LangSmith sí reciben la información ficticia de las consultas y los fragmentos de demostración para generar respuestas y registrar trazas. Nunca habilites este flujo para datos identificables sin evaluación de riesgos, acuerdos de tratamiento, políticas de retención, controles de acceso e infraestructura autorizada por el hospital.

**Fuentes técnicas:**
- Groq: https://console.groq.com/docs/overview
- LangGraph SQLite: https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite
- LangSmith: https://docs.smith.langchain.com/
- Google Colab: https://research.google.com/colaboratory/intl/es/faq.html
