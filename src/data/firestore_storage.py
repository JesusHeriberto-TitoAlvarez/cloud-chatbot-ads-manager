"""
Storage de conversaciones en Firestore.

Inicializa Firebase Admin una sola vez y expone operaciones para guardar y leer
historiales. Incluye control de duplicados por message_id.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore

# === CREDENCIALES E INICIALIZACION FIREBASE ===
RUTA_CREDENCIALES = os.path.join(os.path.dirname(__file__), "../../CredentialsGoogleFirestore.json")

# Inicializar Firebase solo una vez
if not firebase_admin._apps:
    cred = credentials.Certificate(RUTA_CREDENCIALES)
    firebase_admin.initialize_app(cred, {
        "projectId": "servidor-chatbot-448603"
    })

# === CLIENTE FIRESTORE ===
db = firestore.client()

# === CONFIGURACION Y COLECCIONES ===
COLECCION_CONVERSACIONES = "conversations"
MAX_MENSAJES_USUARIO = 6
MAX_MENSAJES_BOT = 6


# === API DE CONVERSACIONES ===
def guardar_mensaje(numero: str, role: str, mensaje: str) -> None:
    """Guarda un mensaje en el historial del usuario.

    Args:
        numero: Identificador del usuario.
        role: Rol del mensaje ("user" o "assistant").
        mensaje: Contenido del mensaje.

    Returns:
        None

    Efectos secundarios:
        Lee y escribe documentos en Firestore.
    """
    doc_ref = db.collection(COLECCION_CONVERSACIONES).document(numero)
    doc = doc_ref.get()
    nuevo_mensaje = {
        "role": role,
        "content": mensaje,
        "timestamp": datetime.utcnow().isoformat()
    }

    if doc.exists:
        datos = doc.to_dict()
        historial = datos.get("historial", [])
        historial.append(nuevo_mensaje)
        doc_ref.update({
            "historial": historial,
            "ultima_actualizacion": nuevo_mensaje["timestamp"]
        })
    else:
        doc_ref.set({
            "nombre": "Usuario",
            "historial": [nuevo_mensaje],
            "ultima_actualizacion": nuevo_mensaje["timestamp"]
        })


def leer_historial(
    numero: str,
    max_user: int = MAX_MENSAJES_USUARIO,
    max_bot: int = MAX_MENSAJES_BOT,
) -> List[Dict[str, Any]]:
    """Lee el historial combinado del usuario.

    Args:
        numero: Identificador del usuario.
        max_user: Maximo de mensajes de usuario a incluir.
        max_bot: Maximo de mensajes del bot a incluir.

    Returns:
        Lista de mensajes combinados y ordenados por timestamp.

    Efectos secundarios:
        Lee documentos en Firestore.
    """
    doc_ref = db.collection(COLECCION_CONVERSACIONES).document(numero)
    doc = doc_ref.get()
    if not doc.exists:
        return []

    datos = doc.to_dict()
    historial = datos.get("historial", [])

    ultimos_usuario = [
        m for m in reversed(historial)
        if isinstance(m, dict) and m.get("role") == "user"
    ][:max_user]

    ultimos_bot = [
        m for m in reversed(historial)
        if isinstance(m, dict) and m.get("role") == "assistant"
    ][:max_bot]

    combinados = sorted(ultimos_usuario + ultimos_bot, key=lambda x: x.get("timestamp", ""))
    return combinados


def actualizar_nombre(numero: str, nombre: str) -> None:
    """Actualiza el nombre del usuario en Firestore.

    Args:
        numero: Identificador del usuario.
        nombre: Nombre a guardar.

    Returns:
        None

    Efectos secundarios:
        Escribe documentos en Firestore.
    """
    doc_ref = db.collection(COLECCION_CONVERSACIONES).document(numero)
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update({
            "nombre": nombre,
            "ultima_actualizacion": datetime.utcnow().isoformat()
        })
    else:
        doc_ref.set({
            "nombre": nombre,
            "historial": [],
            "ultima_actualizacion": datetime.utcnow().isoformat()
        })


def obtener_nombre(numero: str) -> Optional[str]:
    """Obtiene el nombre del usuario si es distinto de "usuario".

    Args:
        numero: Identificador del usuario.

    Returns:
        El nombre si existe y no es "usuario"; de lo contrario None.

    Efectos secundarios:
        Lee documentos en Firestore.
    """
    doc_ref = db.collection(COLECCION_CONVERSACIONES).document(numero)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    datos = doc.to_dict()
    nombre = datos.get("nombre", "")
    return nombre if nombre.lower() != "usuario" else None


# === CONTROL DE MENSAJES DUPLICADOS ===
COLECCION_MENSAJES_PROCESADOS = "mensajes_procesados"


def ya_procesado(message_id: str) -> bool:
    """Indica si un message_id ya fue procesado.

    Args:
        message_id: Identificador del mensaje.

    Returns:
        True si ya existe; False si no existe.

    Efectos secundarios:
        Lee documentos en Firestore.
    """
    return db.collection(COLECCION_MENSAJES_PROCESADOS).document(message_id).get().exists


def registrar_id_procesado(message_id: str, numero: str) -> bool:
    """Registra un message_id si no existe previamente.

    Args:
        message_id: Identificador del mensaje.
        numero: Identificador del usuario.

    Returns:
        False si el id ya estaba registrado; True si se registro en esta llamada.

    Efectos secundarios:
        Lee y escribe documentos en Firestore.
    """
    doc_ref = db.collection(COLECCION_MENSAJES_PROCESADOS).document(message_id)
    if doc_ref.get().exists:
        return False

    doc_ref.set({
        "numero": numero,
        "timestamp": datetime.utcnow().isoformat()
    })
    return True


# LEGACY (deprecated): versiones anteriores disponibles en el historial de Git.
