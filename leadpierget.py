import requests
import pandas as pd
import schedule
import time 

ACCESS_TOKEN = "EAA7hTdVPjsgBPbbzPlMEZClRAJ2c71DRqwyCnZB7FX0GtybOyPrYFoJrjVgqOYTXJW5QVGMaQfpHJBcMY9tCB3GW8s6BZAtiZA3wdNe7Kq4CcJjMBgg7ED0n2A3iTNn7KJR21t1jeNgacFcMmcENBbcZAqZCrVtMxwjVE9e6Usk9CWzenEmlFHdGglPlO4a52kJTjhWyqiUQZDZD"
AD_ACCOUNT_ID = [428549066458338, 653164011031498, 1122267929000780, 1172700037197465]   # id de tu cuenta publicitaria
GRAPH_API_VERSION = "v23.0"

LEADPIER_URL = "https://dash.leadpier.com/marketer-statistics/sources?limit=200&offset=0&orderDirection=DESC&groupBy=HOUR&orderBy=visitors&periodFrom=today&periodTo=today&source=BM5_1"

def traerdata():
    lp_response = requests.get(LEADPIER_URL).json();
    if "data" not in lp_response:
        print("⚠️ Error en Leadpier:", lp_response)
        return
    return lp_response

# --- LLAMAR A LA FUNCIÓN ---
if __name__ == "__main__":
    data = traerdata()
    if data:
        print("✅ Datos obtenidos de Leadpier:")
        print(data)
