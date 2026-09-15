"""
Entidades de ATV Roadmaps.

Un roadmap nace cuando el coach elige un canal de Discord y se genera el link.
De ahí en adelante todo cuelga del mismo registro: las respuestas del cliente,
lo que devolvió la IA (semanas, tareas y entregables) y el historial de
generaciones.

La estructura copia el entregable real de ATV en Notion ("Próximos pasos"):
una cabecera de mes —llamada, meta principal, foco, avatar y cómo trabajamos—
y después un bloque por semana con tareas marcables y los entregables de esa
semana. El horizonte es el MES, no 90 días.

El canal y el nombre del cliente se copian acá al crear el roadmap. Se leen de
ATV Clients, pero se guardan: si mañana el canal se renombra o el cliente se da
de baja, el roadmap entregado tiene que seguir diciendo lo que decía.
"""

from datetime import date, datetime

from pony.orm import Optional, PrimaryKey, Required, Set

from src.db import db, tabla

# Estados por los que pasa un roadmap, en orden.
ESTADO_LINK_ENVIADO = "link_enviado"
ESTADO_FORMULARIO_COMPLETADO = "formulario_completado"
ESTADO_GENERANDO = "generando"
ESTADO_LISTO_PARA_REVISAR = "listo_para_revisar"
ESTADO_ENTREGADO = "entregado"
ESTADO_ERROR = "error"

# Quién ejecuta cada tarea. En el Notion se marca con "(nosotros hacemos)".
QUIEN_NOSOTROS = "nosotros"
QUIEN_CLIENTE = "cliente"


class Roadmap(db.Entity):
    _table_ = tabla("roadmaps")

    id = PrimaryKey(int, auto=True)
    # Token del link público que recibe el cliente. Es la llave de /f/<token> y /r/<token>.
    token = Required(str, 64, unique=True)

    # Cliente y canal, copiados de ATV Clients al crear (ver docstring del módulo).
    canal = Required(str, 120)
    categoria = Optional(str, 60)
    cliente_nombre = Required(str, 255)
    cliente_id_clients = Optional(int, nullable=True)
    programa = Optional(str, 60)

    coach = Required(str, 80)
    estado = Required(str, 40, default=ESTADO_LINK_ENVIADO)

    # ——— Cabecera del entregable ———
    titulo = Optional(str, 255, default="Próximos pasos")
    # La llamada de la que sale el roadmap (Fathom). La carga el coach.
    llamada_url = Optional(str, sql_type="TEXT")
    llamada_fecha = Optional(date, nullable=True)
    mes = Optional(str, 60)  # "Septiembre 2026"
    meta_mes = Optional(str, sql_type="TEXT")
    foco_mes = Optional(str, sql_type="TEXT")
    avatar = Optional(str, sql_type="TEXT")
    como_trabajamos = Optional(str, sql_type="TEXT")

    creado_en = Required(datetime, default=lambda: datetime.utcnow())
    actualizado_en = Required(datetime, default=lambda: datetime.utcnow())
    vence_en = Optional(datetime, nullable=True)
    completado_en = Optional(datetime, nullable=True)
    entregado_en = Optional(datetime, nullable=True)
    error_detalle = Optional(str, sql_type="TEXT")

    respuestas = Set("Respuesta")
    semanas = Set("Semana")
    generaciones = Set("Generacion")


class Respuesta(db.Entity):
    """Una respuesta del formulario. Se guarda con la pregunta tal como se mostró:
    si mañana cambia el texto de una pregunta, los roadmaps viejos siguen leyéndose."""

    _table_ = tabla("respuestas")

    id = PrimaryKey(int, auto=True)
    roadmap = Required("Roadmap", column="roadmap_id")
    bloque = Required(str, 60)
    pregunta_id = Required(str, 80)
    pregunta = Required(str, sql_type="TEXT")
    # Texto plano, o JSON para las de opción múltiple.
    valor = Optional(str, sql_type="TEXT")
    orden = Required(int, default=0)


class Semana(db.Entity):
    """Un bloque del roadmap. `etiqueta` es lo que va en el título rojo del Notion
    ("Semana 1 y 2"), que no siempre es una sola semana."""

    _table_ = tabla("semanas")

    id = PrimaryKey(int, auto=True)
    roadmap = Required("Roadmap", column="roadmap_id")
    etiqueta = Required(str, 60)
    nombre = Required(str, 255)
    orden = Required(int, default=0)
    tareas = Set("Tarea")
    entregables = Set("Entregable")


class Tarea(db.Entity):
    """Una línea con casillero. `quien` distingue lo que ejecuta ATV de lo que
    ejecuta el cliente: en el Notion es el "(nosotros hacemos)" del final."""

    _table_ = tabla("tareas")

    id = PrimaryKey(int, auto=True)
    semana = Required("Semana", column="semana_id")
    tarea = Required(str, sql_type="TEXT")
    quien = Optional(str, 20, default=QUIEN_CLIENTE)
    orden = Required(int, default=0)

    hecha = Required(bool, default=False)
    hecha_en = Optional(datetime, nullable=True)


class Entregable(db.Entity):
    """Lo que queda de la semana: "Entregables de la semana" del Notion. Puede
    apuntar a un documento (Miro, Loom, otra página)."""

    _table_ = tabla("entregables")

    id = PrimaryKey(int, auto=True)
    semana = Required("Semana", column="semana_id")
    texto = Required(str, sql_type="TEXT")
    url = Optional(str, sql_type="TEXT")
    orden = Required(int, default=0)


class Generacion(db.Entity):
    """Cada llamada a la IA, con lo que se mandó y lo que volvió. Sirve para
    entender por qué un roadmap salió como salió sin tener que reproducirlo."""

    _table_ = tabla("generaciones")

    id = PrimaryKey(int, auto=True)
    roadmap = Required("Roadmap", column="roadmap_id")
    enviado_en = Required(datetime, default=lambda: datetime.utcnow())
    respondido_en = Optional(datetime, nullable=True)
    payload = Optional(str, sql_type="TEXT")
    respuesta = Optional(str, sql_type="TEXT")
    ok = Required(bool, default=False)
    error = Optional(str, sql_type="TEXT")
    duracion_ms = Optional(int, nullable=True)
