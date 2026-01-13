"""
Runtime configuration for the Chatbot Ads Manager service.

This module loads environment variables, configures WhatsApp credentials, sets
OpenAI models/temperatures, and defines the storage toggle. It also initializes
an OpenAI client using the environment-provided API key.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# === ENVIRONMENT LOADING ===
# Load .env values at import time to keep downstream modules simple.
load_dotenv()

# === WHATSAPP CREDENTIALS ===
# Tokens required to validate and send messages via the WhatsApp API.
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# === OPENAI API ===
# API key used to initialize the OpenAI client.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# === GPT MODEL CONFIGURATION ===
# Model selection per task profile.
GPT_MODEL_GENERAL = "gpt-3.5-turbo"             # Conversaciones generales
GPT_MODEL_PRECISO = "gpt-3.5-turbo-1106"        # Para tareas criticas (nombre, ciudad, intencion)
GPT_MODEL_AVANZADO = "gpt-4-0125-preview"       # Creatividad, razonamiento complejo
GPT_MODEL_AGENTE = "gpt-4.1"                    # Agente

# Temperature settings per task profile.
TEMPERATURA_GPT = 0.7                           # General (heredado)
TEMPERATURA_CONVERSACION = 0.7                  # Para respuestas amables, naturales
TEMPERATURA_DATOS_PERSONALES = 0.3              # Para extraer nombres, ciudades, categorias
TEMPERATURA_INTENCIONES = 0.2                   # Para clasificar lo que el usuario quiere
TEMPERATURA_AGENTE = 0.0                        # Para Agente

# Por compatibilidad con codigo actual.
GPT_MODEL = GPT_MODEL_GENERAL

# === STORAGE CONTROL ===
# True = usa Firestore (en la nube)
# False = usa JSON local (en carpeta /data/conversations)
USAR_FIRESTORE = True

# USAR_FIRESTORE = True
# USAR_FIRESTORE = False


def _mask(value: Optional[str]) -> str:
    """Return a masked version of a sensitive string for human-friendly debugging."""
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}...{value[-3:]}"


def validate_config() -> None:
    """
    Optional manual validation helper.

    This function performs no I/O and does not raise by default. Call it
    explicitly when you want to inspect configuration completeness.
    """
    _ = {
        "VERIFY_TOKEN": VERIFY_TOKEN,
        "ACCESS_TOKEN": ACCESS_TOKEN,
        "PHONE_NUMBER_ID": PHONE_NUMBER_ID,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }
