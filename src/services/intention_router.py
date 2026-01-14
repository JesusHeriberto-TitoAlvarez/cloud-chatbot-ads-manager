"""
Router de intenciones para mensajes de usuario.

Detecta intenciones en el texto entrante y puede devolver una respuesta directa,
una respuesta fusionada o solo actualizar el historial. Usa historial almacenado
(Firestore) y OpenAI para fusionar respuestas cuando hay multiples intenciones.
"""

# === DEPENDENCIAS Y CONFIGURACION ===
from src.config import openai_client, GPT_MODEL_AVANZADO, TEMPERATURA_CONVERSACION
from src.data.firestore_storage import leer_historial

# === IMPORT DE DETECTORES (INTENCIONES) ===
from src.services.intentions.intention_bolivianismo import detectar_bolivianismo
from src.services.intentions.intention_costo_google_ads import detectar_costo_google_ads
from src.services.intentions.intention_creador import detectar_creador
from src.services.intentions.intention_que_es_google_ads import detectar_que_es_google_ads

# from src.services.intentions.intention_proposito import detectar_proposito
# from src.services.intentions.intention_crear_anuncio import detectar_crear_anuncio
# from src.services.intentions.intention_user_name import detectar_nombre_usuario  # Intención silenciosa
# from src.services.intentions.intention_ciudad_empresa import detectar_ciudad_empresa  # Intención silenciosa
# from src.services.intentions.intention_nombre_empresa import detectar_nombre_empresa  # Intención silenciosa


# === REGISTRO DE INTENCIONES ACTIVAS ===
INTENCIONES = [
    detectar_creador,
    detectar_que_es_google_ads,
    detectar_bolivianismo,
    detectar_costo_google_ads,
    # detectar_proposito,
    # detectar_crear_anuncio
]


# === ROUTER PRINCIPAL ===
def preparar_historial_con_inyeccion(mensaje_usuario, numero_usuario):
    """
    Detecta intenciones en el mensaje del usuario y prepara el historial.

    Args:
        mensaje_usuario: Texto entrante del usuario.
        numero_usuario: Identificador del usuario en el historial.

    Returns:
        dict con "historial" y opcionalmente "respuesta_directa".

    Flujo:
        - Lee historial y deduplica por (role, content.strip()).
        - Ejecuta intenciones y recolecta respuestas.
        - 0 intenciones: solo actualiza historial si no es duplicado.
        - 1 intencion: devuelve respuesta directa.
        - N intenciones: fusiona respuestas con GPT usando contexto reciente.
    """
    historial = leer_historial(numero_usuario)

    # Deduplicado exacto por contenido y role
    vistos = set()
    historial = [
        m for m in historial
        if (clave := (m["role"], m["content"].strip())) not in vistos and not vistos.add(clave)
    ]

    respuestas_detectadas = []

    # Intenciones silenciosas (no responden, solo registran)
    # detectar_nombre_usuario(mensaje_usuario, numero_usuario)      # Guarda el nombre del usuario si se detecta
    # detectar_ciudad_empresa(mensaje_usuario, numero_usuario)      # Guarda la ciudad o departamento si se detecta
    # detectar_nombre_empresa(mensaje_usuario, numero_usuario)      # Guarda el nombre del negocio si se detecta

    # Intenciones con respuesta visible
    for funcion in INTENCIONES:
        resultado = funcion(mensaje_usuario, numero_usuario)
        if resultado:
            print(f"[INTENCIÓN ACTIVADA] {funcion.__name__} → {mensaje_usuario}")
            respuestas_detectadas.append(resultado["respuesta"])

    # 0 intenciones: solo historial (evita duplicar ultimo user)
    if not respuestas_detectadas:
        if (
            not historial
            or historial[-1]["role"] != "user"
            or historial[-1]["content"].strip() != mensaje_usuario.strip()
        ):
            historial.append({"role": "user", "content": mensaje_usuario})
        return {
            "historial": historial
        }

    # 1 intencion: respuesta directa
    if len(respuestas_detectadas) == 1:
        return {
            "respuesta_directa": respuestas_detectadas[0],
            "historial": historial
        }

    # N intenciones: fusion con GPT usando contexto reciente
    # Contexto corto para mantener continuidad conversacional
    ultimos_usuario = [m for m in historial if m["role"] == "user"][-6:]
    ultimos_chatbot = [m for m in historial if m["role"] == "assistant"][-6:]
    historial_reciente = sorted(ultimos_usuario + ultimos_chatbot, key=lambda x: x.get("timestamp", ""))

    partes_respuesta = "\n".join(f"{i+1}. {r}" for i, r in enumerate(respuestas_detectadas))

    prompt_fusionador = [
        {"role": "system", "content": (
            "Eres Chatbot Ads Manager, un asistente conversacional diseñado para responder en WhatsApp "
            "con tono cálido, claro y natural.\n\n"
            "El usuario envió un solo mensaje que contiene múltiples preguntas o intenciones.\n"
            "Tu tarea es combinar todas las respuestas detectadas en un solo mensaje fluido, conversacional y coherente por favor.\n\n"
            "INSTRUCCIONES:\n"
            "- Debes leer y tener en cuenta el historial de conversación que te daré a continuación.\n"
            "- Luego recibirás una serie de ideas que debes comunicar, generadas por otros componentes del sistema.\n"
            "- Tu misión es PARAFRASEAR esa información en un solo mensaje cálido, sin copiar literal el contenido.\n"
            "- Es OBLIGATORIO que utilices toda la información de las respuestas detectadas.\n"
            "- No repitas las preguntas del usuario.\n"
            "- No inicies con saludos como 'Hola' o 'Buenos días' a menos que el usuario ya haya saludado previamente.\n"
            "- El inicio del mensaje debe estar conectado al historial de conversación de manera natural por favor.\n"
            "- Mantén el estilo de una conversación por WhatsApp: frases cortas, amigables y fáciles de leer.\n"
            "- Usa transiciones naturales entre temas para que la respuesta no se sienta fragmentada.\n"
            "- Si vas a dar ejemplos, asegúrate de que se entiendan fácilmente en el contexto boliviano (ej. tienda, ferretería, etc.).\n"
            "- No uses listas a menos que sean realmente necesarias.\n"
            "- No expliques demasiado. Sé claro, directo y cálido.\n"
            "- Siempre prioriza continuidad con el historial reciente.\n"
            "- Si el usuario ha preguntado algo que ya fue respondido antes, vuelve a explicarlo de forma natural, sin decir que ya se habló de eso."
        )}
    ]
    prompt_fusionador.extend(historial_reciente)
    prompt_fusionador.append({"role": "user", "content": partes_respuesta})

    try:
        respuesta_fusionada = openai_client.chat.completions.create(
            model=GPT_MODEL_AVANZADO,
            messages=prompt_fusionador,
            temperature=TEMPERATURA_CONVERSACION,
            max_tokens=400
        ).choices[0].message.content.strip()

        return {
            "respuesta_directa": respuesta_fusionada,
            "historial": historial
        }

    except Exception as e:
        print(f"[ERROR GPT - fusión de intenciones] {e}")
        return {
            "respuesta_directa": (
                "Lo siento, ocurrió un problema al generar la respuesta. "
                "¿Podrías repetir tu mensaje mientras lo soluciono?"),
            "historial": historial
        }


# LEGACY (deprecated): versiones anteriores disponibles en el historial de Git.
