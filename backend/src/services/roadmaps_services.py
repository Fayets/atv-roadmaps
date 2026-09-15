"""Consola del coach: crear, listar, revisar y entregar roadmaps."""

import secrets
import unicodedata
from datetime import date, datetime, timedelta

from decouple import config
from fastapi import HTTPException
from pony.orm import db_session, desc

from src.db import fetch_all
from src.models import (ESTADO_ENTREGADO, ESTADO_LINK_ENVIADO, ESTADO_LISTO_PARA_REVISAR,
                        QUIEN_CLIENTE, QUIEN_NOSOTROS, Entregable, Roadmap, Semana, Tarea)
from src.schemas import (EntregableSchema, RoadmapCreadoResponse, RoadmapDetalleResponse,
                         RoadmapListItem, SemanaSchema, TareaSchema)

PUBLIC_BASE_URL = (config("PUBLIC_BASE_URL", default="http://localhost:5182") or "").rstrip("/")
DIAS_VIGENCIA_LINK = config("DIAS_VIGENCIA_LINK", default=14, cast=int)

_MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _slug(texto: str) -> str:
    """El slug va en la URL del link, así que se saca todo lo que no sea ASCII:
    `Amy y Héctor` → `amy-y-hector`."""
    plano = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    limpio = "".join(c if c.isalnum() else "-" for c in plano)
    return "-".join(p for p in limpio.split("-") if p)[:24] or "cliente"


def mes_actual() -> str:
    hoy = date.today()
    return f"{_MESES[hoy.month - 1].capitalize()} {hoy.year}"


def link_publico(token: str) -> str:
    return f"{PUBLIC_BASE_URL}/f/{token}"


