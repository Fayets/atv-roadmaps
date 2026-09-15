# Estado del sistema — 15 de septiembre de 2026

## Lo que funciona hoy

Probado de punta a punta en local, con los 73 canales reales de ATV Clients:

- Consola del coach con los roadmaps y sus estados.
- Selector de canales leídos de ATV Clients (Postgres en el server, directorio
  de transcripts en local). Marca los canales que ya tienen un roadmap vivo.
- Creación del link con token, vencimiento y mensaje listo para copiar.
- Formulario público de cinco bloques, con validación de las requeridas y
  respuestas guardadas por pregunta.
- Llamada a la IA al enviar el formulario, con respuesta directa o por callback,
  tolerancia a nombres de campo distintos y registro de cada intento.
- Página de "Próximos pasos" con la estructura real del Notion: cabecera del
  mes, semanas, tareas con `(nosotros hacemos)` y entregables. Los casilleros
  los guarda el cliente.
- Revisión del coach y entrega.

## Lo que falta decidir (bloquea, no técnico)

1. ~~El Notion de referencia.~~ **Resuelto el 15-09-2026**: Franco pasó la
   captura de "Próximos pasos" (Clientes ATV → Premia2). La estructura ya está
   copiada: cabecera del mes (llamada de Fathom, meta principal, foco, avatar,
   cómo trabajamos) y un bloque por semana con tareas marcables, el
   `(nosotros hacemos)` y los entregables de la semana. El horizonte pasó de 90
   días a un mes.
2. **La IA de Jeremy (utari.ai).** El endpoint y la clave ya están cargados y el
   trigger responde bien. Faltan dos cosas de su lado: (a) el agente detrás de
   ese trigger hoy arma *otro* producto —un plan de 14 días de recuperación de
   pagos vencidos, en HTML para una landing—, así que hace falta un trigger
   configurado para "Próximos pasos"; (b) responde asincrónico, con
   `agent_run_id`, así que necesitamos que pegue en `callback_url` al terminar
   o un endpoint para consultar el resultado. Detalle en
   `contrato-ia-jeremy.md`.
3. **Las preguntas del formulario.** Las actuales se dedujeron de los programas.
   Son configuración: `backend/src/formulario.py`.
4. **¿Revisa el coach antes de entregar?** Está puesto como paso obligatorio.
5. **¿Quién marca los checks?** Hoy el cliente, y el coach ve el avance.

## Lo que falta construir

- Deploy: Dockerfiles, docker-compose, nginx y certificado para
  `roadmaps.atvos.io`.
- La tile en el registry de atv-ecosystem (una línea, cuando el dominio exista).
- Plantillas por programa: el bloque "Cómo trabajamos" cambia entre Boost,
  Avanzados y Advantage y hoy lo escribe la IA cada vez. Conviene fijarlo por
  programa para que siempre diga lo mismo.
- Exportar a Notion, si se quiere que la página siga viviendo también allá.
- Aviso al coach cuando un roadmap queda listo (hoy lo ve al entrar).
