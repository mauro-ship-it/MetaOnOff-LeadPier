"""
Extrae datos de LeadPier usando sesión del navegador real
Como LeadPier bloquea peticiones desde Python, usamos el navegador
"""
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import pandas as pd

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(__file__), "enviorement.env")
load_dotenv(dotenv_path=env_path)

LEADPIER_EMAIL = os.getenv("LEADPIER_EMAIL")
LEADPIER_PASSWORD = os.getenv("LEADPIER_PASSWORD")


def get_leadpier_data_from_browser():
    """
    Hace login en LeadPier usando el navegador y extrae datos
    ejecutando fetch() desde el contexto del navegador
    """
    driver = None
    try:
        print("[BROWSER] Iniciando navegador para LeadPier...")
        
        # Configurar Chrome
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Ir a login
        print("[BROWSER] Navegando a login...")
        driver.get("https://dash.leadpier.com/login")
        time.sleep(3)
        
        # Login automático
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, 30)
        
        print("[BROWSER] Haciendo login...")
        email_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[placeholder*='email' i]"))
        )
        email_field.send_keys(LEADPIER_EMAIL)
        
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.send_keys(LEADPIER_PASSWORD)
        
        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        login_button.click()
        
        print("[BROWSER] Esperando login...")
        time.sleep(5)
        
        # Verificar login exitoso
        if '/login' in driver.current_url:
            print("[BROWSER] ERROR: Login falló")
            return None
        
        print("[BROWSER] Login exitoso!")
        
        # Hacer petición API desde el navegador
        print("[BROWSER] Obteniendo datos de LeadPier...")
        
        fetch_script = """
        return new Promise((resolve) => {
            fetch('https://webapi.leadpier.com/v1/api/stats/user/sources', {
                method: 'POST',
                headers: {
                    'authorization': 'bearer ' + JSON.parse(localStorage.getItem('authentication')).token,
                    'content-type': 'application/json',
                    'accept': 'application/json'
                },
                body: JSON.stringify({
                    limit: 200,
                    offset: 0,
                    orderDirection: 'DESC',
                    groupBy: 'HOUR',
                    orderBy: 'visitors',
                    periodFrom: 'today',
                    periodTo: 'today',
                    source: 'BM5_1'
                })
            })
            .then(response => response.json())
            .then(data => resolve({success: true, data: data}))
            .catch(error => resolve({success: false, error: error.toString()}));
        });
        """
        
        result = driver.execute_script(fetch_script)
        
        if not result.get('success'):
            print(f"[BROWSER] ERROR: {result.get('error')}")
            return None
        
        print("[BROWSER] Datos obtenidos exitosamente!")
        return result.get('data')
        
    except Exception as e:
        print(f"[BROWSER] Error: {e}")
        return None
        
    finally:
        if driver:
            print("[BROWSER] Cerrando navegador...")
            driver.quit()


def process_leadpier_data(data):
    """Procesa los datos de LeadPier a DataFrame"""
    if not data or 'data' not in data:
        print("[BROWSER] No hay datos para procesar")
        return pd.DataFrame()
    
    raw_data = data['data']
    
    # Manejar diferentes estructuras
    if isinstance(raw_data, dict):
        if "statistics" in raw_data and isinstance(raw_data["statistics"], list):
            raw_data = raw_data["statistics"]
        elif all(isinstance(v, dict) for v in raw_data.values()):
            raw_data = list(raw_data.values())
        else:
            raw_data = [raw_data]
    
    if not raw_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    
    # Procesar columnas
    rename_map = {
        'sourceName': 'adset_name',
        'source_name': 'adset_name',
        'source': 'adset_name',
        'revenue': 'revenue',
        'epl': 'epl',
        'epc': 'epc'
    }
    
    df = df.rename(columns=rename_map)
    
    # Asegurar columnas necesarias
    if 'adset_name' not in df.columns:
        print("[BROWSER] ADVERTENCIA: No se encontró columna de nombre de adset")
        return pd.DataFrame()
    
    # Convertir revenue a numérico
    if 'revenue' in df.columns:
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
    else:
        df['revenue'] = 0
    
    # Normalizar nombres
    df['adset_name_norm'] = df['adset_name'].str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
    
    print(f"[BROWSER] Procesados {len(df)} registros de LeadPier")
    return df[['adset_name', 'revenue', 'adset_name_norm']]


def main():
    """Test del script"""
    print("\n" + "="*70)
    print(" OBTENER DATOS DE LEADPIER VÍA NAVEGADOR")
    print("="*70 + "\n")
    
    data = get_leadpier_data_from_browser()
    
    if data:
        df = process_leadpier_data(data)
        
        if not df.empty:
            print("\n" + "="*70)
            print(" DATOS OBTENIDOS")
            print("="*70)
            print(df.head(10))
            print(f"\nTotal registros: {len(df)}")
            print(f"Revenue total: ${df['revenue'].sum():.2f}")
            
            # Guardar CSV
            output_file = "leadpier_data_browser.csv"
            df.to_csv(output_file, index=False)
            print(f"\n✓ Datos guardados en: {output_file}")
        else:
            print("\n⚠️  No se pudieron procesar los datos")
    else:
        print("\n❌ No se pudieron obtener datos de LeadPier")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

