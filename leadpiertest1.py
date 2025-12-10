import os
import time
import json
import datetime as dt
import requests
import pandas as pd
import schedule
import random
import atexit
from dotenv import load_dotenv
from leadpier_auth import ensure_leadpier_token
from leadpier_undetected_session import get_leadpier_session, process_leadpier_data

# ================== CONFIG ==================
load_dotenv(dotenv_path="enviorement.env")

GRAPH_API_VERSION = "v23.0"
FB_ACCESS_TOKEN   = os.getenv("FB_ACCESS_TOKEN")
LEADPIER_BEARER   = os.getenv("LEADPIER_BEARER")
PROXY_URL         = os.getenv("PROXY_URL")

# Cuentas a revisar
AD_ACCOUNTS = [
    "act_1172700037197465",
    "act_1192065285119034",
    "act_1191638479359701",
]

# Umbrales para lógica de apagado
SPEND_HIGH_THRESHOLD = 50.0    # USD - Si spend > 50 y ROI > 0: mantener prendido
SPEND_LOW_THRESHOLD  = 20.0    # USD - Si spend < 25: mantener prendido
ROI_OFF_THRESHOLD    = 0.0     # Si spend >= 25 y ROI <= 0: apagar

# Umbrales para lógica de escalado (cada hora)
SCALING_CONDITIONS = [
    {"spend_min": 40.0, "spend_max": 99.99, "roi_min": 100.0},  # Condición 0: 40 <= spend < 100 y ROI >= 100
    {"spend_min": 100.0, "roi_min": 70.0},   # Condición 1: spend >= 100 y ROI >= 70
    {"spend_min": 500.0, "roi_min": 50.0},   # Condición 2: spend >= 500 y ROI >= 50  
    {"spend_min": 1000.0, "roi_min": 30.0},  # Condición 3: spend >= 1000 y ROI >= 30
]
SCALING_MULTIPLIER = 1.25  # Multiplicador para aumentar presupuesto (50% más)

# ================== HELPERS ==================
def today_utc_minus_4_str():
    """Devuelve la fecha de hoy en UTC-4 (timezone de Facebook)"""
    utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
    return utc_minus_4.strftime("%Y-%m-%d")

def yesterday_utc_str():
    """DEPRECATED - usar today_utc_minus_4_str() en su lugar"""
    return (dt.datetime.utcnow() - dt.timedelta(days=1)).strftime("%Y-%m-%d")

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
    """GET con manejo de rate limiting (error code 17)"""
    proxies = get_proxies()
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout, proxies=proxies)
            if r.status_code == 200:
                return r.json()
            
            # Manejar rate limiting específicamente
            if r.status_code == 400:
                try:
                    error_data = r.json()
                    error_info = error_data.get("error", {})
                    if error_info.get("code") == 17:  # Rate limit error
                        wait_time = (2 ** i) * 60  # Backoff exponencial: 60s, 120s, 240s
                        print(f"[RATE LIMIT] Límite de API alcanzado. Esperando {wait_time}s...")
                        time.sleep(wait_time)
                        continue  # Reintentar después del backoff
                except:
                    pass
            
            print(f"[FB GET] {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[FB GET] intento {i+1} error: {e}")
        
        # Backoff exponencial estándar para otros errores
        time.sleep(2 ** i)
    return {}

def fb_post(url, data, retries=3, timeout=30):
    """POST con manejo de rate limiting (error code 17)"""
    proxies = get_proxies()
    for i in range(retries):
        try:
            r = requests.post(url, data=data, timeout=timeout, proxies=proxies)
            if r.status_code in (200, 201):
                return r.json()
            
            # Manejar rate limiting específicamente
            if r.status_code == 400:
                try:
                    error_data = r.json()
                    error_info = error_data.get("error", {})
                    if error_info.get("code") == 17:  # Rate limit error
                        wait_time = (2 ** i) * 60  # Backoff exponencial: 60s, 120s, 240s
                        print(f"[RATE LIMIT] Límite de API alcanzado. Esperando {wait_time}s...")
                        time.sleep(wait_time)
                        continue  # Reintentar después del backoff
                except:
                    pass
            
            print(f"[FB POST] {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[FB POST] intento {i+1} error: {e}")
        
        # Backoff exponencial estándar para otros errores
        time.sleep(2 ** i)
    return {}

# ================== LEADPIER ==================
LP_BASE = "https://webapi.leadpier.com"

def fetch_leadpier_sources_df_fallback():
    """
    Método alternativo usando GET como en leadpierget.py
    """
    try:
        url = "https://dash.leadpier.com/marketer-statistics/sources"
        params = {
            "limit": 200,
            "offset": 0,
            "orderDirection": "DESC",
            "groupBy": "HOUR",
            "orderBy": "visitors",
            "periodFrom": "today",
            "periodTo": "today",
            "source": "BM5_1"
        }
        
        # IMPORTANTE: NO usar proxy para Leadpier - lo bloquea con 401
        r = leadpier_request_with_retry('GET', url, params=params, headers=leadpier_headers(), max_retries=3, initial_timeout=30)
        
        if r is None:
            print("[Leadpier Fallback] ERROR: No se pudo conectar a Leadpier después de varios reintentos")
            return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
        
        if r.status_code != 200:
            print(f"[Leadpier Fallback] Status: {r.status_code}, {r.text[:200]}")
            return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
        
        data = r.json()
        
        if not isinstance(data, dict) or "data" not in data:
            print(f"[Leadpier Fallback] Respuesta sin 'data': {str(data)[:200]}")
            return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
        
        if not data["data"]:
            print("[Leadpier Fallback] data['data'] está vacío")
            return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
        
        df = pd.DataFrame(data["data"])
        
        # Asegurar columnas
        for col in ("name", "revenue", "epl", "epc"):
            if col not in df.columns:
                df[col] = 0 if col != "name" else ""
        
        if "name" not in df.columns:
            print("[Leadpier Fallback] Columna 'name' no encontrada:", list(df.columns))
            return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
        
        df = df[["name", "revenue", "epl", "epc"]].rename(columns={"name": "adset_name"})
        df["adset_name_norm"] = df["adset_name"].astype(str).str.strip().str.lower()
        return df
        
    except Exception as e:
        print(f"[Leadpier Fallback] Error: {e}")
        return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])

def fetch_leadpier_sources_df():
    """
    Obtiene datos de LeadPier usando sistema undetected con caché
    - Primero intenta caché (si válida)
    - Luego usa sesión undetected persistente
    - Fallback a navegador estándar si falla
    """
    # Obtener sesión global (singleton con caché)
    session = get_leadpier_session(headless=True)
    
    # Intentar obtener datos (usa caché automáticamente si válida)
    print("[Leadpier] Obteniendo datos (con caché si disponible)...")
    data = session.get_data()
    
    if data:
        # Procesar y retornar datos
        df = process_leadpier_data(data)
        if not df.empty:
            print(f"[OK] Datos de Leadpier obtenidos: {len(df)} registros")
            return df
    
    # Si falla el método undetected, intentar fallback con token directo
    print("[Leadpier] Método undetected falló, intentando con token directo...")
    
    payload = {
        "limit": 200,
        "offset": 0,
        "orderDirection": "DESC",
        "groupBy": "HOUR",
        "orderBy": "visitors",
        "periodFrom": "today",
        "periodTo": "today",
        "source": "BM5_1",
    }

    url = f"{LP_BASE}/v1/api/stats/user/sources"
    r = leadpier_request_with_retry('POST', url, headers=leadpier_headers(), data=json.dumps(payload), max_retries=3, initial_timeout=30)

    if r is None or r.status_code != 200:
        print("[Leadpier] ERROR: Todos los métodos fallaron")
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

    # Procesar datos de Leadpier
    raw_data = data["data"]
    
    # Si está vacío, devolver DataFrame vacío
    if not raw_data:
        print("[Leadpier] Sin datos disponibles")
        return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])
    
    # Manejar diferentes tipos de estructura de datos
    if isinstance(raw_data, dict):
        # Buscar la lista de estadísticas real
        if "statistics" in raw_data and isinstance(raw_data["statistics"], list):
            raw_data = raw_data["statistics"]
        # Si las claves son índices y los valores son los registros
        elif all(isinstance(v, dict) for v in raw_data.values()):
            raw_data = list(raw_data.values())
        # Si es un solo registro, lo convertimos a lista
        else:
            raw_data = [raw_data]
    
    elif isinstance(raw_data, list):
        # Filtrar solo los elementos que sean diccionarios válidos
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
        "source": "name",     # source -> name (que luego se convierte en adset_name)
        "revenue": "revenue", # ya está correcto
        "EPL": "epl",        # EPL -> epl
        "EPC": "epc"         # EPC -> epc (si existe)
    }
    
    # Renombrar columnas según el mapeo
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Asegurar columnas que usaremos; si faltan, las creamos con 0/None
    for col in ("name", "revenue", "epl", "epc"):
        if col not in df.columns:
            df[col] = 0 if col != "name" else ""

    # Verificar que tenemos las columnas necesarias
    if "name" not in df.columns:
        print("[Leadpier] Columna 'name' no encontrada. Columnas disponibles:", list(df.columns))
        return pd.DataFrame(columns=["adset_name", "revenue", "epl", "epc", "adset_name_norm"])

    # Seleccionar solo las columnas que necesitamos
    df = df[["name", "revenue", "epl", "epc"]].rename(columns={"name": "adset_name"})
    # Normalización para match exacto simple
    df["adset_name_norm"] = df["adset_name"].astype(str).str.strip().str.lower()
    return df

