"""
Agente de creacion de campanas para Google Ads basado en conversacion.

Este modulo extrae datos desde el historial del usuario (Firestore) y usa Google
Sheets como estado persistente para completar los campos de la campana.
Retorna un dict con mensaje_respuesta/finalizado para el caller.
No crea campanas directamente; solo recopila y persiste informacion.
"""

import json

from src.config import (
    openai_client,
    GPT_MODEL_AGENTE,
    TEMPERATURA_AGENTE,
)
from src.data.chatbot_sheet_connector import (
    get_user_field,
    update_user_field,
)
from src.data.firestore_storage import leer_historial

# === CONFIGURACION DE COLUMNAS ===
# Mantienen exactamente el diseño actual de la hoja
COLUMNA_CAMPAIGN_NAME = "Campaign Name"
COLUMNA_TITLES = "Titles"
COLUMNA_DESCRIPTIONS = "Descriptions"
COLUMNA_KEYWORDS = "Keywords"
COLUMNA_REQUESTED_BUDGET = "Requested Budget"


# === LECTURA Y VALIDACION DE DATOS ===
def _leer_datos_usuario(phone_number: str) -> dict:
    """
    Lee de Google Sheets los campos relevantes para la campaña de este usuario.

    Campos esperados:
        - campaign_name
        - titles (string con \n)
        - descriptions (string con \n)
        - keywords (string con ", ")
        - requested_budget

    Returns:
        Dict con los valores actuales (strings o vacios si no hay dato).
    """
    return {
        "campaign_name": get_user_field(phone_number, COLUMNA_CAMPAIGN_NAME) or "",
        "titles": (get_user_field(phone_number, COLUMNA_TITLES) or "").strip(),
        "descriptions": (get_user_field(phone_number, COLUMNA_DESCRIPTIONS) or "").strip(),
        "keywords": (get_user_field(phone_number, COLUMNA_KEYWORDS) or "").strip(),
        "requested_budget": get_user_field(phone_number, COLUMNA_REQUESTED_BUDGET) or "",
    }


# Funcion reservada/no usada: referencia una constante no definida en el modulo.
# Se mantiene intacta para evitar cambios de runtime.
def _marcar_validation_incomplete(phone_number: str) -> None:
    """
    Si la fila del usuario existe (o se crea al escribir), marca Validation Status = 'incomplete'
    SOLO si aún está vacío. No sobreescribe estados ya avanzados (ej: Campaign Ready, Ad Ready, etc.)
    """
    actual = (get_user_field(phone_number, COLUMNA_VALIDATION_STATUS) or "").strip()
    if not actual:
        update_user_field(phone_number, COLUMNA_VALIDATION_STATUS, "incomplete")


def usuario_necesita_agente(phone_number: str) -> bool:
    """
    Devuelve True si TODAVÍA falta información importante de campaña
    en Google Sheets para este número.

    Condición para considerar COMPLETO:
        - Campaign Name lleno
        - Titles no vacío
        - Descriptions no vacío
        - Keywords no vacío
        - Requested Budget lleno
    """
    datos = _leer_datos_usuario(phone_number)

    return not (
        datos["campaign_name"]
        and datos["titles"]
        and datos["descriptions"]
        and datos["keywords"]
        and datos["requested_budget"]
    )


