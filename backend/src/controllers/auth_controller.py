from fastapi import APIRouter, Depends

from src.deps import get_current_coach

router = APIRouter()


@router.get("/session")
def session(coach: str = Depends(get_current_coach)):
    """Quién está logueado. La cookie la emite atv-ecosystem; acá solo se valida."""
    return {"coach": coach}
