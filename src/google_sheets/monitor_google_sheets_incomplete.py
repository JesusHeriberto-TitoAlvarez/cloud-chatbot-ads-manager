"""
Script que revisa Google Sheets en modo one-shot, filtra filas con estado "incomplete",
resuelve geo_id por ciudad y ejecuta add_campaign.py para crear campanas.

Se ejecuta directamente via __main__.
"""

import os
import sys
import subprocess

# Permite ejecutar el script directamente desde src/google_sheets/.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'google_ads')))

from google_sheets_manager import get_google_sheets_data, update_google_sheets_entry

# IDs de geoTargetConstant de Google Ads para Bolivia.
CITY_TO_GEO_ID = {
    "la paz": "20084",
    "cochabamba": "20083",
    "santa cruz": "20085",
    "potosi": "9069868",
    "beni": "9069869",
    "chuquisaca": "9069870",
    "pando": "9069871",
    "oruro": "9069872",
    "tarija": "9075434",
}

# Ciudad por defecto si no se encuentra la segmentacion proporcionada.
DEFAULT_CITY = "la paz"
DEFAULT_GEO_ID = CITY_TO_GEO_ID[DEFAULT_CITY]


def monitor_google_sheets():
    """Monitorea Google Sheets y crea campanas cuando corresponde.

    Flujo:
        - Carga el DataFrame.
        - Normaliza columnas.
        - Itera filas y aplica el criterio de procesamiento.
        - Resuelve geo_id por ciudad.
        - Ejecuta add_campaign.py.
        - Actualiza el estado en la hoja si el comando fue exitoso.

    Side effects:
        Imprime en consola, ejecuta subprocess y escribe en Google Sheets.
    """
    print("Checking Google Sheets for campaign updates...")

    # Carga y normalizacion de data
    df = get_google_sheets_data()
    df.columns = df.columns.str.lower().str.strip()

    for index, row in df.iterrows():
        # Iteracion y lectura de fila
        number = str(row.get("number", "")).strip()
        validation_status = str(row.get("validation status", "")).strip()
        customer_id = str(row.get("customer id", "")).strip()
        campaign_name = str(row.get("campaign name", "")).strip()
        requested_budget = str(row.get("requested budget", "")).strip()
        segmentation = str(row.get("segmentation", "")).strip().lower()

        # Mostrar en consola los datos de la fila actual
        print(
            f"Row {index}: Number={number}, Validation Status={validation_status}, "
            f"Customer ID={customer_id}, Campaign Name={campaign_name}, "
            f"Requested Budget={requested_budget}, Segmentation={segmentation}"
        )

        # Criterio de procesamiento
        if number and customer_id and campaign_name and requested_budget and validation_status.lower() == "incomplete":
            # Resolucion de geo_id
            geo_id = CITY_TO_GEO_ID.get(segmentation, DEFAULT_GEO_ID)
            segmentation_used = segmentation if segmentation in CITY_TO_GEO_ID else DEFAULT_CITY

            print(
                f"Creating campaign for Customer ID: {customer_id}, Campaign Name: {campaign_name}, "
                f"Segmentation: {segmentation_used} (Geo ID: {geo_id})"
            )

            # Ejecucion de add_campaign.py
            result = subprocess.run([
                "python", "src/google_ads/add_campaign.py", "-c", customer_id, "-n", campaign_name, "-l", geo_id
            ], capture_output=True, text=True)

            # Mostrar la salida del script add_campaign.py
            print(result.stdout)
            print(result.stderr)

            # Actualizacion de estado en Sheets
            if result.returncode == 0:
                update_google_sheets_entry(campaign_name, "Validation Status", "campaign processing")
                print(f"Campaign Processing: {campaign_name}")
            else:
                print(f"Error creating campaign for {campaign_name}")


if __name__ == "__main__":
    monitor_google_sheets()


# Ejecucion:
# python src/google_sheets/monitor_google_sheets_incomplete.py
# LEGACY (deprecated): version con loop/intervalo disponible en historial de Git.
