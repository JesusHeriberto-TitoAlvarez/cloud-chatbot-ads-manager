"""
Script de prueba manual para validar lectura, escritura y estructura de columnas
en Google Sheets.

Prerequisitos: CredentialsGoogleSheets.json y acceso a la hoja indicada.
"""

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# === CONFIGURACION ===
CREDENTIALS_FILE = "CredentialsGoogleSheets.json"
SHEET_ID = "16MQ_9loHwG1JGV24oD4Qh8XL8hSUU08ZteTEHW12H1U"
SHEET_NAME = "Hoja 1"

# === AUTENTICACION / CONEXION ===
scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    print("✅ Successful connection to Google Sheets.")
except Exception as e:
    print(f"❌ Error connecting to Google Sheets: {e}")
    exit()


# === TESTS ===
def test_read_google_sheets_data():
    """Valida lectura de datos y muestra el DataFrame en consola.

    Prints:
        - Mensaje de hoja vacia o lectura exitosa.
        - DataFrame con los datos leidos.

    Side effects:
        Lee datos desde Google Sheets.
    """
    try:
        values = sheet.get_all_values()
        if not values:
            print("⚠️ The sheet is empty or could not be read.")
            return

        num_columns = len(values[0])  # Detect how many columns exist
        # Rellena filas cortas para alinear columnas.
        values = [row + [""] * (num_columns - len(row)) for row in values]
        df = pd.DataFrame(values[1:], columns=values[0])  # Convert to DataFrame
        print("✅ Data retrieved successfully:")
        print(df)
    except Exception as e:
        print(f"❌ Error reading data from Google Sheets: {e}")


def test_write_google_sheets_data():
    """Valida escritura agregando una fila de prueba.

    Prints:
        - Mensaje de exito o error al escribir.

    Side effects:
        Inserta una fila con append_row en Google Sheets.
    """
    try:
        # Get the number of columns
        values = sheet.get_all_values()
        # Por defecto se asume 19 columnas si la hoja esta vacia.
        num_columns = len(values[0]) if values else 19

        # Create a test row filling all columns
        test_row = [f"Test {i+1}" for i in range(num_columns)]
        sheet.append_row(test_row)
        print("✅ Test row added successfully, filling all columns.")
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")


def test_verify_column_structure():
    """Verifica que la estructura de columnas sea la esperada.

    Prints:
        - Mensajes de estructura correcta o mismatch.
        - Columnas esperadas y encontradas si hay diferencias.

    Side effects:
        Lee datos desde Google Sheets.
    """
    try:
        values = sheet.get_all_values()
        if not values:
            print("⚠️ No data in the sheet to verify.")
            return

        expected_columns = [
            "Number",
            "Customer ID",
            "Campaign Name",
            "Campaign ID",
            "Requested Budget",
            "Assigned Budget",
            "Ad Group ID",
            "Ad ID",
            "Campaign Status",
            "Titles",
            "Descriptions",
            "Keywords",
            "Segmentation",
            "Clicks",
            "Impressions",
            "Total Spend (BOB)",
            "Start Date",
            "End Date",
            "Validation Status",
        ]
        actual_columns = values[0]

        if expected_columns[:len(actual_columns)] == actual_columns:
            print("✅ Column structure is correct.")
        else:
            print("⚠️ Columns do not match the expected structure.")
            print(f"🔹 Expected: {expected_columns}")
            print(f"🔹 Found: {actual_columns}")
    except Exception as e:
        print(f"❌ Error verifying column structure: {e}")


# === EJECUCION ===
test_read_google_sheets_data()
test_write_google_sheets_data()
test_verify_column_structure()

# Ejecucion:
# python src/google_sheets/test_google_sheets.py