# ================== META ==================
def fetch_account_adsets(account_id):
    """Obtiene todos los adsets activos con sus budgets incluidos para evitar llamadas individuales"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{account_id}/adsets"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "id,name,status,daily_budget,lifetime_budget",
        "limit": 200
    }
    rows = []
    while True:
        page = fb_get(url, params) or {}
        rows.extend(page.get("data", []))
        next_url = page.get("paging", {}).get("next")
        if not next_url:
            break
        url, params = next_url, {}  # 'next' ya trae la query completa
        time.sleep(0.5)  # Throttling entre páginas para evitar rate limiting
    
    # Filtrar solo adsets activos
    active_rows = [row for row in rows if row.get("status") == "ACTIVE"]
    return active_rows

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
        time.sleep(0.5)  # Throttling entre páginas para evitar rate limiting
    
    # Convertir a diccionario para búsqueda rápida
    spend_data = {}
    for item in all_data:
        adset_id = item.get("adset_id")
        spend = float(item.get("spend", 0) or 0)
        if adset_id:
            spend_data[adset_id] = spend
    
    return spend_data

def fetch_adset_spend_today(adset_id):
    """Obtiene el spend del adset para HOY en UTC-4"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{adset_id}/insights"
    t = today_utc_minus_4_str()  # Usar fecha de hoy en UTC-4
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "spend",
        "time_range": json.dumps({"since": t, "until": t}),
        "limit": 1
    }
    data = fb_get(url, params) or {}
    
    # Si no hay datos, devolver 0.0 (normal para adsets sin actividad)
    if not data.get("data"):
        print(f"[DEBUG] Sin datos de spend para adset {adset_id} en fecha {t}")
        return 0.0
    
    try:
        spend_value = float(data.get("data", [{}])[0].get("spend", 0) or 0)
        if spend_value > 0:
            print(f"[INFO] Adset {adset_id}: spend ${spend_value:.2f}")
        return spend_value
    except Exception as e:
        print(f"[ERROR] Error procesando spend para adset {adset_id}: {e}")
        return 0.0

def determine_adset_action(spend, roi, adset_name):
    """
    Determina qué acción tomar con un adset según las reglas de negocio:
    1. Si spend > 50 y ROI > 0: mantener prendido
    2. Si spend < 25: mantener prendido  
    3. Si spend >= 25 y ROI <= 0: apagar
    
    Returns:
        tuple: (action, reason)
        action: "KEEP" o "PAUSE"
        reason: explicación de la decisión
    """
    # Regla 2: Si spend < 25, mantener prendido
    if spend < SPEND_LOW_THRESHOLD:
        return "KEEP", f"Regla 2: Spend ${spend:.2f} < ${SPEND_LOW_THRESHOLD}"
    
    # Regla 3: Si spend >= 25 Y ROI <= 0, apagar
    elif spend >= SPEND_LOW_THRESHOLD and roi <= ROI_OFF_THRESHOLD:
        return "PAUSE", f"Regla 3: Spend ${spend:.2f} >= ${SPEND_LOW_THRESHOLD} y ROI {roi:.2f}% <= 0"
    
    # Regla 1: Si spend >= 25 Y ROI > 0, mantener prendido (cualquier spend >= 25 con ROI positivo)
    else:
        return "KEEP", f"Regla 1: Spend ${spend:.2f} >= ${SPEND_LOW_THRESHOLD} y ROI {roi:.2f}% > 0"

def determine_scaling_action(spend, roi, adset_name):
    """
    Determina si un adset debe escalarse según las condiciones:
    0. 40 <= spend < 100 y ROI >= 100 (nueva condición para alto ROI)
    1. spend >= 100 y ROI >= 70
    2. spend >= 500 y ROI >= 50  
    3. spend >= 1000 y ROI >= 30
    
    Returns:
        tuple: (should_scale, condition_met, reason)
        should_scale: True si debe escalarse
        condition_met: número de condición cumplida (0, 1, 2, 3) o None
        reason: explicación de la decisión
    """
    for i, condition in enumerate(SCALING_CONDITIONS):
        spend_min = condition["spend_min"]
        spend_max = condition.get("spend_max", float('inf'))  # Si no tiene spend_max, usar infinito
        roi_min = condition["roi_min"]
        
        # Verificar si cumple todas las condiciones
        if spend >= spend_min and spend <= spend_max and roi >= roi_min:
            if spend_max == float('inf'):
                reason = f"Condición {i}: Spend ${spend:.2f} >= ${spend_min} y ROI {roi:.2f}% >= {roi_min}%"
            else:
                reason = f"Condición {i}: ${spend_min} <= Spend ${spend:.2f} < ${spend_max + 0.01} y ROI {roi:.2f}% >= {roi_min}%"
            return True, i, reason
    
    # No cumple ninguna condición de escalado
    return False, None, f"No cumple condiciones de escalado (spend: ${spend:.2f}, ROI: {roi:.2f}%)"

def get_adset_budget_from_data(adset_data):
    """Extrae el presupuesto del adset desde los datos ya obtenidos (evita llamadas adicionales)"""
    # Facebook devuelve presupuestos en centavos, convertir a dólares
    daily_budget = float(adset_data.get("daily_budget", 0)) / 100 if adset_data.get("daily_budget") else None
    lifetime_budget = float(adset_data.get("lifetime_budget", 0)) / 100 if adset_data.get("lifetime_budget") else None
    
    return {
        "daily_budget": daily_budget,
        "lifetime_budget": lifetime_budget,
        "budget_type": "daily" if daily_budget else "lifetime" if lifetime_budget else "unknown"
    }