# === PERSISTENCIA EN SHEETS ===
def _guardar_datos_en_sheet(phone_number: str, datos: dict) -> None:
    """
    Persiste en Google Sheets los datos provistos por el agente.

    Admite:
        - campaign_name: str
        - titles: list[str] o str
        - descriptions: list[str] o str
        - keywords: list[str] o str
        - requested_budget: str

    Notas importantes:
        - Titles/Descriptions se guardan con "\n".
        - Keywords se guardan con ", ".
        - Solo se escriben campos con contenido.
    """
    # Nombre de campaña / empresa
    campaign_name = datos.get("campaign_name")
    if campaign_name:
        update_user_field(phone_number, COLUMNA_CAMPAIGN_NAME, campaign_name.strip())

    # === TITLES ===
    titles = datos.get("titles")

    # Si viene como string tipo "x|y|z", lo convertimos a lista de 1 elemento
    if isinstance(titles, str):
        titles = [titles]

    if titles and isinstance(titles, list):
        texto_titles = "\n".join(
            t.strip() for t in titles
            if t and isinstance(t, str)
        )
        if texto_titles:
            update_user_field(phone_number, COLUMNA_TITLES, texto_titles)

    # === DESCRIPTIONS ===
    descriptions = datos.get("descriptions")

    if isinstance(descriptions, str):
        descriptions = [descriptions]

    if descriptions and isinstance(descriptions, list):
        texto_descriptions = "\n".join(
            d.strip() for d in descriptions
            if d and isinstance(d, str)
        )
        if texto_descriptions:
            update_user_field(phone_number, COLUMNA_DESCRIPTIONS, texto_descriptions)

    # === KEYWORDS ===
    keywords = datos.get("keywords")

    if isinstance(keywords, str):
        keywords = [keywords]

    if keywords and isinstance(keywords, list):
        texto_keywords = ", ".join(
            k.strip() for k in keywords
            if k and isinstance(k, str)
        )
        if texto_keywords:
            update_user_field(phone_number, COLUMNA_KEYWORDS, texto_keywords)

    # Presupuesto tentativo
    requested_budget = datos.get("requested_budget")
    if requested_budget:
        update_user_field(
            phone_number,
            COLUMNA_REQUESTED_BUDGET,
            str(requested_budget).strip()
        )


