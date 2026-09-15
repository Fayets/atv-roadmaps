from fastapi import APIRouter, Depends, HTTPException

from src.deps import get_current_coach
from src.schemas import (RoadmapCreadoResponse, RoadmapCrearRequest, RoadmapDetalleResponse,
                         RoadmapEditarRequest, RoadmapListItem, TareaCheckRequest)
from src.services.roadmaps_services import RoadmapsServices

router = APIRouter()
service = RoadmapsServices()


@router.get("/", response_model=list[RoadmapListItem])
def listar(coach: str = Depends(get_current_coach)):
    try:
        return service.listar()
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al listar los roadmaps.")


@router.post("/", response_model=RoadmapCreadoResponse)
def crear(body: RoadmapCrearRequest, coach: str = Depends(get_current_coach)):
    try:
        return service.crear(body, coach)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al crear el roadmap.")


@router.get("/{token}", response_model=RoadmapDetalleResponse)
def detalle(token: str, coach: str = Depends(get_current_coach)):
    try:
        return service.detalle(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al abrir el roadmap.")


@router.post("/{token}/entregar", response_model=RoadmapDetalleResponse)
def entregar(token: str, coach: str = Depends(get_current_coach)):
    try:
        return service.entregar(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al entregar el roadmap.")


@router.put("/{token}", response_model=RoadmapDetalleResponse)
def editar(token: str, body: RoadmapEditarRequest, coach: str = Depends(get_current_coach)):
    try:
        return service.editar(token, body)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al guardar el roadmap.")


@router.delete("/{token}", status_code=204)
def eliminar(token: str, coach: str = Depends(get_current_coach)):
    try:
        service.eliminar(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al eliminar el roadmap.")


@router.post("/{token}/tareas/{tarea_id}", response_model=RoadmapDetalleResponse)
def marcar_tarea(token: str, tarea_id: int, body: TareaCheckRequest, coach: str = Depends(get_current_coach)):
    try:
        return service.marcar_tarea(token, tarea_id, body.hecha)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al marcar la tarea.")
