"""
Servicio de envio de mensajes por WhatsApp Cloud API.

Envia el mensaje al endpoint de WhatsApp y lo registra en el historial,
seleccionando el backend segun USAR_FIRESTORE.
"""

import requests

from src.config import ACCESS_TOKEN, PHONE_NUMBER_ID, USAR_FIRESTORE

# Import condicional para seleccionar el backend de almacenamiento.
if USAR_FIRESTORE:
    # Se importa guardar_mensaje con alias para mantener la interfaz comun.
    from src.data.firestore_storage import guardar_mensaje as agregar_mensaje
else:
    from src.data.conversation_storage import agregar_mensaje


def send_message(recipient_id: str, text: str) -> None:
    """Envia un mensaje por WhatsApp y lo guarda en el historial.

    Args:
        recipient_id: ID/numero del destinatario.
        text: Texto a enviar.

    Side effects:
        - Realiza un POST a la API de WhatsApp.
        - Guarda el mensaje del asistente en el historial.
        - Imprime el estado segun response.status_code.
    """
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": text},
    }

    response = requests.post(url, headers=headers, json=payload)

    # Guardar mensaje del chatbot en historial (Firestore o JSON)
    agregar_mensaje(recipient_id, "assistant", text)

    if response.status_code != 200:
        print(f"Error al enviar el mensaje: {response.text}")
    else:
        print("Mensaje enviado correctamente.")