# === CONSTRUCCION DE PROMPT ===
def _construir_prompt_agente(mensaje_usuario: str, phone_number: str) -> list:
    """
    Construye el prompt (lista de mensajes) para el modelo del agente.

    Incluye:
        - Rol del agente y reglas de conversación.
        - Resumen de datos actuales en Sheets (evita repetir preguntas).
        - Historial reciente (solo ultimos N mensajes por contexto corto).
        - Último mensaje del usuario.
    """
    datos_actuales = _leer_datos_usuario(phone_number)

    # Resumen de lo que ya tenemos en la hoja (para que el modelo NO repita preguntas)
    resumen_datos = (
        f"Datos actuales en la hoja para el número {phone_number}:\n"
        f"- Campaign Name: {datos_actuales['campaign_name'] or '(vacío)'}\n"
        f"- Titles: {datos_actuales['titles'] or '(vacío)'}\n"
        f"- Descriptions: {datos_actuales['descriptions'] or '(vacío)'}\n"
        f"- Keywords: {datos_actuales['keywords'] or '(vacío)'}\n"
        f"- Requested Budget: {datos_actuales['requested_budget'] or '(vacío)'}\n"
    )

    # Leemos historial desde Firestore (igual que intention_router)
    historial = leer_historial(phone_number)
    historial_filtrado = [
        m for m in historial
        if isinstance(m, dict) and "role" in m and "content" in m
    ]
    # Contexto corto: no hace falta mas de los ultimos N mensajes
    ultimos_mensajes = historial_filtrado[-8:]

    mensaje_system = (
        "Eres un agente especializado en crear campañas de Google Ads para pequeños negocios en Bolivia.\n"
        "Tu misión es guiar al usuario con preguntas simples para obtener la información necesaria y luego "
        "generar los textos completos de la campaña.\n\n"
        "ROL Y ESTILO:\n"
        "- Eres amable, paciente y hablas como una persona boliviana educada.\n"
        "- Escribe como si estuvieras conversando por WhatsApp: frases cortas, claras y naturales.\n"
        "- Evita palabras técnicas como 'CPC', 'funnel', 'conversión', 'ROAS', etc.\n"
        "- Usa ejemplos simples (por ejemplo: 'cuánta gente vio tu letrero' en lugar de 'impresiones').\n"
        "- Siempre respondes en español, con tono cercano pero profesional.\n\n"
        "OBJETIVO DEL AGENTE EN ESTA FASE:\n"
        "Debes ayudar al usuario a definir y completar, a partir de lo que diga, los siguientes campos:\n"
        "- Nombre de la empresa o negocio (campaign_name).\n"
        "- 15 títulos para los anuncios (titles).\n"
        "- 4 descripciones (descriptions).\n"
        "- 10 palabras o frases clave (keywords).\n"
        "- Un presupuesto diario simbólico que el usuario estaría dispuesto a pagar (requested_budget).\n\n"
        "PRIORIDAD DE PREGUNTAS (ORDEN RECOMENDADO):\n"
        "1) Primero asegúrate de entender qué vende el negocio y qué lo hace diferente.\n"
        "2) Si falta el nombre del negocio, pregúntalo de forma directa y amable.\n"
        "3) Luego profundiza en los productos, servicios y beneficios para los clientes.\n"
        "4) Después pregunta por el presupuesto diario aproximado que estaría dispuesto a invertir.\n"
        "   - Aclara que es un monto simbólico, por ejemplo: 3 Bs por día.\n"
        "5) Cuando tengas información suficiente sobre el negocio, genera los 15 títulos, 4 descripciones y 10 palabras clave.\n\n"
        "REGLAS DE ORO:\n"
        "1) Solo haces UNA pregunta a la vez en 'mensaje_respuesta'.\n"
        "2) Antes de preguntar, revisa la información que ya conoces para NO repetir preguntas.\n"
        "3) Si el usuario ya respondió algo que sirve para varios campos, puedes reutilizar esa idea en los textos.\n"
        "4) Si todavía falta información importante, debes seguir preguntando de forma amable.\n"
        "5) Cuando ya tengas todo lo necesario, en lugar de seguir preguntando, debes generar todos los campos.\n"
        "6) No inventes datos clave del negocio (como el rubro) si el usuario no dio ninguna pista. En esos casos, pregunta.\n\n"
        "FORMATO DE SALIDA OBLIGATORIO:\n"
        "SIEMPRE debes responder en formato JSON ESTRICTO, sin texto adicional, sin explicaciones, sin markdown.\n"
        "El JSON debe tener esta forma:\n"
        "{\n"
        '  "mensaje_respuesta": "texto que enviaras al usuario por WhatsApp",\n'
        '  "datos": {\n'
        '    "campaign_name": "(obligatorio en estado finalizado) nombre del negocio",\n'
        '    "titles": ["Titulo1|Titulo2|...|Titulo15"],\n'
        '    "descriptions": ["Descripcion1|Descripcion2|Descripcion3|Descripcion4"],\n'
        '    "keywords": ["keyword1|keyword2|...|keyword10"],\n'
        '    "requested_budget": "(obligatorio en estado finalizado, puede estar vacío mientras está en proceso) presupuesto diario simbolico como texto, no se cobrara nada (ej: \\\"20 Bs por día\\\")"\n'
        "  },\n"
        '  "estado": "en_proceso"\n'
        "}\n\n"
        "COMPORTAMIENTO SEGÚN ESTADO:\n"
        "- El campo 'estado' solo puede ser exactamente 'en_proceso' o 'finalizado'.\n"
        "- Si todavía falta información clave, usa 'estado': 'en_proceso' y formula UNA sola pregunta amable en "
        "'mensaje_respuesta'. En este caso, puedes dejar los campos de 'datos' vacíos o parcialmente llenos.\n"
        "- Si ya tienes suficiente información para los 15 títulos, 4 descripciones, 10 keywords y un presupuesto razonable, "
        "usa 'estado': 'finalizado' y llena TODOS los campos en 'datos'. En este caso, evita hacer nuevas preguntas.\n\n"
        "REGLAS ESPECIALES PARA LA CALIDAD DE LOS ANUNCIOS:\n"
        "- Los TITULOS NO deben superar los 30 caracteres cada uno.\n"
        "- Las DESCRIPCIONES NO deben superar los 90 caracteres cada una.\n"
        "- Las PALABRAS CLAVE deben ser claras, directas y relacionadas con el negocio (evita palabras sueltas sin relación).\n"
        "- TODOS los títulos, descripciones y keywords deben entregarse usando líneas verticales (|) como separador.\n"
        "  Ejemplo de titles: Vence la rutina|Actívate bailando|Zumba para todos\n"
        "  Ejemplo de keywords: zapatillas running|zapatillas deportivas hombre|zapatillas deportivas mujer\n"
        "- No uses comas ni listas dentro del JSON para estos campos. SOLO separa cada elemento con '|'.\n\n"
        "INSTRUCCIONES IMPORTANTES FINALES:\n"
        "- Responde SIEMPRE con un único objeto JSON válido, sin comentarios, sin markdown y sin texto antes o después del JSON.\n"
        "- Recuerda que el texto de 'mensaje_respuesta' es lo que verá el usuario por WhatsApp, así que debe sonar natural, cercano y claro.\n\n"
        f"{resumen_datos}\n"
        "Ahora recibirás el historial reciente y el último mensaje del usuario."
    )

    mensajes = [{"role": "system", "content": mensaje_system}]

    # Añadimos historial reciente (si existe)
    mensajes.extend(ultimos_mensajes[-6:])

    # Mensaje actual del usuario
    mensajes.append({"role": "user", "content": mensaje_usuario})

    return mensajes


