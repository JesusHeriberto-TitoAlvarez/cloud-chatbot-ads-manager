"""
Script que monitorea Google Sheets en modo one-shot, consulta detalles de campanas
en Google Ads por nombre y actualiza la hoja cuando el estado es "Campaign Processing".

Se ejecuta directamente via __main__.
"""

import os
import sys

import pandas as pd

# Permite ejecutar el script directamente sin empaquetar el modulo.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'google_ads')))

from google_sheets_manager import get_google_sheets_data, update_google_sheets_entry
from google_ads_manager import get_campaign_details

# === CONSTANTES INTERNAS ===
STATUS_PROCESSING = "campaign processing"
STATUS_READY = "Campaign Ready"


def monitor_google_sheets():
    """Monitorea Google Sheets y actualiza detalles de campanas.

    No recibe argumentos ni retorna valores. Imprime en consola y actualiza
    campos en la hoja cuando se cumplen los criterios de filtrado.

    Actualiza: Campaign ID, Assigned Budget, Campaign Status, Total Spend (BOB),
    Start Date, End Date, Validation Status.
    """
    print("Checking Google Sheets for campaign processing updates...")

    # Lectura de datos
    df = get_google_sheets_data()

    # Normalizacion de columnas
    df.columns = df.columns.str.lower().str.strip()

    for index, row in df.iterrows():
        # Lectura de valores por fila
        number = str(row.get("number", "")).strip()
        validation_status = str(row.get("validation status", "")).strip()
        customer_id = str(row.get("customer id", "")).strip()
        campaign_name = str(row.get("campaign name", "")).strip()
        requested_budget = str(row.get("requested budget", "")).strip()

        # Mostrar en consola los datos de la fila actual
        print(
            f"Row {index}: Number={number}, Validation Status={validation_status}, "
            f"Customer ID={customer_id}, Campaign Name={campaign_name}, Requested Budget={requested_budget}"
        )

        # Condicion principal de procesamiento
        if (
            number
            and customer_id
            and campaign_name
            and requested_budget
            and validation_status.lower() == STATUS_PROCESSING
        ):
            print(f"Retrieving campaign details for Customer ID: {customer_id}, Campaign Name: {campaign_name}")

            # Obtener detalles de la campana desde Google Ads
            campaign_data = get_campaign_details(customer_id, campaign_name)

            if campaign_data:
                update_google_sheets_entry(campaign_name, "Campaign ID", campaign_data.get("Campaign ID"))
                update_google_sheets_entry(campaign_name, "Assigned Budget", campaign_data.get("Assigned Budget (Bs)"))
                update_google_sheets_entry(campaign_name, "Campaign Status", campaign_data.get("Status"))

                # Total Spend (BOB): assigned_budget * ((end - start).days + 1)
                total_spend = campaign_data.get("Assigned Budget (Bs)") * (
                    (pd.to_datetime(campaign_data.get("End Date")) - pd.to_datetime(campaign_data.get("Start Date"))).days + 1
                )
                update_google_sheets_entry(campaign_name, "Total Spend (BOB)", total_spend)
                update_google_sheets_entry(campaign_name, "Start Date", campaign_data.get("Start Date"))
                update_google_sheets_entry(campaign_name, "End Date", campaign_data.get("End Date"))
                update_google_sheets_entry(campaign_name, "Validation Status", STATUS_READY)
                print(f"Updated Google Sheets with campaign details for {campaign_name}")
            else:
                print(f"Failed to retrieve campaign details for {campaign_name}")


if __name__ == "__main__":
    monitor_google_sheets()


# Ejecucion:
# python src/google_sheets/monitor_google_sheets_campaign_processing.py
# LEGACY (deprecated): version con loop/intervalo disponible en historial de Git.
