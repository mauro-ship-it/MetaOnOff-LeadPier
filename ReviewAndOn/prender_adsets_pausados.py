import os
import sys
import time
import json
import datetime as dt
import requests
import pandas as pd
from dotenv import load_dotenv

# Agregar el path del directorio padre para importar leadpier_auth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from leadpier_auth import ensure_leadpier_token

# ================== CONFIG ==================
load_dotenv(dotenv_path="../enviorement.env")

GRAPH_API_VERSION = "v23.0"
FB_ACCESS_TOKEN   = os.getenv("FB_ACCESS_TOKEN")
LEADPIER_BEARER   = os.getenv("LEADPIER_BEARER")
PROXY_URL         = os.getenv("PROXY_URL")

# Cuentas a revisar
AD_ACCOUNTS = [
    "act_1122267929000780",
    "act_1172700037197465",
    "act_1192065285119034",
]

# Criterios para prender adsets
MIN_SPEND_THRESHOLD = 100.0  # USD - Mínimo spend requerido
MIN_ROI_THRESHOLD = 0.0      # ROI mínimo requerido

# ================== HELPERS ==================
def today_utc_minus_4_str():
    """Devuelve la fecha de hoy en UTC-4 (timezone de Facebook)"""
    utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
    return utc_minus_4.strftime("%Y-%m-%d")

def week_ago_utc_minus_4_str():
    """Devuelve la fecha de hace una semana en UTC-4"""
    utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
    week_ago = utc_minus_4 - dt.timedelta(days=7)
    return week_ago.strftime("%Y-%m-%d")

def is_within_execution_window_utc_minus_4():
    """Verifica si la hora actual está dentro del rango de ejecución (7PM UTC-4 a 7AM UTC-4)"""
    utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
    current_hour = utc_minus_4.hour
    
    # Rango de ejecución: 19:00 (7PM) a 07:00 (7AM) del día siguiente
    # Esto incluye: 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6
    return current_hour >= 19 or current_hour < 7

def leadpier_headers():
    """Headers exactos que usa el navegador - NO usar proxy con Leadpier"""
    return {
        "authorization": f"bearer {LEADPIER_BEARER}",  # minúsculas como el navegador
        "content-type": "application/json",
        "accept": "application/json",
        "origin": "https://dash.leadpier.com",
        "referer": "https://dash.leadpier.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
    }

def get_proxies():
    """Retorna el diccionario de proxies para usar en requests"""
    if PROXY_URL:
        return {"http": PROXY_URL, "https": PROXY_URL}
    return None

def leadpier_request_with_retry(method, url, max_retries=3, initial_timeout=30, **kwargs):
    """
    Realiza request a Leadpier con retry logic y timeouts incrementales.
    
    Args:
        method: 'GET' o 'POST'
        url: URL de la API
        max_retries: número máximo de reintentos
        initial_timeout: timeout inicial en segundos
        **kwargs: otros argumentos para requests (headers, data, params, etc.)
    
    Returns:
        Response object o None si falla después de todos los reintentos
    """
    for attempt in range(max_retries):
        # Incrementar timeout en cada reintento
        timeout = initial_timeout * (attempt + 1)
        
        try:
            print(f"[Leadpier] Intento {attempt + 1}/{max_retries} (timeout: {timeout}s)...")
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=timeout, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, timeout=timeout, **kwargs)
            else:
                raise ValueError(f"Método no soportado: {method}")
            
            # Si llegamos aquí, la request fue exitosa
            return response
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"[Leadpier] Error de conexión/timeout en intento {attempt + 1}: {type(e).__name__}")
            
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)  # Esperar 5s, 10s, 15s...
                print(f"[Leadpier] Esperando {wait_time}s antes del siguiente intento...")
                time.sleep(wait_time)
            else:
                print("[Leadpier] ERROR: Todos los reintentos fallaron por timeout/conexión")
                return None
                
        except Exception as e:
            print(f"[Leadpier] Error inesperado: {type(e).__name__}: {e}")
            return None
    
    return None

