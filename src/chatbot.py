"""
Chatbot response orchestration.

This module routes incoming user text through the campaign-creation agent when the
required Google Sheets fields are incomplete; otherwise it follows the normal
flow (intent detection + GPT response). The behavior is intentionally simple and
delegates storage and model logic to service modules.
"""

from src.config import USAR_FIRESTORE
from src.services.agents.agent_creacion_campana import (
    ejecutar_agente_creacion_campana,
    usuario_necesita_agente,
)
from src.services.intention_router import preparar_historial_con_inyeccion
from src.services.response_service import generar_respuesta

# If Firestore is disabled, fall back to local JSON storage.
if not USAR_FIRESTORE:
    from src.data.conversation_storage import guardar_en_historial

# Design notes:
# Local history is only stored when Firestore is disabled to avoid duplicating
# persistence across two backends and to keep a single source of truth.


def get_response(text: str, numero_usuario: str) -> str:
    """
    Procesa el mensaje del usuario y genera una respuesta para WhatsApp.

    Args:
        text: Texto recibido desde el usuario (raw).
        numero_usuario: Identificador del usuario (telefono).

    Returns:
        Respuesta final para enviar por WhatsApp.

    Flujo:
        1) Si faltan datos de campana en Google Sheets, se usa el agente.
        2) Si ya esta completo, se ejecuta el flujo normal:
           - Deteccion de intenciones preprogramadas.
           - Conversacion general con GPT usando historial.
    """

    texto = text.strip()

    # Primero: verificar si este usuario todavia necesita pasar por el agente.
    if usuario_necesita_agente(numero_usuario):
        resultado_agente = ejecutar_agente_creacion_campana(texto, numero_usuario)
        # resultado_agente debe incluir la key "mensaje_respuesta".
        return resultado_agente["mensaje_respuesta"]

    # Flujo normal (intenciones + GPT).
    resultado = preparar_historial_con_inyeccion(texto, numero_usuario)

    # Si una intencion preprogramada dio una respuesta directa.
    if resultado.get("respuesta_directa"):
        respuesta = resultado["respuesta_directa"]

        # Guardado del historial solo si se usa almacenamiento local.
        if not USAR_FIRESTORE:
            guardar_en_historial(numero_usuario, {"role": "user", "content": text})
            guardar_en_historial(numero_usuario, {"role": "assistant", "content": respuesta})

        return respuesta

    # Si no hay intencion, GPT responde usando el historial construido.
    return generar_respuesta(text, numero_usuario, resultado["historial"])

# Legacy code (deprecated): ver historial git / rama anterior.
