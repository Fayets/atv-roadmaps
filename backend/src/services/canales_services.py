"""
Canales de Discord, leídos de ATV Clients.

Solo lectura: este sistema nunca escribe en el esquema `clients`. La lista sale
del bot que ya sincroniza los canales, así que el coach no carga clientes a mano
y nunca hay dos listas que se contradigan.

Aunque `clients` viva en la misma base Neon que `roadmaps`, se consulta con su
propio DSN y psycopg2 en vez de con Pony: el acceso a un segundo esquema por
Pony falla (mismo gotcha documentado en ATV Ops).

Sin CLIENTS_DSN el servicio cae al directorio local de transcripts, que es lo
que hay en la Mac de desarrollo. Si tampoco está, devuelve lista vacía y el
coach puede crear el roadmap escribiendo el canal a mano.
"""

from datetime import datetime
from pathlib import Path

from decouple import config

from src.schemas import CanalResponse

CLIENTS_DSN = (config("CLIENTS_DSN", default="") or "").strip()

# Categorías de Discord que no son de clientes (anuncios, updates internos).
CATEGORIAS_IGNORADAS = {
    c.strip().lower()
    for c in (config("CATEGORIAS_IGNORADAS", default="updates") or "").split(",")
    if c.strip()
}
TRANSCRIPTS_BASE_PATH = (config("TRANSCRIPTS_BASE_PATH", default="") or "").strip()

# Una consulta, un canal por fila: el transcript más reciente de cada canal con
# el cliente ya matcheado por el bot.
_SQL = """
SELECT DISTINCT ON (t.canal)
       t.canal,
       t.categoria,
       t.fecha,
       c.id            AS cliente_id,
       c.nombre        AS cliente_nombre,
       c.plan_actual   AS programa,
       c.estado_cliente
  FROM clients.discord_transcripts t
  LEFT JOIN clients.clientes c ON c.id = t.cliente_id
 ORDER BY t.canal, t.fecha DESC
"""


def _desde_postgres() -> list[CanalResponse]:
    import psycopg2

    conn = psycopg2.connect(CLIENTS_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(_SQL)
            filas = cur.fetchall()
    finally:
        conn.close()

    canales: list[CanalResponse] = []
    for canal, categoria, fecha, cliente_id, cliente_nombre, programa, estado in filas:
        if estado == "baja" or (categoria or "").lower() in CATEGORIAS_IGNORADAS:
            continue
        canales.append(
            CanalResponse(
                canal=canal,
                categoria=categoria,
                cliente_nombre=cliente_nombre or _nombre_desde_canal(canal),
                cliente_id=cliente_id,
                programa=programa or (categoria.title() if categoria else None),
                ultima_actividad=datetime.combine(fecha, datetime.min.time()) if fecha else None,
            )
        )
    return canales


def _nombre_desde_canal(canal: str) -> str:
    """`gonza-vallejos` → `Gonza Vallejos`. Solo para canales que el bot todavía
    no matcheó con un cliente; en cuanto lo matchea manda el nombre real."""
    limpio = canal.strip().strip("┊").split("┊")[-1]
    return " ".join(parte.capitalize() for parte in limpio.replace("_", "-").split("-") if parte)


def _desde_transcripts() -> list[CanalResponse]:
    base = Path(TRANSCRIPTS_BASE_PATH)
    if not base.is_dir():
        return []

    canales: list[CanalResponse] = []
    for carpeta in sorted(base.iterdir()):
        if not carpeta.is_dir() or carpeta.name.startswith("."):
            continue
        categoria = carpeta.name
        if categoria.lower() in CATEGORIAS_IGNORADAS:
            continue
        for canal_dir in sorted(carpeta.iterdir()):
            if not canal_dir.is_dir() or canal_dir.name.startswith("."):
                continue
            archivos = sorted(canal_dir.glob("*.txt"))
            ultima = None
            if archivos:
                ultima = datetime.fromtimestamp(archivos[-1].stat().st_mtime)
            canales.append(
                CanalResponse(
                    canal=canal_dir.name,
                    categoria=categoria,
                    cliente_nombre=_nombre_desde_canal(canal_dir.name),
                    programa=categoria.title(),
                    ultima_actividad=ultima,
                )
            )
    return canales


class CanalesServices:
    def listar(self) -> list[CanalResponse]:
        canales = _desde_postgres() if CLIENTS_DSN else _desde_transcripts()
        canales.sort(key=lambda c: (c.ultima_actividad is None, -(c.ultima_actividad or datetime.min).timestamp()))
        self._marcar_con_roadmap(canales)
        return canales

    def categorias(self, canales: list[CanalResponse]) -> list[dict]:
        conteo: dict[str, int] = {}
        for canal in canales:
            clave = canal.categoria or "sin categoría"
            conteo[clave] = conteo.get(clave, 0) + 1
        return [{"id": k, "label": k.title(), "cantidad": v} for k, v in sorted(conteo.items())]

    def _marcar_con_roadmap(self, canales: list[CanalResponse]) -> None:
        """Marca los canales que ya tienen un roadmap vivo, para que el coach no
        genere dos links al mismo cliente sin darse cuenta."""
        from pony.orm import db_session

        from src.db import fetch_all
        from src.models import ESTADO_ENTREGADO, Roadmap

        with db_session:
            vivos = {
                r.canal
                for r in fetch_all(Roadmap.select())
                if r.estado != ESTADO_ENTREGADO
            }
        for canal in canales:
            canal.tiene_roadmap = canal.canal in vivos