def fb_get(url, params, retries=3, timeout=30):
    proxies = get_proxies()
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout, proxies=proxies)
            if r.status_code == 200:
                return r.json()
            print(f"[FB GET] {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[FB GET] intento {i+1} error: {e}")
        time.sleep(2)
    return {}

def fb_post(url, data, retries=3, timeout=30):
    proxies = get_proxies()
    for i in range(retries):
        try:
            r = requests.post(url, data=data, timeout=timeout, proxies=proxies)
            if r.status_code in (200, 201):
                return r.json()
            print(f"[FB POST] {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[FB POST] intento {i+1} error: {e}")
        time.sleep(2)
    return {}

# ================== LEADPIER ==================
LP_BASE = "https://webapi.leadpier.com"

def fetch_leadpier_sources_df():
    """Obtiene datos de Leadpier para el rango de fechas especificado"""
    payload = {
        "limit": 200,
        "offset": 0,
        "orderDirection": "DESC",
        "groupBy": "DAY",
        "orderBy": "visitors",
        "periodFrom": week_ago_utc_minus_4_str(),
        "periodTo": today_utc_minus_4_str(),
        "source": "BM5_1",
    }

    url = f"{LP_BASE}/v1/api/stats/user/sources"
    # IMPORTANTE: NO usar proxy para Leadpier - lo bloquea con 401
    r = leadpier_request_with_retry('POST', url, headers=leadpier_headers(), data=json.dumps(payload), max_retries=3, initial_timeout=30)

    if r is None:
        print("[Leadpier] ERROR: No se pudo conectar a Leadpier después de varios reintentos")
        print("[Leadpier] Continuando sin datos de revenue...")
        return pd.DataFrame()

    if r.status_code != 200:
        print("[Leadpier] Status:", r.status_code, r.text[:200])
        return pd.DataFrame()

    try:
        data = r.json()
    except Exception as e:
        print("[Leadpier] JSON error:", e, r.text[:200])
        return pd.DataFrame()

    if not isinstance(data, dict) or "data" not in data:
        print("[Leadpier] Respuesta sin 'data':", str(data)[:200])
        return pd.DataFrame()

    raw_data = data["data"]
    
    if not raw_data:
        print("[Leadpier] Sin datos disponibles")
        return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
    
    # Manejar diferentes tipos de estructura de datos
    if isinstance(raw_data, dict):
        if "statistics" in raw_data and isinstance(raw_data["statistics"], list):
            raw_data = raw_data["statistics"]
        elif all(isinstance(v, dict) for v in raw_data.values()):
            raw_data = list(raw_data.values())
        else:
            raw_data = [raw_data]
    
    elif isinstance(raw_data, list):
        raw_data = [item for item in raw_data if isinstance(item, dict)]
        if not raw_data:
            print("[Leadpier] No hay datos válidos")
            return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
    
    else:
        print(f"[Leadpier] Formato de datos no soportado: {type(raw_data)}")
        return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
    
    try:
        df = pd.DataFrame(raw_data)
    except Exception as e:
        print(f"[Leadpier] Error creando DataFrame: {e}")
        return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
    
    # Mapear nombres de columnas de Leadpier a nuestro formato esperado
    column_mapping = {
        "source": "name",
        "revenue": "revenue",
        "EPL": "epl",
        "EPC": "epc"
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Asegurar columnas que usaremos
    for col in ("name", "revenue", "epl", "epc"):
        if col not in df.columns:
            df[col] = 0 if col != "name" else ""

    if "name" not in df.columns:
        print("[Leadpier] Columna 'name' no encontrada. Columnas disponibles:", list(df.columns))
        return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])

    df = df[["name", "revenue", "epl", "epc"]].rename(columns={"name": "adset_name"})
    df["adset_name_norm"] = df["adset_name"].astype(str).str.strip().str.lower()
    return df

