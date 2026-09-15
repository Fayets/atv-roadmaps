"""
El formulario que completa el cliente.

Es público: se abre con el token del link, sin sesión. Por eso no expone nada
del resto del sistema — solo el nombre del cliente, su programa y las preguntas.
"""

import json
from datetime import datetime

from fastapi import HTTPException
from pony.orm import db_session

from src.formulario import BLOQUES, preguntas_planas
from src.models import (ESTADO_ENTREGADO, ESTADO_FORMULARIO_COMPLETADO, ESTADO_GENERANDO,
                        ESTADO_LINK_ENVIADO, Respuesta, Roadmap)
from src.schemas import BloqueSchema, FormularioResponse


class FormularioServices:
    def obtener(self, token: str) -> FormularioResponse:
        with db_session:
            roadmap = _buscar(token)
            if roadmap.vence_en and roadmap.vence_en < datetime.utcnow() and roadmap.estado == ESTADO_LINK_ENVIADO:
                raise HTTPException(status_code=410, detail="Este link venció. Pedile uno nuevo a tu coach.")

            return FormularioResponse(
                token=roadmap.token,
                cliente_nombre=roadmap.cliente_nombre,
                programa=roadmap.programa or None,
                estado=roadmap.estado,
                bloques=[BloqueSchema(**bloque) for bloque in BLOQUES],
                respuestas=_respuestas_como_dict(roadmap),
            )

    def enviar(self, token: str, respuestas: dict) -> FormularioResponse:
        faltantes = _validar(respuestas)
        if faltantes:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan respuestas: {', '.join(faltantes)}",
            )

        with db_session:
            roadmap = _buscar(token)
            if roadmap.estado in {ESTADO_GENERANDO, ESTADO_ENTREGADO}:
                raise HTTPException(status_code=409, detail="Este formulario ya fue enviado.")

            for vieja in list(roadmap.respuestas):
                vieja.delete()

            for orden, pregunta in enumerate(preguntas_planas()):
                if pregunta["id"] not in respuestas:
                    continue
                valor = respuestas[pregunta["id"]]
                Respuesta(
                    roadmap=roadmap,
                    bloque=pregunta["bloque"],
                    pregunta_id=pregunta["id"],
                    pregunta=pregunta["label"],
                    valor=valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False),
                    orden=orden,
                )

            roadmap.estado = ESTADO_FORMULARIO_COMPLETADO
            roadmap.completado_en = datetime.utcnow()
            roadmap.actualizado_en = datetime.utcnow()

            resultado = FormularioResponse(
                token=roadmap.token,
                cliente_nombre=roadmap.cliente_nombre,
                programa=roadmap.programa or None,
                estado=roadmap.estado,
                bloques=[BloqueSchema(**bloque) for bloque in BLOQUES],
                respuestas=_respuestas_como_dict(roadmap),
            )

        # Enviar el formulario es lo que dispara la generación: el cliente no
        # tiene que hacer nada más y el coach no tiene que acordarse de apretar
        # un botón. Si la IA todavía no está configurada, queda en
        # "formulario_completado" y se genera después a mano.
        from src.services.ia_services import IAServices

        try:
            IAServices().generar(token)
            resultado.estado = ESTADO_GENERANDO
        except HTTPException as e:
            if e.status_code != 503:
                raise

        return resultado


def _buscar(token: str):
    roadmap = Roadmap.get(token=token)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="Este link no existe.")
    return roadmap


def _validar(respuestas: dict) -> list[str]:
    faltantes = []
    for pregunta in preguntas_planas():
        if not pregunta.get("requerida", True):
            continue
        valor = respuestas.get(pregunta["id"])
        if valor is None or (isinstance(valor, (str, list)) and len(valor) == 0):
            faltantes.append(pregunta["label"])
    return faltantes


def _respuestas_como_dict(roadmap) -> dict:
    salida: dict[str, object] = {}
    for respuesta in roadmap.respuestas:
        crudo = respuesta.valor or ""
        if crudo.startswith("[") or crudo.startswith("{"):
            try:
                salida[respuesta.pregunta_id] = json.loads(crudo)
                continue
            except json.JSONDecodeError:
                pass
        salida[respuesta.pregunta_id] = crudo
    return salida
