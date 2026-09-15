"""
Convierte lo que devuelve la IA en la estructura de "Próximos pasos".

Lo ideal es que mande JSON con `semanas`. Pero un agente configurado para
escupir HTML o texto suelto no puede dejar el roadmap en error: lo que importa
es el contenido, y el formato lo pone este sistema. Así que si no viene JSON,
se lee el HTML/markdown y se arma la misma estructura.

Reglas de lectura:
- Los títulos (h1..h4, o líneas `#`/`##` en markdown) abren un bloque nuevo.
  Si el título arranca con "Día 3", "Semana 1 y 2" o similar, esa parte queda
  como etiqueta y el resto como nombre.
- Los ítems de lista son las tareas de ese bloque.
- Los párrafos antes del primer título son la cabecera (meta del mes).
- Una lista que viene después de un párrafo que dice "entregables" se guarda
  como entregables en vez de tareas.
"""

from html.parser import HTMLParser
import re

# "Día 1", "Días 1-3", "Semana 1 y 2", "Week 2"
_ETIQUETA = re.compile(
    r"^\s*((?:d[ií]as?|semanas?|week|day)\s*[\d]+(?:\s*(?:[-–ya]+|al?)\s*\d+)?)\s*[:.\-–—]?\s*(.*)$",
    re.IGNORECASE,
)


class _Lector(HTMLParser):
    """Recorre el HTML y va anotando títulos, párrafos e ítems de lista."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.piezas: list[tuple[str, str]] = []  # (tipo, texto)
        self._tag: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"h1", "h2", "h3", "h4", "h5", "li", "p"}:
            self._cerrar()
            self._tag = tag

    def handle_endtag(self, tag):
        if tag == self._tag:
            self._cerrar()

    def handle_data(self, data):
        if self._tag:
            self._buffer.append(data)

    def _cerrar(self):
        if self._tag:
            texto = " ".join("".join(self._buffer).split())
            if texto:
                tipo = "titulo" if self._tag.startswith("h") else ("item" if self._tag == "li" else "parrafo")
                self.piezas.append((tipo, texto))
        self._tag = None
        self._buffer = []

    def close(self):
        super().close()
        self._cerrar()


def _piezas_de_markdown(texto: str) -> list[tuple[str, str]]:
    piezas: list[tuple[str, str]] = []
    for linea in texto.splitlines():
        limpia = linea.strip()
        if not limpia:
            continue
        if limpia.startswith("#"):
            piezas.append(("titulo", limpia.lstrip("#").strip()))
        elif re.match(r"^([-*•]|\d+[.)])\s+", limpia):
            piezas.append(("item", re.sub(r"^([-*•]|\d+[.)])\s+", "", limpia)))
        else:
            piezas.append(("parrafo", limpia))
    return piezas


def _partir_etiqueta(titulo: str) -> tuple[str, str]:
    m = _ETIQUETA.match(titulo)
    if not m:
        return "", titulo
    etiqueta, resto = m.group(1).strip(), m.group(2).strip()
    return etiqueta[:60], resto or titulo


def desde_texto(crudo: str) -> dict:
    """HTML, markdown o texto plano → la estructura de "Próximos pasos"."""
    if not crudo or not crudo.strip():
        return {}

    if "<" in crudo and ">" in crudo:
        lector = _Lector()
        lector.feed(crudo)
        lector.close()
        piezas = lector.piezas
    else:
        piezas = _piezas_de_markdown(crudo)

    if not piezas:
        return {}

    titulo = ""
    cabecera: list[str] = []
    semanas: list[dict] = []
    actual: dict | None = None
    # Una lista después de un párrafo que anuncia entregables no son tareas.
    siguiente_es_entregable = False

    for tipo, texto in piezas:
        if tipo == "titulo":
            # El primer título, si no abre un bloque con día/semana, es el título del documento.
            etiqueta, nombre = _partir_etiqueta(texto)
            if not semanas and not etiqueta and not titulo:
                titulo = texto
                continue
            actual = {
                "etiqueta": etiqueta or f"Paso {len(semanas) + 1}",
                "nombre": nombre,
                "tareas": [],
                "entregables": [],
            }
            semanas.append(actual)
            siguiente_es_entregable = False
        elif tipo == "item":
            destino = actual
            if destino is None:
                destino = {"etiqueta": "Paso 1", "nombre": "", "tareas": [], "entregables": []}
                semanas.append(destino)
                actual = destino
            if siguiente_es_entregable:
                destino["entregables"].append({"texto": texto, "url": None})
            else:
                etiqueta, nombre = _partir_etiqueta(texto)
                destino["tareas"].append({"tarea": nombre if etiqueta else texto, "quien": "cliente"})
        else:  # parrafo
            if "entregable" in texto.lower() and len(texto) < 120:
                siguiente_es_entregable = True
                continue
            siguiente_es_entregable = False
            if actual is None:
                cabecera.append(texto)
            else:
                # Un párrafo suelto dentro de un bloque describe el bloque.
                if not actual["nombre"]:
                    actual["nombre"] = texto[:255]
                else:
                    actual["tareas"].append({"tarea": texto, "quien": "cliente"})

    semanas = [s for s in semanas if s["tareas"] or s["entregables"]]
    if not semanas:
        return {}

    return {
        "titulo": titulo,
        "meta_mes": cabecera[0] if cabecera else "",
        "foco_mes": cabecera[1] if len(cabecera) > 1 else "",
        "como_trabajamos": " ".join(cabecera[2:]) if len(cabecera) > 2 else "",
        "semanas": semanas,
    }
