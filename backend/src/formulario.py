"""
Las preguntas de la ficha que completa el cliente.

Son las siete que definió Franco. Esto es configuración, no lógica: cambiar una
pregunta acá es todo lo que hace falta para cambiar el formulario y lo que
recibe la IA.

Los `id` son la llave con la que viaja cada respuesta y están elegidos para que
coincidan con los campos que el agente de utari espera en su plantilla
(qué vende y a quién, precio, clientes activos, facturación, problema principal,
cómo consigue clientes, lista de contactables). No renombrarlos sin avisar del
otro lado.

Van en dos pasos de tres y cuatro preguntas: la ficha tiene que poder llenarse
en diez minutos y dos pantallas cortas se completan más que una larga.
"""

BLOQUES = [
    {
        "id": "negocio",
        "titulo": "Tu negocio hoy",
        "preguntas": [
            {
                "id": "que_vendes",
                "label": "¿Qué vendés y a quién le vendés?",
                "ayuda": "Lo más específico que puedas: qué es la oferta y a qué tipo de persona o negocio.",
                "tipo": "texto_largo",
            },
            {
                "id": "precio",
                "label": "¿A qué precio vendés tu oferta principal?",
                "ayuda": "Si tenés varios planes, el que más vendas.",
                "tipo": "texto",
            },
            {
                "id": "clientes_activos",
                "label": "¿Cuántos clientes activos tenés ahora?",
                "tipo": "numero",
            },
            {
                "id": "facturacion_mes",
                "label": "¿Cuánto facturaste el último mes?",
                "ayuda": "En USD. Un número aproximado sirve.",
                "tipo": "numero",
            },
        ],
    },
    {
        "id": "situacion",
        "titulo": "Dónde estás trabado",
        "preguntas": [
            {
                "id": "problema_principal",
                "label": "¿Cuál es el problema principal que te frenó este mes?",
                "ayuda": "Si tuvieras que señalar una sola cosa.",
                "tipo": "texto_largo",
            },
            {
                "id": "como_consigue_clientes",
                "label": "¿Cómo conseguís clientes hoy?",
                "tipo": "opcion",
                "opciones": [
                    {"id": "organico", "label": "Orgánico"},
                    {"id": "ads", "label": "Ads"},
                    {"id": "referencias", "label": "Referencias"},
                    {"id": "todo", "label": "Todo a la vez"},
                ],
            },
            {
                "id": "lista_contactables",
                "label": "¿Tenés una lista de clientes pasados o leads con los que podrías contactarte esta semana?",
                "tipo": "opcion",
                "opciones": [
                    {"id": "si", "label": "Sí, tengo una lista"},
                    {"id": "algunos", "label": "Algunos, sueltos"},
                    {"id": "no", "label": "No tengo"},
                ],
            },
        ],
    },
]


def preguntas_planas() -> list[dict]:
    """Todas las preguntas con su bloque, en orden. Útil para guardar y validar."""
    salida: list[dict] = []
    for bloque in BLOQUES:
        for pregunta in bloque["preguntas"]:
            salida.append({**pregunta, "bloque": bloque["id"]})
    return salida


def buscar_pregunta(pregunta_id: str) -> dict | None:
    for pregunta in preguntas_planas():
        if pregunta["id"] == pregunta_id:
            return pregunta
    return None