# === EJECUCION DEL AGENTE ===
def ejecutar_agente_creacion_campana(mensaje_usuario: str, phone_number: str) -> dict:
    """
    Punto de entrada del agente de creación de campaña.

    Returns:
        Dict con la forma:
            {
                "mensaje_respuesta": "texto para enviar al usuario",
                "finalizado": True/False
            }

    Side effects:
        - Llama a OpenAI y fuerza JSON estricto.
        - Actualiza Google Sheets con datos nuevos.
        - Imprime estado y errores con prefijo [AGENTE CAMPANA].

    Notas importantes:
        - El mensaje_respuesta se sobreescribe cuando el estado es finalizado.
    """

    mensajes = _construir_prompt_agente(mensaje_usuario, phone_number)

    try:
        respuesta = openai_client.chat.completions.create(
            model=GPT_MODEL_AGENTE,
            messages=mensajes,
            temperature=TEMPERATURA_AGENTE,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        contenido = respuesta.choices[0].message.content.strip()
        print("[AGENTE CAMPANA] Respuesta bruta del modelo:", contenido)

        # Intentamos parsear el JSON
        data = json.loads(contenido)

        mensaje_respuesta = data.get("mensaje_respuesta", "").strip()
        datos = data.get("datos", {}) or {}
        estado = (data.get("estado") or "").strip().lower()

        # Guardar en Google Sheets cualquier dato nuevo
        _guardar_datos_en_sheet(phone_number, datos)

        finalizado = estado == "finalizado"

        # Si el agente ya terminó, NO mostramos títulos/descripciones/keywords,
        # solo un mensaje corto de confirmación.
        if finalizado:
            mensaje_respuesta = (
                "Listo, ya tengo toda la información para armar tu campaña. "
                "Cuando esté preparada te avisaré. "
                "Mientras tanto, podemos seguir conversando de lo que necesites 🙂"
            )
        else:
            # Si todavía está en proceso y el modelo no devolvió texto, usamos un mensaje genérico.
            if not mensaje_respuesta:
                mensaje_respuesta = (
                    "Gracias por la información. Cuentame un poco más sobre tu negocio, por favor."
                )

        # === DEBUG/TEST MARKER (disabled) ===
        # MARCADOR_TEMP = " ¤"
        # return {
        #     "mensaje_respuesta": (mensaje_respuesta + MARCADOR_TEMP),
        #     "finalizado": finalizado,
        # }

        return {
            "mensaje_respuesta": mensaje_respuesta,
            "finalizado": finalizado,
        }

    except json.JSONDecodeError as e:
        print(f"[AGENTE CAMPANA] Error al parsear JSON del modelo: {e}")
        print("[AGENTE CAMPANA] Contenido recibido:", contenido)
        # En caso de fallo, no actualizamos Sheet y seguimos preguntando de forma segura
        return {
            "mensaje_respuesta": (
                "Por favor necesito que me des información mas detallada para poder atrearte mas clientes. "
            ),
            "finalizado": False,
        }

    except Exception as e:
        print(f"[AGENTE CAMPANA] Error general al llamar al modelo: {e}")
        return {
            "mensaje_respuesta": (
                "Lo siento, tuve un problema al procesar la información. "
                "¿Te parece si lo intentamos de nuevo en un momento?"
            ),
            "finalizado": False,
        }