# ================== META ==================
def fetch_account_adsets_paused(account_id):
    """Obtiene todos los adsets de una cuenta (activos y pausados)"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{account_id}/adsets"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "id,name,status",
        "limit": 200
    }
    rows = []
    while True:
        page = fb_get(url, params) or {}
        rows.extend(page.get("data", []))
        next_url = page.get("paging", {}).get("next")
        if not next_url:
            break
        url, params = next_url, {}
    
    # Filtrar solo adsets pausados
    paused_rows = [row for row in rows if row.get("status") == "PAUSED"]
    return paused_rows

def fetch_adsets_report(account_id, start_date, end_date):
    """Obtiene reporte completo de adsets para un rango de fechas usando Ads Reporting API"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{account_id}/insights"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "adset_id,adset_name,spend",
        "time_range": json.dumps({"since": start_date, "until": end_date}),
        "level": "adset",
        "limit": 1000
    }
    
    all_data = []
    while True:
        data = fb_get(url, params) or {}
        if not data.get("data"):
            break
        
        all_data.extend(data.get("data", []))
        
        # Verificar si hay más páginas
        paging = data.get("paging", {})
        next_url = paging.get("next")
        if not next_url:
            break
        
        # Actualizar URL y parámetros para la siguiente página
        url = next_url
        params = {}
    
    # Convertir a diccionario para búsqueda rápida
    spend_data = {}
    for item in all_data:
        adset_id = item.get("adset_id")
        spend = float(item.get("spend", 0) or 0)
        if adset_id:
            spend_data[adset_id] = spend
    
    return spend_data

