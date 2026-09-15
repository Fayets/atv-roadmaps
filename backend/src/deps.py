"""
Sesión compartida del ecosistema.

El coach ya se logueó en atvos.io: acá se valida la misma cookie firmada con el
mismo SECRET. Roadmaps no tiene usuarios propios ni pantalla de login.
"""

from decouple import config
from fastapi import HTTPException, Request

from src.session_utils import SESSION_COOKIE_NAME, verify_session_token

# Solo local: sin cookie del ecosistema se trabaja con un coach de desarrollo.
DEV_LOGIN = config("DEV_LOGIN", default=False, cast=bool)
DEV_COACH = config("DEV_COACH", default="local")


def get_current_coach(request: Request) -> str:
    coach = verify_session_token(request.cookies.get(SESSION_COOKIE_NAME) or "")
    if coach:
        return coach
    if DEV_LOGIN:
        return DEV_COACH
    raise HTTPException(status_code=401, detail="Sesión inválida o expirada.")
