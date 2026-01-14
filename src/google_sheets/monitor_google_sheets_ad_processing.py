"""
Script de monitoreo para Google Sheets que procesa filas con estado "Ad Processing",
consulta grupos de anuncios en Google Ads y actualiza la hoja con los datos.

Dependencias: Google Ads API y el modulo google_sheets_manager.
Nota: ejecucion one-shot (una sola pasada), no es un daemon.
"""

import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Permite ejecutar el script directamente sin instalar el paquete.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'google_ads')))

from google_sheets_manager import get_google_sheets_data, update_google_sheets_entry

# === CONSTANTES DE COLUMNAS/ESTADOS ===
COLUMN_VALIDATION_STATUS = "validation status"
STATUS_TARGET = "Ad Processing"
STATUS_DONE = "Ad Ready"


# === CONSULTAS A GOOGLE ADS ===
def get_ad_groups(client, customer_id, campaign_id):
    """Obtiene los grupos de anuncios para una campana especifica.

    Args:
        client: GoogleAdsClient configurado.
        customer_id: ID del cliente.
        campaign_id: ID de la campana.

    Returns:
        Lista de tuplas (id, name, status) del primer nivel de ad groups.
    """
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT
            ad_group.id,
            ad_group.name,
            ad_group.status
        FROM ad_group
        WHERE ad_group.campaign = 'customers/{customer_id}/campaigns/{campaign_id}'
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    return [(row.ad_group.id, row.ad_group.name, row.ad_group.status.name) for row in response]


# === FLUJO PRINCIPAL ===
def monitor_google_sheets():
    """Monitorea Google Sheets y actualiza datos de ad groups.

    Flujo:
        - Lee la hoja y normaliza encabezados.
        - Filtra filas con Validation Status == "Ad Processing".
        - Valida customer_id (10 digitos) y campaign_id (digitos).
        - Consulta ad groups y actualiza columnas en la hoja.
    """
    print("Checking Google Sheets for ad group updates...")
    df = get_google_sheets_data()
    df.columns = df.columns.str.lower().str.strip()

    print(f"Total rows fetched: {len(df)}")
    print(df[["campaign name", COLUMN_VALIDATION_STATUS]])

    for index, row in df.iterrows():
        google_sheets_row = index + 2
        validation_status = str(row.get(COLUMN_VALIDATION_STATUS, "")).strip()
        if validation_status != STATUS_TARGET:
            continue

        customer_id = str(row.get("customer id", "")).strip()
        campaign_id = str(row.get("campaign id", "")).strip()
        campaign_name = str(row.get("campaign name", "")).strip()

        if not customer_id.isdigit() or len(customer_id) != 10:
            print(f"Skipping row {google_sheets_row} - Invalid Customer ID: {customer_id}")
            continue
        if not campaign_id.isdigit():
            print(f"Skipping row {google_sheets_row} - Invalid Campaign ID: {campaign_id}")
            continue

        try:
            googleads_client = GoogleAdsClient.load_from_storage("google-ads.yaml", version="v21")
            ad_groups = get_ad_groups(googleads_client, customer_id, campaign_id)
            if not ad_groups:
                print(f"No ad groups found for Campaign ID {campaign_id}.")
                continue

            ad_group_id, ad_group_name, ad_group_status = ad_groups[0]
            update_google_sheets_entry(campaign_name, "Ad Group ID", ad_group_id)
            update_google_sheets_entry(campaign_name, "Ad Group Name", ad_group_name)
            update_google_sheets_entry(campaign_name, "Ad Group Status", ad_group_status)
            update_google_sheets_entry(campaign_name, "Validation Status", STATUS_DONE)
            print(f"Google Sheets updated: Ad Group ID, Name, Status, and Validation Status for {campaign_name}")
        except GoogleAdsException as ex:
            print(f"Google Ads API error for Campaign ID {campaign_id}: {ex}")
        except Exception as e:
            print(f"Unexpected error for Campaign ID {campaign_id}: {e}")


if __name__ == "__main__":
    monitor_google_sheets()


# Ejecucion:
# python src/google_sheets/monitor_google_sheets_ad_processing.py
# LEGACY (deprecated): version con loop y sleep disponible en historial de Git.