def activate_adset(adset_id):
    """Activa un adset pausado"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{adset_id}"
    data = {"access_token": FB_ACCESS_TOKEN, "status": "ACTIVE"}
    return fb_post(url, data)

# ================== MAIN ==================
def prender_adsets_elegibles():
    """Función principal para prender adsets pausados que cumplan los criterios
    Solo se ejecuta entre las 7PM UTC-4 y las 7AM UTC-4"""
    print("\n=== PRENDER ADSETS PAUSADOS", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "UTC ===")
    
    # Verificar horario
    if not is_within_execution_window_utc_minus_4():
        utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
        print(f"[TIME] Hora actual: {utc_minus_4.strftime('%H:%M')} UTC-4")
        print("[ERROR] El script solo se ejecuta entre las 7PM UTC-4 y las 7AM UTC-4")
        return
    
    utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
    print(f"[OK] Hora actual: {utc_minus_4.strftime('%H:%M')} UTC-4 - Procediendo...")
    
    # Validar token de Leadpier antes de continuar
    token_valid = ensure_leadpier_token()
    
    if token_valid:
        # Recargar el token actualizado
        global LEADPIER_BEARER
        load_dotenv(dotenv_path="../enviorement.env", override=True)
        LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")
    else:
        print("[WARNING] Token de Leadpier invalido. Continuando sin datos de Leadpier...")
        print("[WARNING] Solo se usaran datos de Facebook para tomar decisiones.")
    
    # 1) Obtener datos de Leadpier para el rango de fechas
    print("Obteniendo datos de Leadpier para el rango de fechas...")
    lp_df = fetch_leadpier_sources_df()
    
    if lp_df.empty:
        print("[WARNING] Sin datos de Leadpier disponibles.")
        return
    else:
        print(f"[OK] Datos de Leadpier obtenidos: {len(lp_df)} registros")
        print(f"[DATE] Rango de fechas: {week_ago_utc_minus_4_str()} a {today_utc_minus_4_str()}")

    # 2) Obtener reportes de spend de todas las cuentas
    print("Obteniendo reportes de spend de Meta para todas las cuentas...")
    all_spend_data = {}
    
    for account in AD_ACCOUNTS:
        print(f"Obteniendo reporte de cuenta {account}...")
        spend_data = fetch_adsets_report(account, week_ago_utc_minus_4_str(), today_utc_minus_4_str())
        all_spend_data.update(spend_data)
        print(f"   [OK] {len(spend_data)} adsets con datos de spend obtenidos")
    
    print(f"[OK] Total de adsets con datos de spend: {len(all_spend_data)}")
    
    # 3) Recorrer cuentas/adsets pausados
    results = []
    adsets_to_activate = []
    
    for account in AD_ACCOUNTS:
        print(f"Revisando adsets pausados en cuenta {account}...")
        paused_adsets = fetch_account_adsets_paused(account)
        print(f"   [STATS] Adsets pausados encontrados: {len(paused_adsets)}")

        for adset in paused_adsets:
            adset_id = adset["id"]
            name = adset.get("name", "")
            status = adset.get("status", "")

            name_norm = name.strip().lower()
            row = lp_df[lp_df["adset_name_norm"] == name_norm]

            # Obtener revenue de Leadpier
            revenue = float(row["revenue"].iloc[0]) if not row.empty else 0.0
            
            # Obtener spend del diccionario (mucho más eficiente)
            spend = all_spend_data.get(adset_id, 0.0)
            roi = ((revenue - spend) / spend * 100.0) if spend > 0 else 0.0

            # Verificar criterios
            meets_spend_criteria = spend >= MIN_SPEND_THRESHOLD
            meets_roi_criteria = roi >= MIN_ROI_THRESHOLD
            is_eligible = meets_spend_criteria and meets_roi_criteria

            results.append({
                "account_id": account,
                "adset_id": adset_id,
                "name": name,
                "status": status,
                "spend": spend,
                "revenue": revenue,
                "roi": roi,
                "meets_spend_criteria": meets_spend_criteria,
                "meets_roi_criteria": meets_roi_criteria,
                "is_eligible": is_eligible,
                "activated": False,
                "activation_result": None
            })

            if is_eligible:
                adsets_to_activate.append({
                    "adset_id": adset_id,
                    "name": name,
                    "spend": spend,
                    "roi": roi,
                    "revenue": revenue
                })

    # 4) Activar adsets elegibles
    print(f"\n[TARGET] Adsets elegibles para activar: {len(adsets_to_activate)}")
    
    if not adsets_to_activate:
        print("[INFO] No hay adsets que cumplan los criterios para activar")
    else:
        for adset_info in adsets_to_activate:
            adset_id = adset_info["adset_id"]
            name = adset_info["name"]
            spend = adset_info["spend"]
            roi = adset_info["roi"]
            
            print(f"\n[ACTIVANDO] ACTIVANDO: {name[:50]}...")
            print(f"   [SPEND] Spend: ${spend:.2f} | [STATS] ROI: {roi:.2f}%")
            
            # Activar adset
            resp = activate_adset(adset_id)
            success = resp.get("success", False) if isinstance(resp, dict) else False
            
            # Actualizar resultado en results
            for result in results:
                if result["adset_id"] == adset_id:
                    result["activated"] = success
                    result["activation_result"] = resp
                    break
            
            if success:
                print(f"   [OK] Activado exitosamente")
            else:
                print(f"   [ERROR] Error al activar: {str(resp)[:100]}")

    # 5) Exportar reporte
    df = pd.DataFrame(results)
    out = "adsets_activation_report.csv"
    df.to_csv(out, index=False)
    
    activated_count = len([r for r in results if r["activated"]])
    eligible_count = len([r for r in results if r["is_eligible"]])
    
    print(f"\n[FILE] Reporte de activación: {out}")
    print(f"[ACTIVANDO] Adsets activados: {activated_count}/{eligible_count} elegibles")
    print(f"[STATS] Total adsets pausados revisados: {len(results)}")
    
    # Resumen de criterios
    print(f"\n[CRITERIA] Criterios aplicados:")
    print(f"   [SPEND] Spend mínimo: ${MIN_SPEND_THRESHOLD}")
    print(f"   [STATS] ROI mínimo: {MIN_ROI_THRESHOLD}%")
    print(f"   [DATE] Rango de fechas: {week_ago_utc_minus_4_str()} a {today_utc_minus_4_str()}")
    print(f"   [TIME] Horario de ejecución: 7PM UTC-4 a 7AM UTC-4")

# ================== EJECUCIÓN ==================
if __name__ == "__main__":
    prender_adsets_elegibles()
