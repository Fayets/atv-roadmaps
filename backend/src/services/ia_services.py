"""
La IA que genera el roadmap (integración de Jeremy).

Integración externa por HTTP: no toca Pony más que para guardar el resultado.
Soporta las dos formas de trabajar del proveedor:

1. Respuesta directa — devuelve el roadmap en el mismo POST.
2. Callback — responde `{"estado": "procesando"}` y más tarde pega en
   `callback_url` con el roadmap terminado.

El contrato completo está en `docs/contrato-ia-jeremy.md`. Si el endpoint de
Jeremy usa otros nombres de campo, el único lugar que hay que tocar es
`_normalizar_respuesta`.
"""

import json
import logging
import threading
from datetime import datetime, timedelta

import httpx
from decouple import config
from fastapi import HTTPException
from pony.orm import db_session

from src.models import ESTADO_ERROR, ESTADO_GENERANDO, Generacion, Roadmap
from src.services.roadmaps_services import RoadmapsServices

_log = logging.getLogger("atv_roadmaps.ia")

WEBHOOK_URL = (config("ROADMAP_AI_WEBHOOK_URL", default="") or "").strip()
API_KEY = (config("ROADMAP_AI_KEY", default="") or "").strip()
# Cómo viaja la clave. utari.ai (la IA de Jeremy) usa `x-webhook-secret` con el
# valor pelado; otros proveedores usan `Authorization: Bearer <clave>`.
AUTH_HEADER = (config("ROADMAP_AI_AUTH_HEADER", default="x-webhook-secret") or "").strip()
AUTH_PREFIJO = config("ROADMAP_AI_AUTH_PREFIJO", default="")
TIMEOUT = config("ROADMAP_AI_TIMEOUT", default=180, cast=int)
CALLBACK_BASE = (config("CALLBACK_BASE_URL", default="") or config("PUBLIC_BASE_URL", default="")).rstrip("/")
# Cuánto se espera un callback antes de dar la generación por perdida.
ESPERA_MAX_MIN = config("ROADMAP_AI_ESPERA_MAX_MIN", default=20, cast=int)


def vencer_si_no_volvio(roadmap) -> None:
    """Un proveedor asincrónico puede aceptar el trigger y no llamar nunca al
    callback. Sin esto el roadmap se queda en "generando" para siempre y el
    coach no sabe si esperar o rehacerlo. Se llama dentro de una db_session."""
    if roadmap.estado != ESTADO_GENERANDO:
        return
    if datetime.utcnow() - roadmap.actualizado_en < timedelta(minutes=ESPERA_MAX_MIN):
        return
    roadmap.estado = ESTADO_ERROR
    roadmap.error_detalle = (
        f"La IA aceptó el pedido pero no devolvió el roadmap en {ESPERA_MAX_MIN} minutos. "
        "Se puede volver a intentar."
    )
    roadmap.actualizado_en = datetime.utcnow()


def _legible(pregunta_id: str, valor) -> str:
    """El valor como lo leería una persona.

    En las preguntas de opción, adentro se guarda el `id` (`ads`, `si`); al
    agente le sirve más la etiqueta que vio el cliente ("Ads", "Sí, tengo una
    lista"), que es lo que le da sentido a la respuesta.
    """
    from src.formulario import buscar_pregunta

    pregunta = buscar_pregunta(pregunta_id) or {}
    etiquetas = {o["id"]: o["label"] for o in pregunta.get("opciones", [])}

    if isinstance(valor, list):
        return ", ".join(etiquetas.get(str(v), str(v)) for v in valor)
    if valor is None:
        return ""
    return etiquetas.get(str(valor), str(valor))