class RoadmapsServices:
    # ——— crear ———

    def crear(self, body, coach: str) -> RoadmapCreadoResponse:
        canal = (body.canal or "").strip()
        if not canal:
            raise HTTPException(status_code=400, detail="Falta el canal del cliente.")

        nombre = (body.cliente_nombre or "").strip()
        if not nombre:
            from src.services.canales_services import _nombre_desde_canal

            nombre = _nombre_desde_canal(canal)

        token = f"{secrets.token_hex(3)}-{_slug(nombre)}-{secrets.token_hex(2)}"

        with db_session:
            roadmap = Roadmap(
                token=token,
                canal=canal,
                categoria=body.categoria or "",
                cliente_nombre=nombre,
                cliente_id_clients=body.cliente_id,
                programa=body.programa or "",
                coach=coach,
                estado=ESTADO_LINK_ENVIADO,
                llamada_url=(getattr(body, "llamada_url", "") or "").strip(),
                mes=mes_actual(),
                vence_en=datetime.utcnow() + timedelta(days=DIAS_VIGENCIA_LINK),
            )
            roadmap.flush()
            return RoadmapCreadoResponse(
                id=roadmap.id,
                token=roadmap.token,
                link=link_publico(roadmap.token),
                cliente_nombre=roadmap.cliente_nombre,
                canal=roadmap.canal,
                vence_en=roadmap.vence_en,
            )

    # ——— listar ———

    def listar(self, coach: str | None = None) -> list[RoadmapListItem]:
        with db_session:
            registros = fetch_all(Roadmap.select().order_by(desc(Roadmap.actualizado_en)))
            salida: list[RoadmapListItem] = []
            for roadmap in registros:
                if coach and roadmap.coach != coach:
                    continue
                totales, hechas = self._avance(roadmap)
                salida.append(
                    RoadmapListItem(
                        id=roadmap.id,
                        token=roadmap.token,
                        canal=roadmap.canal,
                        cliente_nombre=roadmap.cliente_nombre,
                        programa=roadmap.programa or None,
                        coach=roadmap.coach,
                        estado=roadmap.estado,
                        actualizado_en=roadmap.actualizado_en,
                        tareas_totales=totales,
                        tareas_hechas=hechas,
                        titulo=roadmap.titulo or None,
                        preview=self._preview(roadmap),
                    )
                )
            return salida

    @staticmethod
    def _preview(roadmap, lineas: int = 12) -> list[str]:
        """Las primeras líneas del documento, para la miniatura de la lista.
        Se arma acá y no en el frontend para que la lista siga siendo un pedido."""
        salida: list[str] = []
        if roadmap.meta_mes:
            salida.append(roadmap.meta_mes)
        if roadmap.foco_mes:
            salida.append(roadmap.foco_mes)
        for semana in sorted(roadmap.semanas, key=lambda s: s.orden):
            if len(salida) >= lineas:
                break
            titulo = semana.etiqueta
            if semana.nombre:
                titulo = f"{titulo} — {semana.nombre}"
            salida.append(titulo)
            for tarea in sorted(semana.tareas, key=lambda t: t.orden):
                if len(salida) >= lineas:
                    break
                salida.append(tarea.tarea)
        return salida[:lineas]

    # ——— detalle ———

    def detalle(self, token: str) -> RoadmapDetalleResponse:
        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                raise HTTPException(status_code=404, detail="No existe ese roadmap.")
            # Import local: ia_services importa este módulo.
            from src.services.ia_services import vencer_si_no_volvio

            vencer_si_no_volvio(roadmap)
            return self._armar_detalle(roadmap)

    def _armar_detalle(self, roadmap) -> RoadmapDetalleResponse:
        totales, hechas = self._avance(roadmap)
        return RoadmapDetalleResponse(
            token=roadmap.token,
            titulo=roadmap.titulo or "Próximos pasos",
            cliente_nombre=roadmap.cliente_nombre,
            canal=roadmap.canal,
            programa=roadmap.programa or None,
            coach=roadmap.coach,
            estado=roadmap.estado,
            llamada_url=roadmap.llamada_url or None,
            llamada_fecha=roadmap.llamada_fecha,
            mes=roadmap.mes or None,
            meta_mes=roadmap.meta_mes or None,
            foco_mes=roadmap.foco_mes or None,
            avatar=roadmap.avatar or None,
            como_trabajamos=roadmap.como_trabajamos or None,
            creado_en=roadmap.creado_en,
            entregado_en=roadmap.entregado_en,
            tareas_totales=totales,
            tareas_hechas=hechas,
            semanas=[
                SemanaSchema(
                    id=semana.id,
                    etiqueta=semana.etiqueta,
                    nombre=semana.nombre,
                    tareas=[
                        TareaSchema(
                            id=tarea.id,
                            tarea=tarea.tarea,
                            quien=tarea.quien or QUIEN_CLIENTE,
                            hecha=tarea.hecha,
                        )
                        for tarea in sorted(semana.tareas, key=lambda t: t.orden)
                    ],
                    entregables=[
                        EntregableSchema(texto=e.texto, url=e.url or None)
                        for e in sorted(semana.entregables, key=lambda e: e.orden)
                    ],
                )
                for semana in sorted(roadmap.semanas, key=lambda s: s.orden)
            ],
        )

    @staticmethod
    def _avance(roadmap) -> tuple[int, int]:
        totales = 0
        hechas = 0
        for semana in roadmap.semanas:
            for tarea in semana.tareas:
                totales += 1
                if tarea.hecha:
                    hechas += 1
        return totales, hechas

    # ——— acciones ———

    def marcar_tarea(self, token: str, tarea_id: int, hecha: bool) -> RoadmapDetalleResponse:
        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                raise HTTPException(status_code=404, detail="No existe ese roadmap.")
            tarea = Tarea.get(id=tarea_id)
            if tarea is None or tarea.semana.roadmap.id != roadmap.id:
                raise HTTPException(status_code=404, detail="Esa tarea no es de este roadmap.")
            tarea.hecha = hecha
            tarea.hecha_en = datetime.utcnow() if hecha else None
            roadmap.actualizado_en = datetime.utcnow()
            return self._armar_detalle(roadmap)

    def entregar(self, token: str) -> RoadmapDetalleResponse:
        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                raise HTTPException(status_code=404, detail="No existe ese roadmap.")
            if roadmap.estado not in {ESTADO_LISTO_PARA_REVISAR, ESTADO_ENTREGADO}:
                raise HTTPException(status_code=400, detail="El roadmap todavía no está generado.")
            roadmap.estado = ESTADO_ENTREGADO
            roadmap.entregado_en = datetime.utcnow()
            roadmap.actualizado_en = datetime.utcnow()
            return self._armar_detalle(roadmap)

    def eliminar(self, token: str) -> None:
        """Borra el roadmap y todo lo que cuelga de él. No hay papelera: si el
        coach lo borra es porque se equivocó de canal o quedó de una prueba."""
        with db_session:
            roadmap = Roadmap.get(token=token)
            if roadmap is None:
                raise HTTPException(status_code=404, detail="No existe ese roadmap.")
            for semana in list(roadmap.semanas):
                for tarea in list(semana.tareas):
                    tarea.delete()
                for entregable in list(semana.entregables):
                    entregable.delete()
                semana.delete()
            for respuesta in list(roadmap.respuestas):
                respuesta.delete()
            for generacion in list(roadmap.generaciones):
                generacion.delete()
            roadmap.delete()

    # ——— guardar lo que devolvió la IA ———

    def guardar_generacion(self, roadmap, datos: dict) -> None:
        """Reemplaza cabecera, semanas, tareas y entregables. Se llama dentro de
        una db_session abierta por quien la invoca."""
        for semana in list(roadmap.semanas):
            for tarea in list(semana.tareas):
                tarea.delete()
            for entregable in list(semana.entregables):
                entregable.delete()
            semana.delete()

        if datos.get("titulo"):
            roadmap.titulo = datos["titulo"][:255]
        if datos.get("mes"):
            roadmap.mes = datos["mes"][:60]
        roadmap.meta_mes = datos.get("meta_mes") or ""
        roadmap.foco_mes = datos.get("foco_mes") or ""
        roadmap.avatar = datos.get("avatar") or ""
        roadmap.como_trabajamos = datos.get("como_trabajamos") or ""

        for orden_semana, semana_datos in enumerate(datos.get("semanas") or []):
            semana = Semana(
                roadmap=roadmap,
                etiqueta=(semana_datos.get("etiqueta") or f"Semana {orden_semana + 1}")[:60],
                nombre=(semana_datos.get("nombre") or "")[:255],
                orden=orden_semana,
            )
            for orden_tarea, tarea_datos in enumerate(semana_datos.get("tareas") or []):
                texto = (tarea_datos.get("tarea") or "").strip()
                if not texto:
                    continue
                quien = (tarea_datos.get("quien") or "").strip().lower()
                Tarea(
                    semana=semana,
                    tarea=texto,
                    quien=QUIEN_NOSOTROS if quien in {"nosotros", "atv"} else QUIEN_CLIENTE,
                    orden=orden_tarea,
                )
            for orden_ent, ent in enumerate(semana_datos.get("entregables") or []):
                if isinstance(ent, dict):
                    texto, url = (ent.get("texto") or ent.get("titulo") or ""), ent.get("url")
                else:
                    texto, url = str(ent), None
                if not texto.strip():
                    continue
                Entregable(semana=semana, texto=texto.strip(), url=url or "", orden=orden_ent)

        roadmap.estado = ESTADO_LISTO_PARA_REVISAR
        roadmap.actualizado_en = datetime.utcnow()
