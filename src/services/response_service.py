from src.config import openai_client, GPT_MODEL_AVANZADO, TEMPERATURA_CONVERSACION

def generar_respuesta(mensaje_usuario, numero, historial):
    print("[GPT] Generando respuesta personalizada...")

    # Extraer solo los últimos 3 mensajes útiles para el historial resumido
    historial_resumido = historial[-3:] if len(historial) > 3 else historial

    print("[DEBUG] Historial resumido usado en el system prompt:")
    for i, h in enumerate(historial_resumido):
        print(f"[{i}] ({h.get('role')}) → {h.get('content')}")

    mensaje_system = (
        "Eres Chatbot Ads Manager, un guía conversacional que ayuda a personas sin experiencia a comprender y aprovechar la publicidad digital, "
        "en especial a través de Google Ads. Tu rol es acompañar al usuario con explicaciones simples, ejemplos prácticos y pasos concretos, "
        "como si fueras alguien de confianza que le enseña con calma y buena onda.\n\n"
        
        f"Estás interactuando con un usuario mediante un historial como este: {historial_resumido}.\n\n"
        
        "- Responde siempre con naturalidad, como si conversaras por WhatsApp.\n"
        "- Si te saludan, responde con un saludo breve y cálido.\n"
        "- Si te hacen una pregunta o te dan una instrucción, responde directo al tema, con amabilidad.\n"
        "- No digas frases como 'soy un asistente' o 'fui creado para ayudarte', a menos que te lo pregunten.\n"
        "- Usa respuestas muy breves: máximo 3 líneas de WhatsApp (35 a 45 palabras).\n"
        "- Evita párrafos largos. Sé directo, claro y humano.\n"
        "- Puedes incluir listas cortas si ayudan, pero que ocupen máximo 3 líneas.\n"
        "- Usa emojis con moderación (máximo uno), solo si aportan cercanía o confianza.\n"
        "- Nunca uses más de una exclamación seguida.\n"
        "- Siempre responde en el idioma del usuario, con naturalidad y buena onda."
    )

    mensajes = [{"role": "system", "content": mensaje_system}]

    historial_filtrado = [
        mensaje for mensaje in historial
        if isinstance(mensaje, dict)
        and "role" in mensaje
        and "content" in mensaje
    ]
    mensajes.extend(historial_filtrado)

    try:
        response = openai_client.chat.completions.create(
            model=GPT_MODEL_AVANZADO,
            messages=mensajes,
            temperature=TEMPERATURA_CONVERSACION,
            max_tokens=200,  # puedes bajar esto si quieres
        )

        # === TEXTO ORIGINAL DEL MODELO ===
        respuesta = response.choices[0].message.content.strip()

        # === RECORTE DURO A 3 LÍNEAS ===
        # 1) cortar por líneas
        lineas = [l for l in respuesta.splitlines() if l.strip() != ""]
        lineas = lineas[:3]  # solo las primeras 3 líneas
        respuesta_corta = "\n".join(lineas)

        # 2) opcional: limitar también palabras (ej. 45)
        palabras = respuesta_corta.split()
        if len(palabras) > 45:
            respuesta_corta = " ".join(palabras[:45])

        print("[GPT] Respuesta generada y recortada a 3 líneas.")
        return respuesta_corta

    except Exception as e:
        print(f"[ERROR GPT] No se pudo generar la respuesta: {e}")
        return "Lo siento, hubo un problema al generar la respuesta. ¿Puedes intentar de nuevo?"




'''


from src.config import openai_client, GPT_MODEL_AVANZADO, TEMPERATURA_CONVERSACION

def generar_respuesta(mensaje_usuario, numero, historial):
    print("[GPT] Generando respuesta personalizada...")

    # Extraer solo los últimos 3 mensajes útiles para el historial resumido
    historial_resumido = historial[-3:] if len(historial) > 3 else historial

    # 🔍 LOG TEMPORAL: ver el historial que se usará
    print("[DEBUG] Historial resumido usado en el system prompt:")
    for i, h in enumerate(historial_resumido):
        print(f"[{i}] ({h.get('role')}) → {h.get('content')}")

    mensaje_system = (
        "Eres Chatbot Ads Manager, un guía conversacional que ayuda a personas sin experiencia a comprender y aprovechar la publicidad digital, "
        "en especial a través de Google Ads. Tu rol es acompañar al usuario con explicaciones simples, ejemplos prácticos y pasos concretos, "
        "como si fueras alguien de confianza que le enseña con calma y buena onda.\n\n"
        
        f"Estás interactuando con un usuario mediante un historial como este: {historial_resumido}.\n\n"
        
        "- Responde siempre con naturalidad, como si conversaras por WhatsApp.\n"
        "- Si te saludan, responde con un saludo breve y cálido.\n"
        "- Si te hacen una pregunta o te dan una instrucción, responde directo al tema, con amabilidad.\n"
        "- No digas frases como 'soy un asistente' o 'fui creado para ayudarte', a menos que te lo pregunten.\n"
        "- Usa respuestas muy breves: máximo 3 líneas de WhatsApp (35 a 45 palabras).\n"
        "- Evita párrafos largos. Sé directo, claro y humano.\n"
        "- Puedes incluir listas cortas si ayudan, pero que ocupen máximo 3 líneas.\n"
        "- Usa emojis con moderación (máximo uno), solo si aportan cercanía o confianza.\n"
        "- Nunca uses más de una exclamación seguida.\n"
        "- Siempre responde en el idioma del usuario, con naturalidad y buena onda."
    )


    mensajes = [{"role": "system", "content": mensaje_system}]

    historial_filtrado = [
        mensaje for mensaje in historial
        if isinstance(mensaje, dict)
        and "role" in mensaje
        and "content" in mensaje
    ]
    mensajes.extend(historial_filtrado)

    try:
        response = openai_client.chat.completions.create(
            model=GPT_MODEL_AVANZADO,
            messages=mensajes,
            temperature=TEMPERATURA_CONVERSACION,
            max_tokens=500
        )

        respuesta = response.choices[0].message.content.strip()
        print("[GPT] Respuesta generada exitosamente.")
        return respuesta

    except Exception as e:
        print(f"[ERROR GPT] No se pudo generar la respuesta: {e}")
        return "Lo siento, hubo un problema al generar la respuesta. ¿Podés intentar de nuevo?"



'''