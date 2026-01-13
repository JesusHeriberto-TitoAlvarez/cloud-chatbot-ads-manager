"""
Google Sheets connector for registering, reading, and updating users by phone number.

This module uses gspread and a service account to access the spreadsheet.
HEADERS is loaded at import time and assumed stable; restart the process if
the sheet headers change.
"""

import os
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

# === PATHS / CREDENCIALES ===
# Ruta absoluta a las credenciales.
CREDENTIALS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'CredentialsGoogleSheets.json'))

# === CONFIGURACION DE SHEET ===
SHEET_ID = "16MQ_9loHwG1JGV24oD4Qh8XL8hSUU08ZteTEHW12H1U"
WORKSHEET_NAME = "Interacciones_Reales_v01"

# Columnas esperadas (evita magic strings repetidos).
COLUMN_NUMBER_NAME = "Number"
COLUMN_CUSTOMER_ID = "Customer ID"
COLUMN_VALIDATION_STATUS = "Validation Status"
COLUMN_ESTADO_CAMPANA = "Estado Campana"
COLUMN_ESTADO_ANUNCIO = "Estado Anuncio"

# === AUTENTICACION / CLIENTE ===
scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)

# === ENCABEZADOS ===
# Se leen una sola vez al importar el modulo.
HEADERS = sheet.row_values(1)

# === FUNCIONES PUBLICAS ===
def get_user_row(phone_number: str) -> Optional[int]:
    """Devuelve el numero de fila del usuario segun su numero (columna 'Number').

    Args:
        phone_number: Numero de telefono del usuario.

    Returns:
        Indice de fila (1-based) si existe, o None si no se encuentra.

    Raises:
        ValueError: Si la columna 'Number' no esta presente en la hoja.
    """
    if COLUMN_NUMBER_NAME not in HEADERS:
        raise ValueError("La columna 'Number' no estÇ­ presente en la hoja.")
    col_index = HEADERS.index(COLUMN_NUMBER_NAME) + 1
    values = sheet.col_values(col_index)
    for idx, val in enumerate(values[1:], start=2):
        if val.strip() == phone_number.strip():
            return idx
    return None


def create_user_if_not_exists(phone_number: str) -> None:
    """Crea una nueva fila con valores iniciales si el numero no esta registrado aun.

    Args:
        phone_number: Numero de telefono del usuario.

    Returns:
        None

    Raises:
        ValueError: Si la columna 'Number' no esta presente en la hoja.
    """
    if not get_user_row(phone_number):
        new_row = [""] * len(HEADERS)

        if COLUMN_NUMBER_NAME in HEADERS:
            new_row[HEADERS.index(COLUMN_NUMBER_NAME)] = phone_number
        if COLUMN_CUSTOMER_ID in HEADERS:
            new_row[HEADERS.index(COLUMN_CUSTOMER_ID)] = "8829466542"
        if COLUMN_VALIDATION_STATUS in HEADERS:
            new_row[HEADERS.index(COLUMN_VALIDATION_STATUS)] = "incomplete"
        if COLUMN_ESTADO_CAMPANA in HEADERS:
            new_row[HEADERS.index(COLUMN_ESTADO_CAMPANA)] = "no iniciada"
        if COLUMN_ESTADO_ANUNCIO in HEADERS:
            new_row[HEADERS.index(COLUMN_ESTADO_ANUNCIO)] = "no iniciado"

        sheet.append_row(new_row, value_input_option="USER_ENTERED")
        print(f"NÇ§mero {phone_number} registrado con Customer ID y estados iniciales.")
    else:
        print(f"ƒ\"ûEl nÇ§mero {phone_number} ya estaba registrado.")


def update_user_field(phone_number: str, field_name: str, value: str) -> None:
    """Actualiza un campo especifico de un usuario.

    Args:
        phone_number: Numero de telefono del usuario.
        field_name: Nombre de la columna a actualizar.
        value: Valor nuevo a asignar.

    Returns:
        None

    Raises:
        ValueError: Si la columna 'Number' no esta presente en la hoja.
    """
    row = get_user_row(phone_number)
    if row:
        if field_name in HEADERS:
            col = HEADERS.index(field_name) + 1
            sheet.update_cell(row, col, value)
            print(f"Campo '{field_name}' actualizado para {phone_number} con: {value}")
        else:
            print(f"La columna '{field_name}' no existe en la hoja.")
    else:
        print(f"NÇ§mero no encontrado: {phone_number}")


def get_user_field(phone_number: str, field_name: str) -> Optional[str]:
    """Lee el valor de un campo especifico.

    Args:
        phone_number: Numero de telefono del usuario.
        field_name: Nombre de la columna a leer.

    Returns:
        El valor de la celda si existe, o None si no se encuentra.

    Raises:
        ValueError: Si la columna 'Number' no esta presente en la hoja.
    """
    row = get_user_row(phone_number)
    if row and field_name in HEADERS:
        col = HEADERS.index(field_name) + 1
        return sheet.cell(row, col).value
    return None


def delete_user(phone_number: str) -> None:
    """Elimina por completo la fila de un usuario.

    Args:
        phone_number: Numero de telefono del usuario.

    Returns:
        None

    Raises:
        ValueError: Si la columna 'Number' no esta presente en la hoja.
    """
    row = get_user_row(phone_number)
    if row:
        sheet.delete_rows(row)
        print(f"Fila eliminada para el nÇ§mero {phone_number}")


# LEGACY (deprecated): versiones anteriores en historial de Git.
