"""
Script que revisa Google Sheets en modo one-shot, valida filas con "Campaign Ready",
ejecuta add_ad_to_campaign.py y actualiza el estado a "Ad Processing".

Se ejecuta directamente via __main__.
"""

import os
import sys
import subprocess
import random
import string

# Permite ejecutar el script directamente sin empaquetar el modulo.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'google_ads')))

from google_sheets_manager import get_google_sheets_data, update_google_sheets_entry


def generate_random_suffix(length=3):
    """Genera un sufijo aleatorio de letras mayusculas."""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


def monitor_google_sheets():
    """Monitorea Google Sheets y ejecuta add_ad_to_campaign.py si se cumplen los requisitos.

    Side effects:
        - Imprime en consola.
        - Llama a subprocess para crear anuncios.
        - Actualiza Google Sheets si la ejecucion fue exitosa.
    """
    print("\U0001F4CC Checking Google Sheets for campaign readiness updates...")

    # Carga de data
    df = get_google_sheets_data()

    # Normalizacion de columnas
    df.columns = df.columns.str.lower().str.strip()

    # Depuracion: ver cuantas filas se han recuperado y mostrar primeros valores
    print(f"Total rows fetched: {len(df)}")
    print(df[["campaign name", "validation status"]])  # Muestra los primeros valores

    for index, row in df.iterrows():
        # +2 por encabezado y ajuste de indices de Google Sheets
        google_sheets_row = index + 2

        # Verificar si Validation Status es 'Campaign Ready'
        validation_status = str(row.get("validation status", "")).strip()
        if validation_status != "Campaign Ready":
            continue

        # Leer los valores de cada fila y limpiar espacios
        customer_id = str(row.get("customer id", "")).strip()
        campaign_id = str(row.get("campaign id", "")).strip()
        campaign_name = str(row.get("campaign name", "")).strip()
        titles = str(row.get("titles", "")).strip()
        descriptions = str(row.get("descriptions", "")).strip()
        keywords = str(row.get("keywords", "")).strip()
        campaign_status = str(row.get("campaign status", "")).strip()

        # required_fields usa nombres normalizados (df.columns ya esta en lower/strip)
        required_fields = [
            "customer id",
            "campaign id",
            "campaign name",
            "titles",
            "descriptions",
            "keywords",
            "assigned budget",
            "campaign status",
        ]
        missing_fields = [field for field in required_fields if row.get(field) in [None, ""]]

        if missing_fields:
            print(f"\u274C Skipping row {google_sheets_row} due to missing fields: {', '.join(missing_fields)}")
            continue

        if not customer_id.isdigit() or len(customer_id) != 10:
            print(f"Skipping row {google_sheets_row} - Invalid Customer ID: {customer_id}")
            continue

        if not campaign_id.isdigit():
            print(f"Skipping row {google_sheets_row} - Invalid Campaign ID: {campaign_id}")
            continue

        if not campaign_name:
            print(f"Skipping row {google_sheets_row} - Campaign Name is missing.")
            continue

        ad_group_name = f"{campaign_name}_{generate_random_suffix()}"

        print("Executing add_ad_to_campaign.py with:")
        print(f"  - Customer ID: '{customer_id}'")
        print(f"  - Campaign ID: '{campaign_id}'")
        print(f"  - Ad Group Name: '{ad_group_name}'")
        print(f"  - Titles: {titles}")
        print(f"  - Descriptions: {descriptions}")
        print(f"  - Keywords: {keywords}")

        try:
            assigned_budget = float(str(row.get("assigned budget", "")).strip())
            if assigned_budget > 5:
                print(f"\u274C Skipping {campaign_name} - Assigned Budget ({assigned_budget}) exceeds limit.")
                continue
        except ValueError:
            print(f"\u274C Error: Assigned Budget is not a valid number for Campaign: {campaign_name}")
            continue

        # Separador actual: '|'
        titles_list = [t.strip() for t in titles.split("|") if t.strip()]
        descriptions_list = [d.strip() for d in descriptions.split("|") if d.strip()]
        keywords_list = [k.strip() for k in keywords.split("|") if k.strip()]

        if not (3 <= len(titles_list) <= 15):
            print(f"\u274C Skipping {campaign_name} - Titles validation failed.")
            continue
        if not (2 <= len(descriptions_list) <= 4):
            print(f"\u274C Skipping {campaign_name} - Descriptions validation failed.")
            continue
        if len(keywords_list) > 10:
            print(f"\u274C Skipping {campaign_name} - Keywords validation failed.")
            continue
        if campaign_status != "PAUSED":
            print(f"\u274C Skipping {campaign_name} - Campaign Status is not 'PAUSED'.")
            continue

        print(f"All conditions met. Creating Ad Group: {ad_group_name} for Campaign: {campaign_name}")
        print("Running add_ad_to_campaign.py...")

        result = subprocess.run([
            "python", "src/google_ads/add_ad_to_campaign.py",
            "-c", customer_id,
            "-n", campaign_id,
            "-g", ad_group_name,
            "-t", titles,
            "-d", descriptions,
            "-k", keywords
        ], capture_output=True, text=True)

        print("Output from add_ad_to_campaign.py:")
        print(result.stdout)
        print(result.stderr)

        if result.returncode == 0:
            update_google_sheets_entry(campaign_name, "Validation Status", "Ad Processing")
            print(f"Google Sheets actualizado: 'Validation Status' cambiado a 'Ad Processing' para Campaign Name {campaign_name}")
            print("Process completed successfully!")
        else:
            print(f"\u274C Error executing add_ad_to_campaign.py for Campaign ID {campaign_id}")


if __name__ == "__main__":
    monitor_google_sheets()


# Ejecucion:
# python src/google_sheets/monitor_google_sheets_campaign_ready.py
# LEGACY (deprecated): versiones anteriores (incluyendo modo loop) disponibles en el historial de Git.
