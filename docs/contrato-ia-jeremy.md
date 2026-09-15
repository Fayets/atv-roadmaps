# Contrato con la IA que genera el roadmap

Este es el documento para pasarle a Jeremy. Define qué manda ATV Roadmaps y qué
espera de vuelta. Si su IA ya expone algo parecido con otros nombres, no hace
falta que lo cambie: se adapta del lado nuestro en
`backend/src/services/ia_services.py`, en `_normalizar_respuesta`, que es el
único lugar del sistema que conoce el formato del proveedor.

## Qué hay que generar

El entregable real de ATV en Notion: la página **"Próximos pasos"** de cada
cliente. Tiene dos partes:

1. **Cabecera del mes** — la llamada de la que sale, la meta principal, el foco,
   el avatar y cómo trabajamos según el programa.
2. **Un bloque por semana** — tareas con casillero y los entregables de esa
   semana.

El horizonte es el **mes** (normalmente cuatro semanas, que pueden agruparse:
"Semana 1 y 2"), no 90 días.

## Cuándo se llama

Apenas el cliente envía el formulario. El coach no aprieta ningún botón: enviar
el formulario es lo que dispara la generación.

## Configuración

```
ROADMAP_AI_WEBHOOK_URL=https://api.utari.ai/v1/triggers/<trigger-id>/webhook
ROADMAP_AI_KEY=sk_trigger_…
ROADMAP_AI_AUTH_HEADER=x-webhook-secret   # utari.ai usa este header, no Authorization
ROADMAP_AI_TIMEOUT=180                    # segundos
ROADMAP_AI_ESPERA_MAX_MIN=20              # cuánto esperar el callback
```

Para un proveedor que use `Authorization: Bearer`, se cambia a
`ROADMAP_AI_AUTH_HEADER=Authorization` y `ROADMAP_AI_AUTH_PREFIJO="Bearer "`.

Sin `ROADMAP_AI_WEBHOOK_URL` el sistema funciona igual: el roadmap queda en
estado `formulario_completado` y se genera después.

## Estado de la integración (15-09-2026)

El trigger de utari.ai **responde bien**: acepta la clave y arranca el worker.
Faltan dos cosas del lado de Jeremy:

1. **El agente está configurado para otro trabajo.** Hoy ese trigger dispara un
   agente de *recuperación de pagos vencidos*: pide "clientes activos",
   "problema principal", "tiene lista de clientes pasados", arma un plan de
   **14 días para generar cash rápido** y devuelve **HTML para una landing**,
   a propósito genérico y sin el nombre del cliente. No es "Próximos pasos".
   Hace falta un trigger nuevo (o reconfigurar este) con lo que describe este
   documento.
2. **La respuesta es asincrónica.** El POST devuelve
   `{"success": true, "execution": {"thread_id": …, "agent_run_id": …}}` y el
   resultado llega después. Entonces hace falta que el agente, al terminar,
   pegue en `callback_url` — o un endpoint para consultar por `agent_run_id`.
   Mientras tanto el roadmap queda en "generando" y, pasados
   `ROADMAP_AI_ESPERA_MAX_MIN`, pasa a error para que el coach no espere de
   gusto.

## Lo que se manda

`POST {ROADMAP_AI_WEBHOOK_URL}` con `Authorization: Bearer {ROADMAP_AI_KEY}`:

```json
{
  "roadmap_id": "2748df-gonza-vallejos-cc60",
  "cliente": {
    "nombre": "Gonza Vallejos",
    "canal": "gonza-vallejos",
    "programa": "Avanzados",
    "coach": "Mauri"
  },
  "llamada_url": "https://fathom.video/share/Zj-LzUWQYN41FCGubtZ6fSyVUZ6eDEPz",
  "mes": "Septiembre 2026",
  "respuestas": [
    {
      "id": "avatar",
      "bloque": "negocio",
      "pregunta": "¿A quién le vendés hoy?",
      "valor": "Creadores de contenido de fitness con 10k–80k seguidores…"
    },
    {
      "id": "piezas_venta",
      "bloque": "ventas",
      "pregunta": "¿Qué piezas del sistema ya tenés funcionando?",
      "valor": ["vsl_chat", "triage"]
    }
  ],
  "callback_url": "https://roadmaps.atvos.io/api/ia/callback"
}
```

Las respuestas van **tres veces**, para que el agente use la forma que le quede
más cómoda sin que haya que tocar nada acá:

- `respuestas` — la lista completa con `id`, `bloque`, `pregunta` y `valor`.
- `respuestas_por_id` — un mapa plano `{"avatar": "…", "facturacion_mes": "9000"}`,
  para plantillas que interpolan variables por nombre.
- `formulario_texto` — un bloque de texto con `pregunta respuesta` por línea,
  listo para pegar dentro de un prompt.

