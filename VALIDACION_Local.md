# INGER | Estado de verificación técnica

- Se generó un notebook Jupyter válido con 26 celdas que incorpora todo el código necesario: no importa paquetes locales del proyecto anterior, no solicita `input()` y no requiere subir ZIP en ejecución.
- Se compiló el contenido Python de todas las celdas (salvo la instrucción `%pip`, que es magia de Colab).
- Se verificaron localmente 12 condiciones de núcleo: carga de cuatro CSV + dos JSON ficticios, enlace de ocho casos, 19 fragmentos, clasificación de intención, reglas administrativas, ausencia de datos, permisos de escritura, memoria y snapshot de SQLite.
- Se revisó la apariencia del informe en Word tras renderizar cuatro páginas.
- **No ejecutado online aquí:** Groq API, sincronización real con Drive montado, descargas del modelo SentenceTransformer y envío de trazas a LangSmith. Esto debe verificarse en Colab con permisos y claves de usuario.
- **Protección:** el notebook debe ejecutarse solamente con datos de demostración completamente ficticios.
