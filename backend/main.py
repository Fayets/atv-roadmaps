from contextlib import asynccontextmanager

from decouple import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.controllers.auth_controller import router as auth_router
from src.controllers.canales_controller import router as canales_router
from src.controllers.formulario_controller import router as formulario_router
from src.controllers.ia_controller import router as ia_router
from src.controllers.roadmaps_controller import router as roadmaps_router
from src.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="atv-roadmaps", lifespan=lifespan)

origins = [
    origin.strip()
    for origin in config("CORS_ORIGINS", default="http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(canales_router, prefix="/api/canales", tags=["canales"])
app.include_router(roadmaps_router, prefix="/api/roadmaps", tags=["roadmaps"])
app.include_router(ia_router, prefix="/api/ia", tags=["ia"])
# Sin sesión: el cliente entra con el token del link.
app.include_router(formulario_router, prefix="/api/f", tags=["formulario"])


@app.get("/health")
def health():
    return {"status": "ok"}