def get_adset_budget(adset_id):
    """Obtiene el presupuesto diario actual del adset (solo usar si no se tiene en fetch_account_adsets)"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{adset_id}"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "daily_budget,lifetime_budget,budget_remaining"
    }
    data = fb_get(url, params) or {}
    
    # Facebook devuelve presupuestos en centavos, convertir a dólares
    daily_budget = float(data.get("daily_budget", 0)) / 100 if data.get("daily_budget") else None
    lifetime_budget = float(data.get("lifetime_budget", 0)) / 100 if data.get("lifetime_budget") else None
    
    return {
        "daily_budget": daily_budget,
        "lifetime_budget": lifetime_budget,
        "budget_type": "daily" if daily_budget else "lifetime" if lifetime_budget else "unknown"
    }

def round_budget_intelligently(budget):
    """
    Redondea el presupuesto de manera inteligente:
    - Si budget <= 100,000: redondeo HACIA ABAJO sobre los miles
    - Si budget > 100,000: redondeo HACIA ABAJO sobre las decenas de miles
    
    Ejemplos:
    - 25000 * 1.25 = 31250 → 31000 (hacia abajo en miles)
    - 230000 * 1.25 = 287500 → 280000 (hacia abajo en decenas de miles)
    """
    if budget <= 0:
        return budget
    
    if budget <= 100000:
        # Redondeo hacia abajo sobre los miles
        return int(budget / 1000) * 1000
    else:
        # Redondeo hacia abajo sobre las decenas de miles
        return int(budget / 10000) * 10000

def scale_adset_budget(adset_id, current_budget, budget_type):
    """Escala el presupuesto del adset multiplicándolo por SCALING_MULTIPLIER con redondeo inteligente"""
    if not current_budget or current_budget <= 0:
        return {"success": False, "error": "Presupuesto actual inválido"}
    
    # Calcular nuevo presupuesto y redondearlo
    raw_new_budget = current_budget * SCALING_MULTIPLIER
    new_budget = round_budget_intelligently(raw_new_budget)
    new_budget_cents = int(new_budget * 100)  # Convertir a centavos para Facebook
    
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{adset_id}"
    data = {"access_token": FB_ACCESS_TOKEN}
    
    if budget_type == "daily":
        data["daily_budget"] = new_budget_cents
    elif budget_type == "lifetime":
        data["lifetime_budget"] = new_budget_cents
    else:
        return {"success": False, "error": "Tipo de presupuesto desconocido"}
    
    response = fb_post(url, data)
    
    if response and not response.get("error"):
        return {
            "success": True,
            "old_budget": current_budget,
            "new_budget": new_budget,
            "raw_new_budget": raw_new_budget,  # Presupuesto sin redondear para referencia
            "budget_type": budget_type,
            "multiplier": SCALING_MULTIPLIER
        }
    else:
        return {
            "success": False,
            "error": response.get("error", "Error desconocido"),
            "response": response
        }

def pause_adset(adset_id):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{adset_id}"
    data = {"access_token": FB_ACCESS_TOKEN, "status": "PAUSED"}
    return fb_post(url, data)

# ================== ESCALAMIENTO ==================
def escalamiento():
    """
    Función de escalado que se ejecuta cada hora.
    Revisa todos los adsets activos y escala aquellos que cumplan las condiciones.
    """
    print("\n=== ESCALAMIENTO", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "UTC ===")
    
    # Validar token de Leadpier antes de continuar
    token_valid = ensure_leadpier_token()
    
    if token_valid:
        # Recargar el token actualizado
        global LEADPIER_BEARER
        load_dotenv(dotenv_path="enviorement.env", override=True)
        LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")
    else:
        print("[WARNING] Token de Leadpier invalido. Continuando sin datos de Leadpier...")
        print("[WARNING] Solo se usaran datos de Facebook para tomar decisiones.")
    
    # 1) Obtener datos de Leadpier
    print("Obteniendo datos de Leadpier para escalamiento...")
    lp_df = fetch_leadpier_sources_df()
    
    # Si falla, intentar método fallback
    if lp_df.empty:
        print("Método POST falló, intentando método fallback (GET)...")
        lp_df = fetch_leadpier_sources_df_fallback()
    
    if lp_df.empty:
        print("[WARNING] Sin datos de Leadpier para escalamiento.")
        return
    else:
        print(f"[OK] Datos de Leadpier obtenidos: {len(lp_df)} registros")

    # 2) Obtener datos de spend para todas las cuentas de una vez
    print("Obteniendo datos de spend para escalamiento...")
    all_spend_data = {}
    today = today_utc_minus_4_str()
    
    for account in AD_ACCOUNTS:
        print(f"Obteniendo reporte de spend para cuenta {account}...")
        spend_data = fetch_adsets_report(account, today, today)
        all_spend_data.update(spend_data)
        time.sleep(1)  # Throttling entre cuentas para evitar rate limiting
    
    print(f"[OK] Datos de spend obtenidos para {len(all_spend_data)} adsets")

    # 3) Recorrer cuentas/adsets para escalamiento
    scaling_results = []
    
    for account in AD_ACCOUNTS:
        print(f"Revisando escalamiento en cuenta {account}...")
        adsets = fetch_account_adsets(account)
        time.sleep(1)  # Throttling entre cuentas para evitar rate limiting

        for a in adsets:
            adset_id = a["id"]
            name     = a.get("name", "")
            status   = a.get("status", "")

            # Solo procesar adsets activos
            if status != "ACTIVE":
                continue

            name_norm = name.strip().lower()
            row = lp_df[lp_df["adset_name_norm"] == name_norm]

            revenue = float(row["revenue"].iloc[0]) if not row.empty else 0.0
            
            # Obtener spend del diccionario optimizado
            spend = all_spend_data.get(adset_id, 0.0)
            if spend > 0:
                print(f"[INFO] Adset {adset_id}: spend ${spend:.2f}")
            else:
                print(f"[DEBUG] Sin datos de spend para adset {adset_id} en fecha {today}")
            
            roi     = ((revenue - spend) / spend * 100.0) if spend > 0 else 0.0

            # Determinar si debe escalarse
            should_scale, condition_met, reason = determine_scaling_action(spend, roi, name)
            
            scaling_results.append({
                "account_id": account,
                "adset_id": adset_id,
                "name": name,
                "spend": spend,
                "revenue": revenue,
                "roi": roi,
                "should_scale": should_scale,
                "condition_met": condition_met,
                "reason": reason,
                "scaled": False,
                "scaling_result": None
            })

            if should_scale:
                # Obtener presupuesto actual desde los datos ya obtenidos (evita llamada adicional)
                budget_info = get_adset_budget_from_data(a)
                current_budget = budget_info["daily_budget"] or budget_info["lifetime_budget"]
                budget_type = budget_info["budget_type"]
                
                # Si no se obtuvo el budget en fetch_account_adsets, hacer llamada individual como fallback
                if budget_type == "unknown":
                    print(f"[WARNING] Budget no disponible en datos iniciales, haciendo llamada individual para {adset_id}...")
                    budget_info = get_adset_budget(adset_id)
                    current_budget = budget_info["daily_budget"] or budget_info["lifetime_budget"]
                    budget_type = budget_info["budget_type"]
                    time.sleep(0.3)  # Throttling después de llamada individual
                
                if current_budget and budget_type != "unknown":
                    # Escalar presupuesto
                    scaling_result = scale_adset_budget(adset_id, current_budget, budget_type)
                    scaling_results[-1]["scaled"] = scaling_result["success"]
                    scaling_results[-1]["scaling_result"] = scaling_result
                    
                    if scaling_result["success"]:
                        raw_budget = scaling_result.get('raw_new_budget', scaling_result['new_budget'])
                        print(f"[ESCALADO] ESCALADO: {name[:50]}...")
                        print(f"   [SPEND] Spend: ${spend:.2f} | [STATS] ROI: {roi:.2f}%")
                        print(f"   [REASON] Razón: {reason}")
                        print(f"   💵 Presupuesto: ${scaling_result['old_budget']:.2f} → ${scaling_result['new_budget']:.2f}")
                        print(f"   🔢 Cálculo: ${scaling_result['old_budget']:.2f} × {scaling_result['multiplier']} = ${raw_budget:.2f} → ${scaling_result['new_budget']:.2f} (redondeado)")
                        print()
                        time.sleep(0.3)  # Throttling después de escalar para evitar rate limiting
                    else:
                        print(f"[ERROR] ERROR ESCALANDO: {name[:50]}...")
                        print(f"   [SPEND] Spend: ${spend:.2f} | [STATS] ROI: {roi:.2f}%")
                        print(f"   [REASON] Razón: {reason}")
                        print(f"   [ERROR] Error: {scaling_result.get('error', 'Error desconocido')}")
                        print()
                else:
                    scaling_results[-1]["scaling_result"] = {"success": False, "error": "No se pudo obtener presupuesto"}
                    print(f"[ERROR] ERROR: No se pudo obtener presupuesto para {name[:50]}...")
                    print()

    # 3) Export de resultados de escalamiento
    df = pd.DataFrame(scaling_results)
    out = "scaling_report.csv"
    df.to_csv(out, index=False)
    
    scaled_count = len([r for r in scaling_results if r["scaled"]])
    eligible_count = len([r for r in scaling_results if r["should_scale"]])
    
    print(f"[FILE] Reporte de escalamiento: {out}")
    print(f"[ESCALADO] Adsets escalados: {scaled_count}/{eligible_count} elegibles")
    print(f"[STATS] Total adsets revisados: {len(scaling_results)}")

# ================== MAIN ==================
def revisar_y_actualizar():
    print("\n=== RUN", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "UTC ===")

    # Validar token de Leadpier antes de continuar
    token_valid = ensure_leadpier_token()
    
    if token_valid:
        # Recargar el token actualizado
        global LEADPIER_BEARER
        load_dotenv(dotenv_path="enviorement.env", override=True)
        LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")
    else:
        print("[WARNING] Token de Leadpier invalido. Continuando sin datos de Leadpier...")
        print("[WARNING] Solo se usaran datos de Facebook para tomar decisiones.")

    # 1) Leadpier - Intentar método principal primero
    print("Intentando obtener datos de Leadpier (método POST)...")
    lp_df = fetch_leadpier_sources_df()
    
    # Si falla, intentar método fallback
    if lp_df.empty:
        print("Método POST falló, intentando método fallback (GET)...")
        lp_df = fetch_leadpier_sources_df_fallback()
    
    if lp_df.empty:
        print("[WARNING] Ambos métodos de Leadpier fallaron; no se toman acciones.")
        return
    else:
        print(f"[OK] Datos de Leadpier obtenidos: {len(lp_df)} registros")

    # 2) Obtener datos de spend para todas las cuentas de una vez
    print("Obteniendo datos de spend para todas las cuentas...")
    all_spend_data = {}
    today = today_utc_minus_4_str()
    
    for account in AD_ACCOUNTS:
        print(f"Obteniendo reporte de spend para cuenta {account}...")
        spend_data = fetch_adsets_report(account, today, today)
        all_spend_data.update(spend_data)
        time.sleep(1)  # Throttling entre cuentas para evitar rate limiting
    
    print(f"[OK] Datos de spend obtenidos para {len(all_spend_data)} adsets")

    # 3) Recorremos cuentas/adsets
    results = []
    for account in AD_ACCOUNTS:
        print(f"Cuenta {account}: adsets activos…")
        adsets = fetch_account_adsets(account)
        time.sleep(1)  # Throttling entre cuentas para evitar rate limiting

        for a in adsets:
            adset_id = a["id"]
            name     = a.get("name", "")
            status   = a.get("status", "")

            name_norm = name.strip().lower()
            row = lp_df[lp_df["adset_name_norm"] == name_norm]

            revenue = float(row["revenue"].iloc[0]) if not row.empty else 0.0
            epl     = row["epl"].iloc[0] if ("epl" in lp_df.columns and not row.empty) else None
            epc     = row["epc"].iloc[0] if ("epc" in lp_df.columns and not row.empty) else None

            # Obtener spend del diccionario optimizado
            spend = all_spend_data.get(adset_id, 0.0)
            if spend > 0:
                print(f"[INFO] Adset {adset_id}: spend ${spend:.2f}")
            else:
                print(f"[DEBUG] Sin datos de spend para adset {adset_id} en fecha {today}")
            
            roi     = ((revenue - spend) / spend * 100.0) if spend > 0 else 0.0

            # Determinar acción según las reglas de negocio
            action, reason = determine_adset_action(spend, roi, name)
            
            results.append({
                "account_id": account,
                "adset_id": adset_id,
                "name": name,
                "status": status,
                "spend": spend,
                "revenue": revenue,
                "roi": roi,
                "epl": epl,
                "epc": epc,
                "action": action,
                "reason": reason,
            })

            # Aplicar acción si es necesario
            if action == "PAUSE" and status == "ACTIVE":
                resp = pause_adset(adset_id)
                success = resp.get("success", False) if isinstance(resp, dict) else False
                print(f"[PAUSADO] PAUSADO: {name[:50]}...")
                print(f"   [SPEND] Spend: ${spend:.2f} | [STATS] ROI: {roi:.2f}%")
                print(f"   [REASON] Razón: {reason}")
                print(f"   [OK] Resultado: {'Éxito' if success else 'Error'}")
                if not success:
                    print(f"   [ERROR] Respuesta FB: {str(resp)[:100]}")
                print()
                time.sleep(0.3)  # Throttling después de pausar para evitar rate limiting
            
            elif action == "KEEP":
                print(f"[OK] MANTENER: {name[:50]}...")
                print(f"   [SPEND] Spend: ${spend:.2f} | [STATS] ROI: {roi:.2f}%")
                print(f"   [REASON] Razón: {reason}")
                print()

    # 4) Export
    df = pd.DataFrame(results)
    out = "adsets_report.csv"
    df.to_csv(out, index=False)
    print(f"[FILE] Exportado: {out}  ({len(df)} filas)")

# ================== FUNCIONES CON JITTER ==================
def revisar_con_jitter():
    """Wrapper de revisar_y_actualizar con delay aleatorio"""
    jitter = random.randint(0, 60)  # 0-60 segundos de jitter
    if jitter > 0:
        print(f"[JITTER] Esperando {jitter}s antes de ejecutar...")
        time.sleep(jitter)
    revisar_y_actualizar()

def escalamiento_con_jitter():
    """Wrapper de escalamiento con delay aleatorio"""
    jitter = random.randint(0, 120)  # 0-120 segundos de jitter para escalamiento
    if jitter > 0:
        print(f"[JITTER] Esperando {jitter}s antes de escalar...")
        time.sleep(jitter)
    escalamiento()

def keep_alive_leadpier():
    """Mantiene la sesión de LeadPier activa"""
    try:
        session = get_leadpier_session(headless=True)
        session.keep_alive()
    except Exception as e:
        print(f"[KEEP-ALIVE] Error: {e}")

def cleanup_on_exit():
    """Limpieza al salir del script"""
    print("\n[CLEANUP] Cerrando sesiones...")
    try:
        session = get_leadpier_session(headless=True)
        session.close()
        print("[CLEANUP] Sesiones cerradas correctamente")
    except:
        pass

# ================== SCHEDULER ==================
if __name__ == "__main__":
    # Registrar cleanup al salir
    atexit.register(cleanup_on_exit)
    
    # Primera corrida ahora
    revisar_y_actualizar()
    
    # Primera corrida de escalamiento
    escalamiento()

    # Schedulers con jitter para parecer más humano
    schedule.every(10).minutes.do(revisar_con_jitter)  # Cada 10 minutos: apagado (con jitter)
    schedule.every(1).hours.do(escalamiento_con_jitter)  # Cada 1 hora: escalamiento (con jitter)
    schedule.every(2).minutes.do(keep_alive_leadpier)  # Cada 2 minutos: mantener sesión activa
    
    # Mostrar horario actual y límite
    utc_minus_4_now = dt.datetime.utcnow() - dt.timedelta(hours=4)
    print(f"[TIME] Hora actual: {utc_minus_4_now.strftime('%H:%M')} UTC-4")
    print("[INFO] Schedulers activos:")
    print("   [STATS] Revisión y apagado: cada 10 minutos (+jitter 0-60s)")
    print("   [ESCALADO] Escalamiento: cada 1 hora (+jitter 0-120s)")
    print("   [KEEP-ALIVE] Mantener sesión: cada 2 minutos")
    print("   [STOP] Límite: Se detendrá a las 18:00 (6 PM) UTC-4")
    
    try:
        while True:
            # Verificar si es después de las 6 PM UTC-4
            utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
            current_hour = utc_minus_4.hour
            
            if current_hour >= 18:  # 18:00 = 6 PM
                print(f"\n[STOP] FINALIZANDO: Son las {utc_minus_4.strftime('%H:%M')} UTC-4 (después de las 6 PM)")
                print("   El script se detendrá hasta mañana.")
                break
                
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] Interrumpido por el usuario")
    finally:
        cleanup_on_exit()
