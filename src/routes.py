from flask import Blueprint, request, jsonify
from src.config import VERIFY_TOKEN, USAR_FIRESTORE
from src.chatbot import get_response
from src.services.message_service import send_message
from src.data.firestore_storage import (
    guardar_mensaje as agregar_mensaje,
    leer_historial,
    registrar_id_procesado  # 👈 usamos directamente esto ahora
)
from src.data.chatbot_sheet_connector import create_user_if_not_exists
import traceback

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == VERIFY_TOKEN:
            return str(challenge), 200
        return "Token inválido", 403

    if request.method == "POST":
        try:
            data = request.get_json()
            if not data or "entry" not in data:
                return jsonify({"error": "Datos de entrada no válidos"}), 400

            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    if "messages" in change.get("value", {}):
                        message = change["value"]["messages"][0]
                        sender_id = message.get("from")
                        message_text = message.get("text", {}).get("body")
                        message_id = message.get("id")

                        if sender_id and message_text and message_id:
                            # 🔒 Verificación de duplicados usando el ID del mensaje
                            if not registrar_id_procesado(message_id, sender_id):
                                print(f"[IGNORADO] Ya procesado (registro duplicado): {message_id}")
                                return "Ya procesado", 200

                            # Leer historial del usuario desde Firestore
                            historial = leer_historial(sender_id)

                            # 🟢 Primer mensaje del usuario (no hay historial previo)
                            if not historial:
                                # Guardar el primer mensaje del usuario
                                agregar_mensaje(sender_id, "user", message_text)

                                # Registrar automáticamente el número en Google Sheets
                                create_user_if_not_exists(sender_id)

                                # Mensaje de bienvenida alineado con el agente
                                mensaje_bienvenida = (
                                    "¡Hola! 😊 Soy tu asistente de marketing digital y mi objetivo es ayudarte a conseguir más clientes.\n\n"
                                    "ℹ️ Aviso: Para brindarte una mejor experiencia guardaré tus respuestas.\n\n"
                                    "Para empezar, cuéntame por favor: ¿cómo se llama tu empresa?"
                                )

                                send_message(sender_id, mensaje_bienvenida)
                                return "Bienvenida enviada", 200

                            # 🔁 Flujo normal desde el segundo mensaje
                            agregar_mensaje(sender_id, "user", message_text)
                            respuesta = get_response(message_text, sender_id)
                            send_message(sender_id, respuesta)

            return "Evento recibido", 200

        except Exception as e:
            print("======= TRACEBACK COMPLETO =======")
            traceback.print_exc()
            print("==================================")
            print(f"Error en webhook: {str(e)}")
            return jsonify({"error": str(e)}), 500





'''
from flask import Blueprint, request, jsonify
from src.config import VERIFY_TOKEN, USAR_FIRESTORE
from src.chatbot import get_response
from src.services.message_service import send_message
from src.data.firestore_storage import (
    guardar_mensaje as agregar_mensaje,
    leer_historial,
    registrar_id_procesado  # 👈 usamos directamente esto ahora
)
from src.data.chatbot_sheet_connector import create_user_if_not_exists
import traceback

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == VERIFY_TOKEN:
            return str(challenge), 200
        return "Token inválido", 403

    if request.method == "POST":
        try:
            data = request.get_json()
            if not data or "entry" not in data:
                return jsonify({"error": "Datos de entrada no válidos"}), 400

            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    if "messages" in change.get("value", {}):
                        message = change["value"]["messages"][0]
                        sender_id = message.get("from")
                        message_text = message.get("text", {}).get("body")
                        message_id = message.get("id")

                        if sender_id and message_text and message_id:
                            # 🔒 INTENTO DE REGISTRAR DIRECTAMENTE EL ID
                            if not registrar_id_procesado(message_id, sender_id):
                                print(f"[IGNORADO] Ya procesado (registro duplicado): {message_id}")
                                return "Ya procesado", 200

                            historial = leer_historial(sender_id)

                            if not historial:
                                agregar_mensaje(sender_id, "user", message_text)

                                # REGISTRO AUTOMÁTICO DEL NÚMERO EN GOOGLE SHEETS
                                create_user_if_not_exists(sender_id)
                                mensaje_bienvenida = (
                                    "*Bienvenido al Chatbot Oficial de Asistencia en Google Ads.*\n\n"
                                    "Este sistema está diseñado para ayudarte a comprender mejor cómo funciona la publicidad en Google y, si lo deseas, "
                                    "puedes crear campañas reales escribiendo simplemente *CREAR CAMPAÑA*.\n\n"
                                    "Durante tu experiencia, todo lo que escribas será almacenado en un historial privado. Esto nos permite mantener "
                                    "una conversación natural y ofrecerte respuestas más útiles según el contexto.\n\n"
                                    "Si tienes alguna consulta sobre Google Ads o necesitas asistencia paso a paso, puedes escribirme con total confianza. "
                                    "Estoy aquí para ayudarte a visibilizar tu negocio en internet de forma efectiva."
                                )

                                send_message(sender_id, mensaje_bienvenida)
                                return "Bienvenida enviada", 200

                            # Flujo normal desde el segundo mensaje
                            agregar_mensaje(sender_id, "user", message_text)
                            respuesta = get_response(message_text, sender_id)
                            send_message(sender_id, respuesta)

            return "Evento recibido", 200

        except Exception as e:
            print("======= TRACEBACK COMPLETO =======")
            traceback.print_exc()
            print("==================================")
            print(f"Error en webhook: {str(e)}")
            return jsonify({"error": str(e)}), 500

'''