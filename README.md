# ATV Roadmaps

Del canal de Discord al plan del cliente. El coach elige el canal, el sistema
genera un link, el cliente completa el formulario y la IA devuelve la página de
**"Próximos pasos"** del mes: cabecera (llamada, meta, foco, avatar, cómo
trabajamos) y un bloque por semana con tareas y entregables. Misma estructura
que el Notion que ATV ya usa con cada cliente.

Maqueta de referencia: `docs/maqueta.html`.

## Levantarlo en local

Dos terminales. No hace falta ninguna credencial de Neon: en local es SQLite.

```bash
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.template .env
# En local, para entrar sin la cookie del ecosistema:
echo "DEV_LOGIN=1" >> .env
./.venv/bin/uvicorn main:app --reload --port 8014
```

```bash
cd frontend
npm install
npm run dev        # http://localhost:5182
```

En el vault también están cargados como `atv-roadmaps-backend` y
`atv-roadmaps-frontend` en `.claude/launch.json`.

### Los canales en local

Sin `CLIENTS_DSN`, la lista de canales sale del directorio de transcripts que
escribe el bot de ATV Clients. Apuntá `TRANSCRIPTS_BASE_PATH` ahí:

```
TRANSCRIPTS_BASE_PATH=/Users/…/Desktop/ATV/atv-clients/backend/transcripts
```

En el servidor se usa `CLIENTS_DSN` y salen del esquema `clients`. Siempre de
solo lectura: este sistema no escribe una sola fila en otro esquema.

### Probar el circuito completo sin Jeremy

`backend/scripts/ia_falsa.py` levanta una IA falsa que responde con la forma del
contrato. Correla y descomentá `ROADMAP_AI_WEBHOOK_URL` en el `.env`:

```bash
python3 backend/scripts/ia_falsa.py
```

## El flujo

1. **`/`** — consola del coach: botón grande y los roadmaps en curso.
2. **`/nuevo`** — lista de canales de ATV Clients, por categoría.
3. El sistema crea el link (y el coach puede pegar el Fathom de la llamada) y lo
   deja listo para copiar. No manda mensajes.
4. **`/f/:token`** — el cliente completa el formulario (cinco bloques).
5. Enviarlo dispara la generación con la IA (ver `docs/contrato-ia-jeremy.md`).
6. **`/r/:token`** — los próximos pasos del mes. El coach los revisa y los
   entrega; el cliente marca los casilleros y el coach ve el avance.

Estados: `link_enviado` → `formulario_completado` → `generando` →
`listo_para_revisar` → `entregado`. Los mueve el sistema solo salvo el último.

## Dónde tocar cada cosa

| Qué querés cambiar | Dónde |
|---|---|
| Las preguntas del formulario | `backend/src/formulario.py` |
| La estructura del entregable | `backend/src/models.py` (`Semana`, `Tarea`, `Entregable`) |
| El formato que habla con la IA | `backend/src/services/ia_services.py` → `_normalizar_respuesta` |
| De dónde salen los canales | `backend/src/services/canales_services.py` |
| Colores y tipografía | `frontend/src/styles/tokens.css` |
| Las llamadas al backend | `frontend/src/api.js` |

## Convenciones

Las del ecosistema, en `docs/`: raíz `frontend/` + `backend/`, dominio en
`backend/src/`, Pony con `db_session` en los servicios y controladores delgados
que solo delegan.

## Integración con el ecosistema

- Sesión: cookie `ecosystem_session`, firmada con el mismo `SECRET` de
  atv-ecosystem. No hay login propio.
- Base: la Neon compartida, esquema `roadmaps`.
- Tile del dashboard: falta agregar una entrada en
  `atv-ecosystem/frontend/src/modules/registry.js` con
  `hubPath: 'https://roadmaps.atvos.io'`. Se hace cuando el dominio esté
  levantado, para no dejar una tile que lleva a ningún lado.
- Deploy previsto: `/opt/atv-roadmaps`, puertos 8014 backend y 8094 frontend
  (libres: 8008/8088 hiring, 8010/8090 agentes, 8012/8092 ops).
