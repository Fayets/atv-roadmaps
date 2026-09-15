"""
IA falsa para probar el pipeline sin depender del endpoint de Jeremy.

    python3 scripts/ia_falsa.py

y en backend/.env:

    ROADMAP_AI_WEBHOOK_URL=http://127.0.0.1:8999/roadmap

Devuelve un roadmap con la forma del contrato (docs/contrato-ia-jeremy.md), y a
propósito usa sinónimos (`weeks`, `pasos`, `deliverables`) y el "(nosotros
hacemos)" escrito dentro del texto en la última semana, para verificar que la
normalización los acepta.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

ROADMAP = {
    "titulo": "Próximos pasos",
    "mes": "Septiembre 2026",
    "meta_mes": (
        "Ordenar el contenido para que salga todas las semanas sin depender de la inspiración, "
        "e instalar el proceso de agendamiento que hoy no existe."
    ),
    "foco_mes": "Regularidad de contenido + agendamiento. Nada de tocar el precio todavía.",
    "avatar": (
        "Creadores de contenido de fitness con 10k-80k seguidores que ya venden planes sueltos "
        "por DM y quieren pasar a un programa de 3 meses con acompanamiento."
    ),
    "como_trabajamos": (
        "Avanzados no es un servicio DFY. Vos ejecutas y nosotros te acompanamos con frameworks, "
        "estructura y revision. En este roadmap hay partes donde hacemos directo (el guion del "
        "recurso semanal y el flujo de agendamiento) y partes donde ayudamos (revision de reels, "
        "KPIs). Todo lo subis al Discord y ahi revisamos, damos check o correccion."
    ),
    "semanas": [
        {
            "etiqueta": "Semana 1 y 2",
            "nombre": "Ordenar la oferta y el metodo",
            "tareas": [
                {"tarea": "Reescribir el avatar tomando tus 3 mejores clientes: quienes pagaron mas y mejores resultados tuvieron.", "quien": "cliente"},
                {"tarea": "Armamos con vos el mapa del metodo unico en un Miro y te lo presentamos por Loom.", "quien": "nosotros"},
                {"tarea": "Volcar avatar, oferta y metodo en la bio de Instagram para que se entienda en cinco segundos.", "quien": "cliente"},
            ],
            "entregables": [
                {"texto": "Avatar reescrito + metodo unico en Miro (lo armamos nosotros, se entrega por Loom)"},
                {"texto": "Perfil de Instagram actualizado"},
            ],
        },
        {
            "etiqueta": "Semana 3",
            "nombre": "Regularidad de contenido",
            "pasos": [
                {"tarea": "Publicar el recurso semanal de YouTube. La regularidad pesa mas que la produccion.", "quien": "cliente"},
                {"tarea": "Tres reels y cinco historias que terminen siempre en el recurso de la semana.", "quien": "cliente"},
                {"tarea": "Revisamos los guiones antes de que grabes y te devolvemos correcciones por Discord.", "quien": "nosotros"},
            ],
            "deliverables": [
                {"texto": "Recurso semanal publicado + 3 reels"},
                {"texto": "Calendario de contenido de las proximas 4 semanas"},
            ],
        },
        {
            "etiqueta": "Semana 4",
            "nombre": "Agendamiento y triage",
            "tareas": [
                "Armamos el flujo de chat a llamada para tu tipo de cliente (nosotros hacemos)",
                "Implementar el triage antes de cada llamada para subir la tasa de presentacion",
                "Sumarle al VSL de chat las objeciones nuevas que aparecieron en las ultimas llamadas",
            ],
            "entregables": [
                "Flujo de agendamiento andando",
                "VSL de chat actualizado",
            ],
        },
    ],
}


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        print("recibido:", cuerpo["cliente"]["nombre"], "|", len(cuerpo["respuestas"]), "respuestas")
        salida = json.dumps({"roadmap_id": cuerpo["roadmap_id"], **ROADMAP}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(salida)))
        self.end_headers()
        self.wfile.write(salida)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("IA falsa escuchando en http://127.0.0.1:8999/roadmap")
    HTTPServer(("127.0.0.1", 8999), H).serve_forever()