class IAServices:
    def generar(self, token: str, *, en_background: bool = True) -> dict:
        """Marca el roadmap como generando y dispara la llamada. Devuelve enseguida:
        el coach no tiene por qué esperar dos minutos mirando una pantalla."""
        if not WEBHOOK_URL:
            raise HTTPException(
                status_code=503,
                detail="Falta configurar ROADMAP_AI_WEBHOOK_URL: todavía no está conectada la IA.",
            )

        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                raise HTTPException(status_code=404, detail="No existe ese roadmap.")
            if not roadmap.respuestas:
                raise HTTPException(status_code=400, detail="El cliente todavía no completó el formulario.")
            payload = self._armar_payload(roadmap)
            roadmap.estado = ESTADO_GENERANDO
            roadmap.error_detalle = ""
            roadmap.actualizado_en = datetime.utcnow()

        if en_background:
            threading.Thread(target=self._llamar, args=(token, payload), daemon=True, name=f"ia-{token}").start()
            return {"token": token, "estado": ESTADO_GENERANDO}

        self._llamar(token, payload)
        return {"token": token, "estado": self.estado(token)["estado"]}

    def estado(self, token: str) -> dict:
        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                raise HTTPException(status_code=404, detail="No existe ese roadmap.")
            vencer_si_no_volvio(roadmap)
            return {"token": token, "estado": roadmap.estado, "error_detalle": roadmap.error_detalle or None}

    # ——— payload ———

    def _armar_payload(self, roadmap) -> dict:
        respuestas = []
        for respuesta in sorted(roadmap.respuestas, key=lambda r: r.orden):
            crudo = respuesta.valor or ""
            valor: object = crudo
            if crudo.startswith("[") or crudo.startswith("{"):
                try:
                    valor = json.loads(crudo)
                except json.JSONDecodeError:
                    pass
            respuestas.append(
                {
                    "id": respuesta.pregunta_id,
                    "bloque": respuesta.bloque,
                    "pregunta": respuesta.pregunta,
                    "valor": valor,
                }
            )

        # Otras formas de leer lo mismo. La lista de arriba es el contrato, pero
        # las plantillas de trigger necesitan valores sueltos en la raíz.
        por_id = {r["id"]: r["valor"] for r in respuestas}
        legibles = [_legible(r["id"], r["valor"]) for r in respuestas]
        texto = "\n".join(f"{r['pregunta']} {v}" for r, v in zip(respuestas, legibles))

        # q1..qN, por posición: así lo espera la plantilla del trigger de utari
        # (`{{payload.q1}}`). Por posición y no por nombre para que agregar o
        # sacar una pregunta del formulario no rompa el mapeo del otro lado.
        por_posicion = {f"q{i + 1}": v for i, v in enumerate(legibles)}

        return {
            "roadmap_id": roadmap.token,
            "cliente": {
                "nombre": roadmap.cliente_nombre,
                "canal": roadmap.canal,
                "programa": roadmap.programa or None,
                "coach": roadmap.coach,
            },
            # La llamada de la que sale el roadmap, si el coach la cargó.
            "llamada_url": roadmap.llamada_url or None,
            "mes": roadmap.mes or None,
            "respuestas": respuestas,
            "respuestas_por_id": por_id,
            "formulario_texto": texto,
            "callback_url": f"{CALLBACK_BASE}/api/ia/callback" if CALLBACK_BASE else None,
            # Las plantillas de trigger suelen leer las variables de la raíz del
            # body o de `data`. Se mandan en los tres lugares para no depender de
            # cómo esté atado del otro lado; sobra información, no falta.
            "data": por_id,
            **por_posicion,
            **por_id,
        }

    # ——— llamada ———

    def _llamar(self, token: str, payload: dict) -> None:
        inicio = datetime.utcnow()
        headers = {"Content-Type": "application/json"}
        if API_KEY and AUTH_HEADER:
            headers[AUTH_HEADER] = f"{AUTH_PREFIJO}{API_KEY}"

        respuesta_cruda = ""
        error = ""
        datos: dict | None = None
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                r = client.post(WEBHOOK_URL, json=payload, headers=headers)
                respuesta_cruda = r.text
                r.raise_for_status()
                datos = self._normalizar_respuesta(r.json())
        except httpx.HTTPStatusError as e:
            error = f"La IA respondió {e.response.status_code}."
        except httpx.TimeoutException:
            error = f"La IA no respondió en {TIMEOUT} segundos."
        except Exception as e:  # noqa: BLE001
            error = f"No se pudo generar el roadmap: {e}"

        duracion = int((datetime.utcnow() - inicio).total_seconds() * 1000)

        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                return
            Generacion(
                roadmap=roadmap,
                enviado_en=inicio,
                respondido_en=datetime.utcnow(),
                payload=json.dumps(payload, ensure_ascii=False),
                respuesta=respuesta_cruda[:20000],
                ok=not error and bool(datos and datos.get("semanas")),
                error=error,
                duracion_ms=duracion,
            )

            if error:
                roadmap.estado = ESTADO_ERROR
                roadmap.error_detalle = error
                roadmap.actualizado_en = datetime.utcnow()
                _log.warning("Roadmap %s: %s", token, error)
                return

            # Sin semanas todavía: el proveedor avisa que sigue procesando y
            # va a pegar en el callback. Se queda en "generando".
            if not datos or not datos.get("semanas"):
                _log.info("Roadmap %s: la IA quedó procesando, se espera el callback.", token)
                return

            RoadmapsServices().guardar_generacion(roadmap, datos)

    # ——— callback ———

    def recibir_callback(self, cuerpo: dict) -> dict:
        token = cuerpo.get("roadmap_id") or cuerpo.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Falta roadmap_id.")

        datos = self._normalizar_respuesta(cuerpo)
        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                raise HTTPException(status_code=404, detail="No existe ese roadmap.")

            Generacion(
                roadmap=roadmap,
                respondido_en=datetime.utcnow(),
                respuesta=json.dumps(cuerpo, ensure_ascii=False)[:20000],
                ok=bool(datos.get("semanas")),
            )

            if not datos.get("semanas"):
                roadmap.estado = ESTADO_ERROR
                roadmap.error_detalle = cuerpo.get("error") or "La IA respondió sin semanas."
                roadmap.actualizado_en = datetime.utcnow()
                return {"ok": False, "estado": roadmap.estado}

            RoadmapsServices().guardar_generacion(roadmap, datos)
            return {"ok": True, "estado": roadmap.estado}

    # ——— adaptación ———

    @staticmethod
    def _normalizar_respuesta(cuerpo) -> dict:
        """Único punto de contacto con el formato del proveedor.

        Acepta el roadmap en la raíz o anidado en `roadmap` / `data` / `output`,
        y tolera sinónimos razonables. Si mañana Jeremy cambia los nombres, se
        agregan acá y nada más del sistema se entera."""
        if isinstance(cuerpo, str):
            try:
                cuerpo = json.loads(cuerpo)
            except json.JSONDecodeError:
                return {}
        if not isinstance(cuerpo, dict):
            return {}

        for clave in ("roadmap", "data", "output", "result"):
            anidado = cuerpo.get(clave)
            if isinstance(anidado, dict) and any(k in anidado for k in ("semanas", "weeks", "bloques")):
                cuerpo = anidado
                break

        crudas = cuerpo.get("semanas") or cuerpo.get("weeks") or cuerpo.get("bloques") or []
        semanas = []
        for i, semana in enumerate(crudas):
            if not isinstance(semana, dict):
                continue
            tareas = []
            for t in semana.get("tareas") or semana.get("pasos") or semana.get("items") or []:
                if isinstance(t, dict):
                    tareas.append(
                        {
                            "tarea": t.get("tarea") or t.get("titulo") or t.get("texto") or "",
                            "quien": t.get("quien") or t.get("responsable") or "",
                        }
                    )
                else:
                    # También se acepta el "(nosotros hacemos)" escrito en el texto.
                    texto = str(t)
                    quien = "nosotros" if "nosotros hacemos" in texto.lower() else ""
                    tareas.append({"tarea": texto, "quien": quien})

            entregables = []
            for e in semana.get("entregables") or semana.get("deliverables") or []:
                if isinstance(e, dict):
                    entregables.append(
                        {"texto": e.get("texto") or e.get("titulo") or "", "url": e.get("url")}
                    )
                else:
                    entregables.append({"texto": str(e), "url": None})

            semanas.append(
                {
                    "etiqueta": semana.get("etiqueta") or semana.get("periodo") or f"Semana {i + 1}",
                    "nombre": semana.get("nombre") or semana.get("titulo") or "",
                    "tareas": tareas,
                    "entregables": entregables,
                }
            )

        return {
            "titulo": cuerpo.get("titulo") or cuerpo.get("title") or "",
            "mes": cuerpo.get("mes") or "",
            "meta_mes": cuerpo.get("meta_mes") or cuerpo.get("meta") or "",
            "foco_mes": cuerpo.get("foco_mes") or cuerpo.get("foco") or "",
            "avatar": cuerpo.get("avatar") or "",
            "como_trabajamos": cuerpo.get("como_trabajamos") or cuerpo.get("modo_trabajo") or "",
            "semanas": semanas,
        }
