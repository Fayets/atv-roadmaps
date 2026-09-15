from fastapi import APIRouter, Depends, HTTPException, Request

from src.deps import get_current_coach
from src.schemas import EstadoResponse
from src.services.ia_services import IAServices

router = APIRouter()
service = IAServices()


@router.post("/{token}/generar")
def generar(token: str, coach: str = Depends(get_current_coach)):
    """Regenerar a mano. El camino normal es automático al enviar el formulario."""
    try:
        return service.generar(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al pedir el roadmap a la IA.")


@router.get("/{token}/estado", response_model=EstadoResponse)
def estado(token: str):
    try:
        return service.estado(token)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al consultar el estado.")


@router.post("/callback")
async def callback(request: Request):
    """Lo llama la IA cuando termina un roadmap que tardó. Se autentica con la
    misma clave que se usa para salir."""
    try:
        from src.services.ia_services import API_KEY, AUTH_HEADER, AUTH_PREFIJO

        if API_KEY:
            # Se acepta por header o por query (`?k=`): el agente de la IA pega
            # en la URL que le pasamos, sin tener que armar headers.
            enviado = (
                request.query_params.get("k", "")
                or request.headers.get(AUTH_HEADER, "")
                or request.headers.get("authorization", "")
            )
            if enviado.removeprefix(AUTH_PREFIJO).removeprefix("Bearer ").strip() != API_KEY:
                raise HTTPException(status_code=401, detail="Clave inválida.")
        return service.recibir_callback(await request.json())
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Error inesperado al recibir el roadmap.")
