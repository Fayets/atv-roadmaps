"""Contratos Pydantic de ATV Roadmaps."""

from datetime import date, datetime

from pydantic import BaseModel


# ——— canales (ATV Clients, solo lectura) ———

class CanalResponse(BaseModel):
    canal: str
    categoria: str | None = None
    cliente_nombre: str | None = None
    cliente_id: int | None = None
    programa: str | None = None
    ultima_actividad: datetime | None = None
    tiene_roadmap: bool = False


# ——— roadmaps (consola del coach) ———

class RoadmapCrearRequest(BaseModel):
    canal: str
    categoria: str | None = None
    cliente_nombre: str | None = None
    cliente_id: int | None = None
    programa: str | None = None
    # La llamada de la que sale el roadmap (Fathom). La pega el coach.
    llamada_url: str | None = None


class RoadmapListItem(BaseModel):
    id: int
    token: str
    canal: str
    cliente_nombre: str
    programa: str | None = None
    coach: str
    estado: str
    actualizado_en: datetime
    tareas_totales: int = 0
    tareas_hechas: int = 0
    # Para dibujar la miniatura del documento en la lista, sin pedir el detalle.
    titulo: str | None = None
    preview: list[str] = []


class RoadmapCreadoResponse(BaseModel):
    id: int
    token: str
    link: str
    cliente_nombre: str
    canal: str
    vence_en: datetime | None = None


# ——— formulario (público, por token) ———

class OpcionSchema(BaseModel):
    id: str
    label: str


class PreguntaSchema(BaseModel):
    id: str
    label: str
    ayuda: str | None = None
    tipo: str  # texto | texto_largo | numero | opcion | opciones
    opciones: list[OpcionSchema] = []
    requerida: bool = True


class BloqueSchema(BaseModel):
    id: str
    titulo: str
    preguntas: list[PreguntaSchema]


class FormularioResponse(BaseModel):
    token: str
    cliente_nombre: str
    programa: str | None = None
    estado: str
    bloques: list[BloqueSchema]
    respuestas: dict[str, object] = {}


class FormularioEnviarRequest(BaseModel):
    respuestas: dict[str, object]


# ——— roadmap generado ———

class EntregableSchema(BaseModel):
    texto: str
    url: str | None = None


class TareaSchema(BaseModel):
    id: int | None = None
    tarea: str
    quien: str = "cliente"
    hecha: bool = False


class SemanaSchema(BaseModel):
    id: int | None = None
    etiqueta: str
    nombre: str
    tareas: list[TareaSchema] = []
    entregables: list[EntregableSchema] = []


class RoadmapDetalleResponse(BaseModel):
    token: str
    titulo: str = "Próximos pasos"
    cliente_nombre: str
    canal: str
    programa: str | None = None
    coach: str
    estado: str

    # Cabecera del mes.
    llamada_url: str | None = None
    llamada_fecha: date | None = None
    mes: str | None = None
    meta_mes: str | None = None
    foco_mes: str | None = None
    avatar: str | None = None
    como_trabajamos: str | None = None

    creado_en: datetime
    entregado_en: datetime | None = None
    semanas: list[SemanaSchema] = []
    tareas_totales: int = 0
    tareas_hechas: int = 0


class TareaEditarSchema(BaseModel):
    tarea: str
    quien: str = "cliente"


class EntregableEditarSchema(BaseModel):
    texto: str
    url: str | None = None


class SemanaEditarSchema(BaseModel):
    etiqueta: str = ""
    nombre: str = ""
    tareas: list[TareaEditarSchema] = []
    entregables: list[EntregableEditarSchema] = []


class RoadmapEditarRequest(BaseModel):
    """El documento completo tal como quedó después de que el coach lo corrigió."""

    titulo: str | None = None
    llamada_url: str | None = None
    mes: str | None = None
    meta_mes: str | None = None
    foco_mes: str | None = None
    avatar: str | None = None
    como_trabajamos: str | None = None
    semanas: list[SemanaEditarSchema] = []


class TareaCheckRequest(BaseModel):
    hecha: bool


class EstadoResponse(BaseModel):
    token: str
    estado: str
    error_detalle: str | None = None
