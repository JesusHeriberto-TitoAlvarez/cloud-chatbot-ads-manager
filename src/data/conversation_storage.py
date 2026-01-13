"""
Local JSON storage for per-user conversation history.

Files are stored under the conversations folder next to this module. This is
intended for local/development use and is not designed for high-concurrency or
large-scale workloads.
"""

from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

# === PATHS Y CARPETA BASE ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_CONVERSACIONES = os.path.join(BASE_DIR, "conversations")

# Crear carpeta si no existe
if not os.path.exists(CARPETA_CONVERSACIONES):
    os.makedirs(CARPETA_CONVERSACIONES)

# === CONFIGURACION ===
MAX_MENSAJES_USUARIO = 6
MAX_MENSAJES_BOT = 6

# === UTILIDADES INTERNAS ===
def ruta_archivo(numero: str) -> str:
    """Construye la ruta del archivo JSON para un numero.

    Args:
        numero: Identificador del usuario.

    Returns:
        Ruta absoluta al archivo JSON.
    """
    return os.path.join(CARPETA_CONVERSACIONES, f"{numero}.json")


def inicializar_conversacion(numero: str) -> None:
    """Crea el archivo base de conversacion si no existe.

    Args:
        numero: Identificador del usuario.

    Returns:
        None

    Efectos secundarios:
        Crea un archivo JSON en disco con estructura inicial.
    """
    ruta = ruta_archivo(numero)
    if not os.path.exists(ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "nombre": "Usuario",
                    "historial": [],
                    "ultima_actualizacion": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )


# === API PUBLICA ===
def agregar_mensaje(numero: str, role: str, mensaje: str) -> None:
    """Agrega un mensaje al historial del usuario.

    Args:
        numero: Identificador del usuario.
        role: Rol del mensaje ("user" o "assistant").
        mensaje: Contenido del mensaje.

    Returns:
        None

    Efectos secundarios:
        Lee y escribe el archivo JSON del usuario.
    """
    inicializar_conversacion(numero)
    ruta = ruta_archivo(numero)
    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    nuevo_mensaje = {
        "role": role,
        "content": mensaje,
        "timestamp": datetime.utcnow().isoformat(),
    }

    datos["historial"].append(nuevo_mensaje)
    datos["ultima_actualizacion"] = nuevo_mensaje["timestamp"]

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2)


def leer_historial(
    numero: str,
    max_user: int = MAX_MENSAJES_USUARIO,
    max_bot: int = MAX_MENSAJES_BOT,
) -> List[Dict[str, Any]]:
    """Lee el historial combinado del usuario desde disco.

    Args:
        numero: Identificador del usuario.
        max_user: Maximo de mensajes de usuario a incluir.
        max_bot: Maximo de mensajes del bot a incluir.

    Returns:
        Lista de mensajes combinados y ordenados por timestamp.

    Efectos secundarios:
        Lee el archivo JSON del usuario si existe.
    """
    ruta = ruta_archivo(numero)
    if not os.path.exists(ruta):
        return []

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    historial = datos.get("historial", [])

    # Filtrar ultimos mensajes por rol (mantener logica original).
    ultimos_usuario = [m for m in reversed(historial) if m["role"] == "user"][:max_user]
    ultimos_bot = [m for m in reversed(historial) if m["role"] == "assistant"][:max_bot]

    mensajes_combinados = sorted(
        ultimos_usuario + ultimos_bot, key=lambda x: x["timestamp"]
    )
    return mensajes_combinados


def actualizar_nombre(numero: str, nombre: str) -> None:
    """Actualiza el nombre del usuario en el archivo JSON.

    Args:
        numero: Identificador del usuario.
        nombre: Nombre a guardar.

    Returns:
        None

    Efectos secundarios:
        Lee y escribe el archivo JSON del usuario.
    """
    ruta = ruta_archivo(numero)
    if not os.path.exists(ruta):
        inicializar_conversacion(numero)

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    datos["nombre"] = nombre
    datos["ultima_actualizacion"] = datetime.utcnow().isoformat()

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2)


def obtener_nombre(numero: str) -> Optional[str]:
    """Obtiene el nombre del usuario si existe y no es el default.

    Args:
        numero: Identificador del usuario.

    Returns:
        El nombre si existe y no es "Usuario"; de lo contrario None.

    Efectos secundarios:
        Lee el archivo JSON del usuario si existe.
    """
    ruta = ruta_archivo(numero)
    if not os.path.exists(ruta):
        return None

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    nombre = datos.get("nombre", "")
    return nombre if nombre.lower() != "usuario" else None
