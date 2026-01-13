"""
Flask entrypoint for Chatbot Ads Manager.

Registers the WhatsApp webhook blueprint and exposes basic health/diagnostic
endpoints, including the App Engine stop handler.
"""

from flask import Flask

from src.routes import webhook_bp

# === APP SETUP ===
app = Flask(__name__)

# === HEALTH / DIAGNOSTICS ===
@app.route("/")
def home():
    """Endpoint de salud simple para confirmar disponibilidad del servicio."""
    return "Chatbot Ads Manager está en línea y listo para recibir mensajes por WhatsApp."

# === APP ENGINE SPECIAL ROUTES ===
@app.route("/_ah/stop")
def stop_handler():
    """Evita errores 404/500 cuando App Engine emite la senal de stop."""
    return "OK", 200

# === WEBHOOK ROUTES ===
app.register_blueprint(webhook_bp)

# === LOCAL EXECUTION ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

# LEGACY (deprecated): ver historial de Git para versiones anteriores.
