"""
Las preguntas del formulario que completa el cliente.

Esto es configuración, no lógica: cambiar una pregunta acá es todo lo que hace
falta para cambiar el formulario y lo que recibe la IA. El `id` de cada pregunta
es la llave con la que viaja la respuesta, así que conviene no renombrarlos una
vez que hay roadmaps generados.

El orden de los bloques es el orden en que la IA necesita el contexto: qué vende,
desde qué números arranca, con qué audiencia cuenta, qué sistema de ventas tiene
y recién al final a dónde quiere llegar este mes. El roadmap es mensual (cuatro
semanas), como el entregable real de ATV en Notion.

PENDIENTE: la lista definitiva la define Franco. Estas son las que se deducen de
los programas (avatar, método único, MVP, recurso semanal, VSL de chat, triage).
"""

BLOQUES = [
    {
        "id": "negocio",
        "titulo": "Tu negocio y tu oferta",
        "preguntas": [
            {
                "id": "avatar",
                "label": "¿A quién le vendés hoy?",
                "ayuda": "Lo más específico que puedas: a qué se dedica, qué factura, qué quiere lograr.",
                "tipo": "texto_largo",
            },
            {
                "id": "oferta",
                "label": "¿Qué le vendés y a qué precio?",
                "ayuda": "Nombre del programa o servicio, duración y precio actual.",
                "tipo": "texto_largo",
            },
            {
                "id": "metodo_unico",
                "label": "¿Tenés tu método único escrito?",
                "tipo": "opcion",
                "opciones": [
                    {"id": "si", "label": "Sí, lo puedo explicar en una llamada"},
                    {"id": "parcial", "label": "Lo tengo en la cabeza, sin escribir"},
                    {"id": "no", "label": "Todavía no"},
                ],
            },
        ],
    },
    {
        "id": "numeros",
        "titulo": "Los números de hoy",
        "preguntas": [
            {
                "id": "facturacion_mes",
                "label": "¿Cuánto facturaste el último mes? (USD)",
                "tipo": "numero",
            },
            {
                "id": "ventas_mes",
                "label": "¿Cuántas ventas del programa hiciste el último mes?",
                "tipo": "numero",
            },
            {
                "id": "llamadas_mes",
                "label": "¿Cuántas llamadas de venta tuviste el último mes?",
                "ayuda": "Las que se presentaron, no las agendadas.",
                "tipo": "numero",
            },
            {
                "id": "equipo",
                "label": "¿Con quién trabajás hoy?",
                "ayuda": "Setter, closer, editor, nadie todavía.",
                "tipo": "texto",
                "requerida": False,
            },
        ],
    },
    {
        "id": "audiencia",
        "titulo": "Audiencia y contenido",
        "preguntas": [
            {
                "id": "canales",
                "label": "¿Dónde está tu audiencia hoy?",
                "tipo": "opciones",
                "opciones": [
                    {"id": "instagram", "label": "Instagram"},
                    {"id": "youtube", "label": "YouTube"},
                    {"id": "tiktok", "label": "TikTok"},
                    {"id": "email", "label": "Email"},
                    {"id": "comunidad", "label": "Comunidad propia"},
                    {"id": "ninguno", "label": "Nada todavía"},
                ],
            },
            {
                "id": "recurso_semanal",
                "label": "¿Tenés recurso semanal publicando?",
                "ayuda": "El video de YouTube que ordena el resto del contenido de la semana.",
                "tipo": "opcion",
                "opciones": [
                    {"id": "si", "label": "Sí, todas las semanas"},
                    {"id": "a_veces", "label": "A veces"},
                    {"id": "no", "label": "No"},
                ],
            },
            {
                "id": "seguidores",
                "label": "¿Cuántos seguidores tenés en tu canal principal?",
                "tipo": "numero",
                "requerida": False,
            },
        ],
    },
    {
        "id": "ventas",
        "titulo": "Tu sistema de ventas",
        "preguntas": [
            {
                "id": "piezas_venta",
                "label": "¿Qué piezas del sistema ya tenés funcionando?",
                "tipo": "opciones",
                "opciones": [
                    {"id": "vsl_chat", "label": "VSL de chat"},
                    {"id": "agendamiento", "label": "Proceso de agendamiento"},
                    {"id": "triage", "label": "Triage"},
                    {"id": "nutricion", "label": "Nutrición previa a la llamada"},
                    {"id": "ninguna", "label": "Ninguna"},
                ],
            },
            {
                "id": "cuello_botella",
                "label": "¿Dónde sentís que se te traba hoy?",
                "ayuda": "Si tuvieras que señalar una sola cosa.",
                "tipo": "texto_largo",
            },
        ],
    },
    {
        "id": "objetivo",
        "titulo": "El objetivo del mes",
        "preguntas": [
            {
                "id": "objetivo_mes",
                "label": "¿Qué querés lograr este mes?",
                "ayuda": "Un número concreto sirve más que una intención.",
                "tipo": "texto_largo",
            },
            {
                "id": "horas_semana",
                "label": "¿Cuántas horas por semana le podés dedicar?",
                "tipo": "numero",
            },
            {
                "id": "obstaculo",
                "label": "¿Qué te impidió lograrlo hasta ahora?",
                "tipo": "texto_largo",
                "requerida": False,
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
