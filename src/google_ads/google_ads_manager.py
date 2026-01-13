"""
Consulta detalles de campanas en Google Ads por nombre.

Requiere un google-ads.yaml configurado con permisos adecuados. El gasto se
obtiene desde metrics.cost_micros.
"""

from typing import Any, Dict, Optional

from google.ads.googleads.client import GoogleAdsClient

# === CONSULTA DE CAMPANAS ===
def get_campaign_details(customer_id: str, campaign_name: str) -> Optional[Dict[str, Any]]:
    """Obtiene todos los detalles posibles de una campana en Google Ads.

    Args:
        customer_id: ID del cliente de Google Ads.
        campaign_name: Nombre de la campana a consultar.

    Returns:
        Un dict con detalles de la campana, o None si no existe.

    Side effects:
        Imprime diagnostico en consola.
    """
    client = GoogleAdsClient.load_from_storage("google-ads.yaml", version="v21")
    ga_service = client.get_service("GoogleAdsService")

    # Incluir metrics.cost_micros para calcular el gasto total.
    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign.start_date,
            campaign.end_date,
            campaign_budget.amount_micros,
            campaign.bidding_strategy_type,
            campaign.serving_status,
            campaign.optimization_score,
            metrics.cost_micros
        FROM campaign
        WHERE campaign.name = '{campaign_name}'
    """

    response = ga_service.search(customer_id=customer_id, query=query)

    for row in response:
        campaign_data = {
            "Campaign ID": row.campaign.id,
            "Campaign Name": row.campaign.name,
            "Status": row.campaign.status.name,
            "Channel Type": row.campaign.advertising_channel_type.name,
            "Start Date": row.campaign.start_date,
            "End Date": row.campaign.end_date,
            "Assigned Budget (Bs)": row.campaign_budget.amount_micros / 1_000_000,  # Convertir a Bs
            "Total Spend (Bs)": row.metrics.cost_micros / 1_000_000,  # Convertir micros a Bs
            "Bidding Strategy": row.campaign.bidding_strategy_type.name,
            "Serving Status": row.campaign.serving_status.name,
            "Optimization Score": row.campaign.optimization_score,
        }
        print("ƒo. Campaign details retrieved:", campaign_data)
        return campaign_data

    print(f"ƒ?O No campaign found for name: {campaign_name}")
    return None
