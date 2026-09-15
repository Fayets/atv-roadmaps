from fastapi import APIRouter, Depends, HTTPException

from src.deps import get_current_coach
from src.services.canales_services import CanalesServices

router = APIRouter()
service = CanalesServices()


@router.get("/")
def listar_canales(_coach: str = Depends(get_current_coach)):
    try:
        canales = service.listar()
        return {"canales": canales, "categorias": service.categorias(canales)}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudieron leer los canales de ATV Clients.")
