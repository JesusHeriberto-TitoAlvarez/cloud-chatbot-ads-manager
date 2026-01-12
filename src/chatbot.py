from src.services.response_service import generar_respuesta
from src.services.intention_router import preparar_historial_con_inyeccion
from src.config import USAR_FIRESTORE

# Agente de creación de campaña
from src.services.agents.agent_creacion_campana import (
    ejecutar_agente_creacion_campana,
    usuario_necesita_agente,
)

# Si no usamos Firestore, usamos almacenamiento local de respaldo
if not USAR_FIRESTORE:
    from src.data.conversation_storage import guardar_en_historial


def get_response(text: str, numero_usuario: str) -> str:
    """
    Procesa el mensaje del usuario y genera una respuesta para WhatsApp.

    Flujo:
    1) Mientras falte información de campaña en Google Sheets
       (Campaign Name, Titles, Descriptions, Keywords, Requested Budget),
       se usa el AGENTE de creación de campaña.
    2) Cuando toda esa información ya está completa, se pasa al flujo normal:
       - Intenciones preprogramadas
       - Conversación general con GPT
    """

    texto = text.strip()

    # 1) Primero: verificar si este usuario todavía necesita pasar por el AGENTE.
    #    usuario_necesita_agente() revisa los campos en Google Sheets.
    if usuario_necesita_agente(numero_usuario):
        resultado_agente = ejecutar_agente_creacion_campana(texto, numero_usuario)
        return resultado_agente["mensaje_respuesta"]

    # 2) Si NO necesita agente, seguimos al FLUJO NORMAL (intenciones + GPT)
    resultado = preparar_historial_con_inyeccion(texto, numero_usuario)

    # Si una intención preprogramada dio una respuesta directa
    if resultado.get("respuesta_directa"):
        respuesta = resultado["respuesta_directa"]

        # Guardado del historial solo si se usa almacenamiento local
        if not USAR_FIRESTORE:
            guardar_en_historial(numero_usuario, {"role": "user", "content": text})
            guardar_en_historial(numero_usuario, {"role": "assistant", "content": respuesta})

        return respuesta

    # Si no hay intención, GPT responde usando el historial construido
    return generar_respuesta(text, numero_usuario, resultado["historial"])










'''
from src.services.response_service import generar_respuesta
from src.services.intention_router import preparar_historial_con_inyeccion
from src.config import USAR_FIRESTORE
from src.services.FSM.flujo_creacion_campana import ejecutar_flujo_creacion_campana
from src.data.firestore_storage import guardar_mensaje
from src.data.chatbot_sheet_connector import get_user_field, update_user_field

if not USAR_FIRESTORE:
    from src.data.conversation_storage import guardar_en_historial


def get_response(text, numero_usuario):
    """
    Procesa el mensaje del usuario y genera una respuesta para WhatsApp.
    """

    texto = text.strip()

    # 🔴 SALIR del flujo de creación — solo si es exactamente "SALIR" en mayúsculas
    if texto == "SALIR":
        respuesta = "Saliste del proceso de creación de campaña. Puedes seguir preguntando lo que desees 😊"

        if USAR_FIRESTORE:
            guardar_mensaje(numero_usuario, "assistant", respuesta)

        estado_campana = get_user_field(numero_usuario, "Estado Campana")
        estado_anuncio = get_user_field(numero_usuario, "Estado Anuncio")

        # 🧼 Caso 1: El usuario salió antes de completar la campaña
        if estado_campana != "Campana Complete":
            campos_a_borrar = ["User Name", "Campaign Name", "Segmentation", "Requested Budget"]
            for campo in campos_a_borrar:
                update_user_field(numero_usuario, campo, "")

            # Restablecer estado si algún dato está incompleto
            falta_dato = any(get_user_field(numero_usuario, campo) in [None, ""] for campo in campos_a_borrar)
            if falta_dato:
                update_user_field(numero_usuario, "Estado Campana", "no iniciada")

        # 🧼 Caso 2: La campaña fue completada pero el anuncio aún no
        elif estado_anuncio != "Anuncio Completed":
            campos_a_borrar = ["Titles", "Descriptions", "Keywords"]
            for campo in campos_a_borrar:
                update_user_field(numero_usuario, campo, "")

            # Reiniciar flujo de anuncio si el usuario se detuvo a medio camino
            update_user_field(numero_usuario, "Estado Anuncio", "no iniciado")

        return respuesta

    # 🟢 INICIAR el flujo FSM — solo si es exactamente "CREAR CAMPAÑA"
    if texto == "CREAR CAMPAÑA":
        return ejecutar_flujo_creacion_campana(numero_usuario)

    # 🔁 FSM activo: ejecutar si el estado indica que el usuario está en medio del proceso
    estado_campana = get_user_field(numero_usuario, "Estado Campana")
    estado_anuncio = get_user_field(numero_usuario, "Estado Anuncio")
    if (
        (estado_campana not in [None, "", "no iniciada", "Campana Complete"])
        or (estado_anuncio not in [None, "", "no iniciado", "Anuncio Completed"])
    ):
        return ejecutar_flujo_creacion_campana(numero_usuario, texto)

    # ⚪️ Proceso normal: intenciones + GPT
    resultado = preparar_historial_con_inyeccion(texto, numero_usuario)

    if resultado.get("respuesta_directa"):
        respuesta = resultado["respuesta_directa"]

        if not USAR_FIRESTORE:
            guardar_en_historial(numero_usuario, {"role": "user", "content": text})
            guardar_en_historial(numero_usuario, {"role": "assistant", "content": respuesta})

        return respuesta

    return generar_respuesta(text, numero_usuario, resultado["historial"])
'''
