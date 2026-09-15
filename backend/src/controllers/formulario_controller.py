"""
Rutas públicas: las abre el cliente con el token del link, sin sesión.

El token es la única credencial, así que acá no se expone nada que no sea de
ese cliente.
"""

from fastapi import APIRouter, HTTPException

from src.schemas import (FormularioEnviarRequest, FormularioResponse, RoadmapDetalleResponse,
                         TareaCheckRequest)
from src.services.formulario_services import FormularioServices
from src.services.roadmaps_services import RoadmapsServices

router = APIRouter()
service = FormularioServices()
roadmaps = RoadmapsServices()


@router.get("/{token}", response_model=FormularioResponse)
def obtener(token: str):
    try:
        return service.obtener(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo abrir el formulario.")


@router.post("/{token}", response_model=FormularioResponse)
def enviar(token: str, body: FormularioEnviarRequest):
    try:
        return service.enviar(token, body.respuestas)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo enviar el formulario.")


@router.get("/{token}/roadmap", response_model=RoadmapDetalleResponse)
def ver_roadmap(token: str):
    try:
        return roadmaps.detalle(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo abrir el roadmap.")


@router.post("/{token}/roadmap/tareas/{tarea_id}", response_model=RoadmapDetalleResponse)
def marcar_tarea(token: str, tarea_id: int, body: TareaCheckRequest):
    try:
        return roadmaps.marcar_tarea(token, tarea_id, body.hecha)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo guardar el avance.")
