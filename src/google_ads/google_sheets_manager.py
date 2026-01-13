"""
Modulo de utilidades para leer y actualizar la hoja de Google Sheets del proyecto.

La autenticacion se realiza mediante service account y el worksheet se inicializa
al importar el modulo.
"""

from typing import Any, Dict, List, Optional

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# === CONFIGURACION ===
SHEET_ID = "16MQ_9loHwG1JGV24oD4Qh8XL8hSUU08ZteTEHW12H1U"
SHEET_NAME = "Interacciones_Reales_v01"  # Asegurate de que el nombre coincida
CREDENTIALS_FILE = "CredentialsGoogleSheets.json"  # Ruta al archivo de credenciales

# === AUTENTICACION Y WORKSHEET ===
scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)


# === OPERACIONES DE LECTURA ===
def get_google_sheets_data() -> "pd.DataFrame":
    """Obtiene los datos de la hoja como DataFrame.

    Returns:
        DataFrame con los registros de la hoja.

    Side effects:
        Lee datos desde Google Sheets.
    """
    data = sheet.get_all_records()
    return pd.DataFrame(data)


# === OPERACIONES DE ACTUALIZACION ===
def update_google_sheets_entry_by_row(row_index: int, updates: Dict[str, Any]) -> None:
    """Actualiza multiples celdas en una fila especifica usando los headers.

    Args:
        row_index: Numero de fila (1-based) en la hoja.
        updates: Diccionario de columna -> valor nuevo.

    Returns:
        None

    Side effects:
        Escribe celdas en Google Sheets.
    """
    headers = sheet.row_values(1)
    for column_name, new_value in updates.items():
        if column_name in headers:
            column_index = headers.index(column_name) + 1
            try:
                sheet.update_cell(row_index, column_index, new_value)
                print(f"Fila {row_index} actualizada: {column_name} = {new_value}")
            except Exception as e:
                print(f"Error al actualizar la fila {row_index} en Google Sheets: {e}")


def update_google_sheets_entry(campaign_name: str, column_name: str, new_value: Any) -> None:
    """Modifica una celda usando Campaign Name como referencia.

    Args:
        campaign_name: Nombre de la campana.
        column_name: Nombre de la columna a actualizar.
        new_value: Valor nuevo.

    Returns:
        None

    Side effects:
        Lee y escribe en Google Sheets.
    """
    df = get_google_sheets_data()
    df.columns = df.columns.str.lower().str.strip()
    row_index = df.index[df["campaign name"].str.lower().str.strip() == campaign_name.lower().strip()].tolist()

    if row_index:
        row_number = row_index[0] + 2  # Ajuste por encabezado
        update_google_sheets_entry_by_row(row_number, {column_name: new_value})
    else:
        print(f"No se encontró la campaña con nombre {campaign_name}.")


# === OPERACIONES DE INSERCION ===
def add_new_entry(
    user_name: str,
    number: str,
    customer_id: str,
    campaign_name: str,
    requested_budget: Any,
    assigned_budget: Any,
    ad_group_id: Any,
    ad_group_name: Any,
    ad_group_status: Any,
    titles: Any,
    descriptions: Any,
    keywords: Any,
    start_date: Any,
    end_date: Any,
    validation_status: Any,
) -> None:
    """Agrega una nueva entrada en la hoja con los datos proporcionados.

    Args:
        user_name: Nombre del usuario.
        number: Numero de telefono.
        customer_id: ID del cliente de Google Ads.
        campaign_name: Nombre de la campana.
        requested_budget: Presupuesto solicitado.
        assigned_budget: Presupuesto asignado.
        ad_group_id: ID del grupo de anuncios.
        ad_group_name: Nombre del grupo de anuncios.
        ad_group_status: Estado del grupo de anuncios.
        titles: Titulos de anuncios.
        descriptions: Descripciones de anuncios.
        keywords: Palabras clave.
        start_date: Fecha de inicio.
        end_date: Fecha de fin.
        validation_status: Estado de validacion.

    Returns:
        None

    Side effects:
        Inserta una fila en Google Sheets.
    """
    sheet.append_row([
        user_name,
        number,
        customer_id,
        campaign_name,
        requested_budget,
        assigned_budget,
        ad_group_id,
        ad_group_name,
        ad_group_status,
        titles,
        descriptions,
        keywords,
        start_date,
        end_date,
        validation_status,
    ])
    print(f"Nueva entrada agregada para {campaign_name}")


def add_user_phone_number(number: str) -> None:
    """Agrega una fila con el numero en la columna 'Number'.

    Args:
        number: Numero de telefono a registrar.

    Returns:
        None

    Side effects:
        Inserta una fila en Google Sheets.
    """
    try:
        headers = sheet.row_values(1)
        row_data = [""] * len(headers)
        if "Number" in headers:
            number_index = headers.index("Number")
            row_data[number_index] = number
            sheet.append_row(row_data)
            print(f"Número {number} registrado correctamente en Google Sheets.")
        else:
            print("La columna 'Number' no fue encontrada en la hoja.")
    except Exception as e:
        print(f"Error al agregar número en Google Sheets: {e}")


def update_user_name_by_number(number: str, new_name: str) -> None:
    """Actualiza el nombre del usuario usando su numero de telefono.

    Args:
        number: Numero de telefono del usuario.
        new_name: Nombre actualizado.

    Returns:
        None

    Side effects:
        Lee y escribe en Google Sheets.
    """
    try:
        df = get_google_sheets_data()
        df.columns = df.columns.str.lower().str.strip()

        if "number" not in df.columns:
            print("❌ La columna 'Number' no fue encontrada en el DataFrame.")
            return

        row_index = df.index[df["number"].astype(str) == str(number)].tolist()
        if row_index:
            row_number = row_index[0] + 2  # +2 por encabezado
            update_google_sheets_entry_by_row(row_number, {"User Name": new_name})
            print(f"✅ Nombre actualizado para {number}: {new_name}")
        else:
            print(f"⚠️ No se encontró el número {number} en la hoja.")
    except Exception as e:
        print(f"❌ Error al actualizar nombre por número: {e}")


# LEGACY (deprecated): versiones anteriores en historial de Git.