`valor` es texto, número o lista de strings, según el tipo de pregunta. El orden
de `respuestas` es el orden del formulario: primero qué vende, después los
números, la audiencia, el sistema de ventas y al final el objetivo del mes.

`llamada_url` es el Fathom de la llamada, que el coach pega al crear el roadmap.
Puede venir vacío. La lista de preguntas vive en `backend/src/formulario.py` y
puede cambiar: la IA debería leer `pregunta` y `valor`, no asumir un set fijo
de `id`.

## Lo que se espera de vuelta

Respondiendo `200` con este JSON:

```json
{
  "roadmap_id": "2748df-gonza-vallejos-cc60",
  "titulo": "Próximos pasos",
  "mes": "Septiembre 2026",
  "meta_mes": "Ordenar el contenido para que salga todas las semanas sin depender de la inspiración, e instalar el proceso de agendamiento que hoy no existe.",
  "foco_mes": "Regularidad de contenido + agendamiento. Nada de tocar el precio todavía.",
  "avatar": "Creadores de contenido de fitness con 10k–80k seguidores que ya venden planes sueltos por DM…",
  "como_trabajamos": "Avanzados no es un servicio DFY. Vos ejecutás y nosotros te acompañamos con frameworks, estructura y revisión. En este roadmap hay partes donde hacemos directo y partes donde ayudamos. Todo lo subís al Discord y ahí revisamos, damos check o corrección.",
  "semanas": [
    {
      "etiqueta": "Semana 1 y 2",
      "nombre": "Ordenar la oferta y el método",
      "tareas": [
        {
          "tarea": "Reescribir el avatar tomando tus 3 mejores clientes: quiénes pagaron más y mejores resultados tuvieron.",
          "quien": "cliente"
        },
        {
          "tarea": "Armamos con vos el mapa del método único en un Miro y te lo presentamos por Loom.",
          "quien": "nosotros"
        }
      ],
      "entregables": [
        { "texto": "Avatar reescrito + método único en Miro", "url": null },
        { "texto": "Proyecciones y limitaciones", "url": "https://…" }
      ]
    }
  ]
}
```

### Los campos, uno por uno

| Campo | Qué es |
|---|---|
| `titulo` | Casi siempre "Próximos pasos". |
| `mes` | "Septiembre 2026". Si no viene, se usa el mes en curso. |
| `meta_mes` | La meta principal del mes, en una o dos frases. |
| `foco_mes` | En qué se concentra el mes y, si sirve, qué NO se toca todavía. |
| `avatar` | El público del cliente, como quedó después del formulario. |
| `como_trabajamos` | El párrafo que aclara el modelo del programa: qué hace ATV directo y qué acompaña. Es el que evita el malentendido de que esto es DFY. |
| `semanas[].etiqueta` | "Semana 1 y 2", "Semana 3". Puede agrupar. |
| `semanas[].nombre` | El tema de esa semana. |
| `tareas[].tarea` | La línea con casillero. Una acción concreta, con el detalle suficiente para ejecutarla sin volver a preguntar. |
| `tareas[].quien` | `"nosotros"` si lo ejecuta ATV, `"cliente"` si lo ejecuta el cliente. Es el `(nosotros hacemos)` del Notion. |
| `entregables[]` | Lo que queda de la semana. `texto` obligatorio, `url` opcional. |

### Sinónimos que también se aceptan

Para no obligar a Jeremy a renombrar nada:

| Lo esperado | También se acepta |
|---|---|
| `semanas` | `weeks`, `bloques` |
| `tareas` | `pasos`, `items` |
| `entregables` | `deliverables` |
| `etiqueta` | `periodo` |
| `nombre` | `titulo` |
| `tarea` | `titulo`, `texto` |
| `quien` | `responsable` |
| `meta_mes` | `meta` |
| `foco_mes` | `foco` |
| `como_trabajamos` | `modo_trabajo` |

El roadmap puede venir en la raíz o anidado en `roadmap`, `data`, `output` o
`result`. Las tareas y los entregables también se aceptan como strings sueltos
en vez de objetos; si un string termina en `(nosotros hacemos)`, se detecta y se
marca como tarea de ATV.

## Si tarda

Si la generación lleva más que el timeout, la IA puede responder enseguida
`{"estado": "procesando"}` (sin `semanas`) y después hacer un `POST` a
`callback_url` con el mismo JSON de arriba, incluyendo `roadmap_id` y la misma
clave en `Authorization`. El roadmap queda en "generando" hasta que llegue.

## Errores

Cualquier respuesta que no sea `2xx`, o un JSON sin `semanas`, deja el roadmap
en estado `error` con el detalle visible para el coach, que puede volver a
intentarlo desde la consola. Cada intento queda guardado (payload enviado,
respuesta cruda, duración) en la tabla `roadmaps.generaciones`.
