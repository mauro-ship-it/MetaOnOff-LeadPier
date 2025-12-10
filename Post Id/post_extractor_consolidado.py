import os
import sys
import time
import json
import datetime as dt
import requests
import pandas as pd
from dotenv import load_dotenv

# Agregar el path del directorio para importar leadpier_auth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Mainteinance and Scaling'))
from leadpier_auth import ensure_leadpier_token

# ================== CONFIG ==================
load_dotenv(dotenv_path="../Mainteinance and Scaling/enviorement.env")

GRAPH_API_VERSION = "v23.0"
FB_ACCESS_TOKEN   = os.getenv("FB_ACCESS_TOKEN")
LEADPIER_BEARER   = os.getenv("LEADPIER_BEARER")
PROXY_URL         = os.getenv("PROXY_URL")

# Cuentas a revisar
AD_ACCOUNTS = [
    "act_653164011031498",
    "act_1172700037197465",
    "act_1192065285119034",
]

# Thresholds
ROI_POSITIVE_THRESHOLD = 0.0  # ROI >= 0
MIN_SPEND_THRESHOLD = 20.0    # Spend >= 20

# ================== HELPERS ==================
def today_utc_minus_4_str():
    """Devuelve la fecha de hoy en UTC-4 (timezone de Facebook)"""
    utc_minus_4 = dt.datetime.utcnow() - dt.timedelta(hours=4)
    return utc_minus_4.strftime("%Y-%m-%d")

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

# ================== LEADPIER ==================
LP_BASE = "https://webapi.leadpier.com"

def fetch_leadpier_sources_df():
    """Obtiene datos de Leadpier para calcular ROI"""
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
        return pd.DataFrame(columns=["adset_name", "revenue", "adset_name_norm"])
    
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
            return pd.DataFrame(columns=["adset_name", "revenue", "adset_name_norm"])
    
    try:
        df = pd.DataFrame(raw_data)
    except Exception as e:
        print(f"[Leadpier] Error creando DataFrame: {e}")
        return pd.DataFrame(columns=["adset_name", "revenue", "adset_name_norm"])
    
    # Mapear nombres de columnas
    column_mapping = {
        "source": "name",
        "revenue": "revenue",
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Asegurar columnas necesarias
    for col in ("name", "revenue"):
        if col not in df.columns:
            df[col] = 0 if col != "name" else ""

    if "name" not in df.columns:
        print("[Leadpier] Columna 'name' no encontrada. Columnas disponibles:", list(df.columns))
        return pd.DataFrame(columns=["adset_name", "revenue", "adset_name_norm"])

    df = df[["name", "revenue"]].rename(columns={"name": "adset_name"})
    df["adset_name_norm"] = df["adset_name"].astype(str).str.strip().str.lower()
    return df

# ================== META ==================
def fetch_account_adsets(account_id):
    """Obtiene todos los adsets activos de una cuenta"""
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
    t = today_utc_minus_4_str()
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "spend",
        "time_range": json.dumps({"since": t, "until": t}),
        "limit": 1
    }
    data = fb_get(url, params) or {}
    
    if not data.get("data"):
        return 0.0
    
    try:
        spend_value = float(data.get("data", [{}])[0].get("spend", 0) or 0)
        return spend_value
    except Exception as e:
        print(f"[ERROR] Error procesando spend para adset {adset_id}: {e}")
        return 0.0

def fetch_adset_ads_with_posts(adset_id):
    """Obtiene los ads de un adset y extrae los post_ids"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{adset_id}/ads"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "id,name,status,creative",
        "limit": 100
    }
    
    ads_data = fb_get(url, params) or {}
    ads_list = ads_data.get("data", [])
    
    post_ids = []
    
    for ad in ads_list:
        if ad.get("status") == "ACTIVE":
            creative = ad.get("creative", {})
            
            # Obtener detalles del creative
            if creative.get("id"):
                creative_details = fetch_creative_details(creative["id"])
                post_id = extract_post_id_from_creative(creative_details)
                
                if post_id:
                    post_ids.append({
                        "ad_id": ad["id"],
                        "ad_name": ad.get("name", ""),
                        "post_id": post_id
                    })
    
    return post_ids

def fetch_creative_details(creative_id):
    """Obtiene solo el effective_object_story_id de un creative de Facebook"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{creative_id}"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "effective_object_story_id"
    }
    
    return fb_get(url, params) or {}

def extract_post_id_from_creative(creative_details):
    """Extrae el post_id del effective_object_story_id"""
    post_id = creative_details.get("effective_object_story_id")
    
    if post_id:
        print(f"[DEBUG] Post ID encontrado: {post_id} (fuente: effective_object_story_id)")
    else:
        print(f"[DEBUG] No se encontró effective_object_story_id")
    
    return post_id

def extract_page_id_from_post_id(post_id):
    """Extrae el page_id del post_id (formato: page_id_post_id)"""
    if post_id and "_" in post_id:
        return post_id.split("_")[0]
    return None

# ================== SCORING SYSTEM ==================
def calculate_spend_punctuation(spend):
    """Calcula puntuación basada en spend: 20-100: 1, 100-1000: 2, 1000-5000: 3, 5000+: 4"""
    if 20 <= spend < 100:
        return 1
    elif 100 <= spend < 1000:
        return 2
    elif 1000 <= spend < 5000:
        return 3
    elif spend >= 5000:
        return 4
    else:
        return 0

def calculate_roi_punctuation(roi):
    """Calcula puntuación basada en ROI: 0-10%: 0.1, 10-20%: 0.2, etc."""
    if roi < 0:
        return 0.0
    elif roi >= 100:
        return 1.0 + ((roi - 100) // 10) * 0.1
    else:
        return (roi // 10 + 1) * 0.1

def calculate_profit_punctuation(profit):
    """Calcula puntuación basada en profit: 0-50: 0.1, 50-100: 0.2, etc."""
    if profit < 50:
        return 0.1
    elif profit < 100:
        return 0.2
    elif profit < 200:
        return 0.4
    elif profit < 500:
        return 0.6
    elif profit < 1000:
        return 0.8
    else:
        return 1.0

def calculate_profit_multiplier(profit):
    """Calcula multiplicador de bonus basado en profit"""
    if profit >= 1000:
        return 1.5
    elif profit >= 500:
        return 1.3
    elif profit >= 200:
        return 1.1
    else:
        return 1.0

# ================== MAIN FUNCTION ==================
def extract_positive_roi_posts():
    """Función principal que extrae posts de adsets con ROI >= 0 y spend >= 20"""
    print("\n=== EXTRACTOR DE POST IDs", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "UTC ===")
    
    # Validar token de Leadpier antes de continuar
    if not ensure_leadpier_token():
        print("[ERROR] No se pudo validar/renovar el token de Leadpier. Deteniendo ejecucion.")
        return []
    
    # Recargar el token actualizado
    global LEADPIER_BEARER
    load_dotenv(dotenv_path="../Mainteinance and Scaling/enviorement.env", override=True)
    LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")
    
    # 1) Obtener datos de Leadpier
    print("Obteniendo datos de Leadpier...")
    lp_df = fetch_leadpier_sources_df()
    
    if lp_df.empty:
        print("⚠️ Sin datos de Leadpier.")
        return []
    else:
        print(f"✅ Datos de Leadpier obtenidos: {len(lp_df)} registros")

    # 2) Obtener datos de spend para todas las cuentas de una vez
    print("Obteniendo datos de spend para todas las cuentas...")
    all_spend_data = {}
    today = today_utc_minus_4_str()
    
    for account in AD_ACCOUNTS:
        print(f"Obteniendo reporte de spend para cuenta {account}...")
        spend_data = fetch_adsets_report(account, today, today)
        all_spend_data.update(spend_data)
    
    print(f"[OK] Datos de spend obtenidos para {len(all_spend_data)} adsets")

    # 3) Lista para almacenar resultados
    positive_roi_posts = []
    filtered_count = 0
    
    # 4) Recorrer cuentas/adsets
    for account in AD_ACCOUNTS:
        print(f"Procesando cuenta {account}...")
        adsets = fetch_account_adsets(account)
        
        # page_id se extraerá del post_id cuando esté disponible
        
        for adset in adsets:
            adset_id = adset["id"]
            name = adset.get("name", "")
            
            # Buscar datos en Leadpier
            name_norm = name.strip().lower()
            row = lp_df[lp_df["adset_name_norm"] == name_norm]
            
            revenue = float(row["revenue"].iloc[0]) if not row.empty else 0.0
            
            # Obtener spend del diccionario optimizado
            spend = all_spend_data.get(adset_id, 0.0)
            if spend > 0:
                print(f"[INFO] Adset {adset_id}: spend ${spend:.2f}")
            else:
                print(f"[DEBUG] Sin datos de spend para adset {adset_id} en fecha {today}")
            
            roi = ((revenue - spend) / spend * 100.0) if spend > 0 else 0.0
            profit = revenue - spend
            
            # FILTRO: Solo procesar adsets con ROI >= 0 Y spend >= 20
            if roi >= ROI_POSITIVE_THRESHOLD and spend >= MIN_SPEND_THRESHOLD:
                print(f"🎯 ADSET VÁLIDO: {name[:50]}... | ROI: {roi:.2f}% | Spend: ${spend:.2f} | Profit: ${profit:.2f}")
                
                # Obtener post_ids de este adset
                post_data = fetch_adset_ads_with_posts(adset_id)
                
                for post_info in post_data:
                    if post_info["post_id"]:
                        # Extraer page_id y post_id del formato page_id_post_id
                        post_id_parts = post_info["post_id"].split("_")
                        if len(post_id_parts) >= 2:
                            actual_page_id = post_id_parts[0]  # El page_id real del post
                            clean_post_id = post_id_parts[-1]
                        else:
                            # Si no tiene formato page_id_post_id, usar el post_id tal como está
                            actual_page_id = "unknown"
                            clean_post_id = post_info["post_id"]
                        
                        facebook_link = f"https://www.facebook.com/{actual_page_id}/posts/{clean_post_id}/"
                        
                        positive_roi_posts.append({
                            "account_id": account,
                            "page_id": actual_page_id,  # Usar el page_id real del post
                            "actual_page_id": actual_page_id,
                            "adset_id": adset_id,
                            "adset_name": name,
                            "ad_id": post_info["ad_id"],
                            "ad_name": post_info["ad_name"],
                            "post_id": clean_post_id,
                            "full_post_id": post_info["post_id"],
                            "facebook_link": facebook_link,
                            "spend": spend,
                            "revenue": revenue,
                            "roi": roi,
                            "profit": profit
                        })
                        
                        print(f"   📎 Link: {facebook_link}")
            else:
                if spend < MIN_SPEND_THRESHOLD:
                    filtered_count += 1
                    print(f"🚫 FILTRADO (spend < ${MIN_SPEND_THRESHOLD}): {name[:50]}... | Spend: ${spend:.2f}")
                elif roi < ROI_POSITIVE_THRESHOLD:
                    print(f"🚫 FILTRADO (ROI < {ROI_POSITIVE_THRESHOLD}%): {name[:50]}... | ROI: {roi:.2f}%")
    
    print(f"\n📊 RESUMEN DE FILTROS:")
    print(f"   🚫 Adsets filtrados por spend < ${MIN_SPEND_THRESHOLD}: {filtered_count}")
    print(f"   ✅ Adsets válidos procesados: {len(positive_roi_posts)}")
    
    return positive_roi_posts

def remove_duplicates_and_score(posts_data):
    """Remueve duplicados por facebook_link y calcula puntuaciones híbridas"""
    if not posts_data:
        return []
    
    print("\n🔄 PROCESANDO DATOS CON SISTEMA HÍBRIDO:")
    print(f"   📊 Posts originales: {len(posts_data)}")
    
    # Convertir a DataFrame para facilitar el procesamiento
    df = pd.DataFrame(posts_data)
    
    # 1) Remover duplicados basados en facebook_link
    df_unique = df.drop_duplicates(subset=['facebook_link'], keep='first')
    
    duplicates_removed = len(df) - len(df_unique)
    print(f"   🗑️ Duplicados removidos: {duplicates_removed}")
    print(f"   ✅ Posts únicos: {len(df_unique)}")
    
    # 2) Calcular puntuaciones individuales
    df_unique['spend_punctuation'] = df_unique['spend'].apply(calculate_spend_punctuation)
    df_unique['roi_punctuation'] = df_unique['roi'].apply(calculate_roi_punctuation)
    df_unique['profit_punctuation'] = df_unique['profit'].apply(calculate_profit_punctuation)
    df_unique['profit_multiplier'] = df_unique['profit'].apply(calculate_profit_multiplier)
    
    # 3) Calcular puntuación híbrida: (Spend × ROI × Profit) × Multiplier
    df_unique['base_score'] = df_unique['spend_punctuation'] * df_unique['roi_punctuation'] * df_unique['profit_punctuation']
    df_unique['total_score'] = df_unique['base_score'] * df_unique['profit_multiplier']
    
    # 4) Ordenar por puntuación total (mayor a menor)
    df_unique = df_unique.sort_values('total_score', ascending=False)
    
    print(f"   🏆 Rango de puntuaciones: {df_unique['total_score'].min():.2f} - {df_unique['total_score'].max():.2f}")
    
    return df_unique.to_dict('records')

def create_simple_list(posts_data):
    """Crea una lista simple ordenada para copiar y enviar (SIN SCORE)"""
    if not posts_data:
        return []
    
    print("\n📋 LISTA SIMPLE PARA COPIAR:")
    print("=" * 60)
    
    simple_list = []
    for i, post in enumerate(posts_data, 1):
        adset_name = post['adset_name']
        facebook_link = post['facebook_link']
        
        # Crear línea formateada simple: solo nombre y link
        line = f"{i}. {adset_name}\n{facebook_link}"
        simple_list.append(line)
        print(f"{i}. {adset_name}")
        print(facebook_link)
        print()
    
    return simple_list

def export_results(posts_data):
    """Exporta los resultados a un CSV y crea lista simple"""
    if not posts_data:
        print("❌ No se encontraron posts con ROI positivo y spend >= $20.")
        return
    
    # Procesar datos: remover duplicados y calcular puntuaciones
    processed_data = remove_duplicates_and_score(posts_data)
    
    if not processed_data:
        print("❌ No quedaron datos después del procesamiento.")
        return
    
    df = pd.DataFrame(processed_data)
    output_file = "positive_roi_posts_final.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n📁 RESULTADOS EXPORTADOS:")
    print(f"   📄 Archivo CSV: {output_file}")
    print(f"   📊 Total posts únicos: {len(processed_data)}")
    print(f"   🎯 Adsets únicos: {len(df['adset_id'].unique())}")
    print(f"   🏢 Cuentas procesadas: {len(df['account_id'].unique())}")
    
    # Mostrar estadísticas de puntuación
    print(f"\n📊 ESTADÍSTICAS DE PUNTUACIÓN HÍBRIDA:")
    print(f"   🏆 Puntuación más alta: {df['total_score'].max():.2f}")
    print(f"   📉 Puntuación más baja: {df['total_score'].min():.2f}")
    print(f"   📈 Puntuación promedio: {df['total_score'].mean():.2f}")
    
    # Crear lista simple para copiar (SIN SCORE)
    simple_list = create_simple_list(processed_data)
    
    # Exportar lista simple a archivo de texto (SIN SCORE)
    simple_file = "lista_ordenada_adsets.txt"
    with open(simple_file, 'w', encoding='utf-8') as f:
        f.write("LISTA ORDENADA DE ADSETS CON ROI POSITIVO\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total adsets: {len(processed_data)}\n")
        f.write(f"Fecha: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, post in enumerate(processed_data, 1):
            f.write(f"{i}. {post['adset_name']}\n")
            f.write(f"   Spend: ${post['spend']:.2f} | ROI: {post['roi']:.1f}% | Profit: ${post['profit']:.2f}\n")
            f.write(f"   Link: {post['facebook_link']}\n\n")
    
    print(f"   📄 Lista simple: {simple_file}")
    
    # Mostrar todos los posts por puntuación
    print(f"\n🏆 TODOS LOS POSTS CON ROI POSITIVO (ordenados por puntuación):")
    for i, row in df.iterrows():
        print(f"{i+1}. {row['adset_name']}")
        print(row['facebook_link'])
        print()
    
    return df

# ================== EXECUTION ==================
if __name__ == "__main__":
    print("🚀 EXTRACTOR DE POST IDs CON SISTEMA HÍBRIDO")
    print("🔄 SISTEMA: (Spend × ROI × Profit) × Profit_Multiplier")
    print(f"🚫 FILTROS: ROI >= {ROI_POSITIVE_THRESHOLD}% Y Spend >= ${MIN_SPEND_THRESHOLD}")
    print("=" * 60)
    
    # Ejecutar extracción
    results = extract_positive_roi_posts()
    
    # Exportar resultados
    export_results(results)
    
    print("\n✅ PROCESO COMPLETADO")
    print("📋 Puedes copiar la lista de arriba o usar el archivo 'lista_ordenada_adsets.txt'")
