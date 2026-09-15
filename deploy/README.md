# Deploy de ATV Roadmaps en el VPS

Mismo patrón que el resto de los sistemas: repo en `/opt/atv-roadmaps`, un
`docker-compose.yml` con backend + frontend, nginx del host por subdominio.

| | Puerto host | Interno |
|---|---|---|
| backend (FastAPI) | **8014** | 8000 |
| frontend (nginx estático) | **8094** | 80 |
| dominio | `roadmaps.atvos.io` | |

Libres confirmados: 8002 clients, 8008/8088 hiring, 8010/8090 agentes,
8012/8092 ops.

## Antes de empezar

1. **DNS**: un registro `A` de `roadmaps.atvos.io` → `72.60.244.220`. Sin esto
   Certbot no puede emitir el certificado.
2. **Repo en GitHub**: crear `atvroadmaps` y hacer el primer push (ver abajo).

## Primera vez, en el VPS

```bash
cd /opt && git clone <remoto> atv-roadmaps && cd atv-roadmaps
mkdir -p /opt/atv-roadmaps/data
cp backend/.env.template backend/.env && nano backend/.env   # ver la sección siguiente
cp deploy/roadmaps.atvos.io.conf /etc/nginx/sites-enabled/roadmaps.atvos.io
nginx -t && systemctl reload nginx
certbot --nginx -d roadmaps.atvos.io
docker compose up -d --build
curl -s https://roadmaps.atvos.io/health
```

## `backend/.env` en el server

```ini
# Base: la Neon compartida del ecosistema, esquema propio.
# Las credenciales son las mismas del .env de atv-ecosystem / atv-ops.
DB_PROVIDER=postgres
DB_SCHEMA=roadmaps
DB_HOST=<host de la Neon compartida>
DB_PORT=5432
DB_USER=<usuario>
DB_PASS=<clave>
DB_NAME=neondb
DB_SSLMODE=require

# Canales de Discord: se LEEN del esquema clients. Aunque viva en la misma base,
# hay que setear el DSN aparte (Pony falla contra un segundo esquema).
CLIENTS_DSN=postgresql://<usuario>:<clave>@<host>/neondb?sslmode=require

# Sesión compartida del ecosistema: MISMO valor que el SECRET de atv-ecosystem.
# Con esto el coach entra sin volver a loguearse.
SECRET=<el SECRET de atv-ecosystem, idéntico>
# IMPORTANTE: en el server va en 0. Con 1 cualquiera entra sin sesión.
DEV_LOGIN=0

# Base de los links que se le mandan al cliente.
PUBLIC_BASE_URL=https://roadmaps.atvos.io
CORS_ORIGINS=https://roadmaps.atvos.io,https://atvos.io

# IA de Jeremy (utari.ai). Mientras el trigger siga apuntando al agente de
# cobranza, dejar la URL vacía: el roadmap queda en "formulario_completado" y se
# genera cuando esté el trigger correcto. Ver docs/contrato-ia-jeremy.md.
ROADMAP_AI_WEBHOOK_URL=
ROADMAP_AI_KEY=sk_trigger_...
ROADMAP_AI_AUTH_HEADER=x-webhook-secret
ROADMAP_AI_TIMEOUT=180
ROADMAP_AI_ESPERA_MAX_MIN=20

# Categorías de Discord que no son clientes.
CATEGORIAS_IGNORADAS=updates
```

**No** poner `TRANSCRIPTS_BASE_PATH` en el server: ahí los canales salen de
Postgres por `CLIENTS_DSN`. El directorio de transcripts es el atajo local.

## Actualizar

```bash
cd /opt/atv-roadmaps && git config pull.rebase false && git pull origin master && docker compose up -d --build
```

## Comprobar que quedó bien

```bash
curl -s https://roadmaps.atvos.io/health
# {"status":"ok"}

# Con sesión del ecosistema, la lista de canales tiene que traer los 73 reales:
curl -s https://roadmaps.atvos.io/api/canales/ -H 'Cookie: ecosystem_session=<tu cookie>' | head -c 300

# Sin sesión tiene que dar 401 (si da 200, DEV_LOGIN quedó en 1):
curl -s -o /dev/null -w '%{http_code}\n' https://roadmaps.atvos.io/api/roadmaps/
```

## Qué toca de otros sistemas

Solo una línea en **atv-ecosystem**: la tile del dashboard en
`frontend/src/modules/registry.js`. Nada más, y ningún dato de otro sistema: el
esquema `clients` se lee, nunca se escribe.
