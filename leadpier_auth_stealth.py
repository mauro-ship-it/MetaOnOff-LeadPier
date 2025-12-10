"""
Módulo de autenticación STEALTH para Leadpier
Implementa técnicas anti-detección para evadir medidas anti-bot
"""
import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(__file__), "enviorement.env")
load_dotenv(dotenv_path=env_path)

LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")
LEADPIER_EMAIL = os.getenv("LEADPIER_EMAIL")
LEADPIER_PASSWORD = os.getenv("LEADPIER_PASSWORD")
PROXY_URL = os.getenv("PROXY_URL")


def create_stealth_driver(headless=False):
    """
    Crea un driver de Chrome con configuración anti-detección
    Implementa técnicas para evadir detección de automatización
    """
    chrome_options = Options()
    
    # Configuraciones básicas
    if headless:
        chrome_options.add_argument("--headless=new")  # Nuevo modo headless más difícil de detectar
    
    # Anti-detección: User agent realista
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Argumentos para parecer más humano
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Ocultar que es automatizado
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # No mostrar "Chrome is being controlled"
    chrome_options.add_experimental_option('useAutomationExtension', False)  # No usar extensión de automatización
    
    # Configuraciones de navegador normal
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    # Simular configuraciones de usuario real
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,  # Bloquear notificaciones
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })
    
    # Inicializar driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    # JavaScript para ocultar webdriver y otras propiedades de automatización
    stealth_js = """
    // Sobrescribir la propiedad webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    
    // Sobrescribir plugins para parecer navegador real
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    
    // Sobrescribir languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    
    // Agregar chrome runtime para parecer más real
    window.chrome = {
        runtime: {}
    };
    
    // Sobrescribir permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    """
    
    # Ejecutar el script anti-detección
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': stealth_js
    })
    
    return driver


def human_typing(element, text, min_delay=0.05, max_delay=0.15):
    """
    Escribe texto de manera más humana con delays variables
    """
    import random
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))


def random_mouse_movement(driver):
    """
    Simula movimiento aleatorio del mouse
    """
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        import random
        
        action = ActionChains(driver)
        # Mover mouse a posición aleatoria
        x_offset = random.randint(100, 500)
        y_offset = random.randint(100, 400)
        action.move_by_offset(x_offset, y_offset).perform()
        time.sleep(random.uniform(0.3, 0.8))
    except:
        pass


def stealth_login_leadpier(email, password, headless=False):
    """
    Login con técnicas anti-detección
    """
    driver = None
    try:
        print("[STEALTH AUTH] Iniciando login con técnicas anti-detección...")
        
        # Crear driver con configuración stealth
        driver = create_stealth_driver(headless=headless)
        
        print("[STEALTH AUTH] Navegando a la página de login...")
        driver.get("https://dash.leadpier.com/login")
        
        # Esperar de manera más humana (no siempre el mismo tiempo)
        import random
        wait = WebDriverWait(driver, 30)
        time.sleep(random.uniform(2, 4))
        
        # Simular movimiento de mouse antes de interactuar
        random_mouse_movement(driver)
        
        # Esperar y llenar el campo de email de manera humana
        print("[STEALTH AUTH] Ingresando credenciales de manera natural...")
        email_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[placeholder*='email' i]"))
        )
        
        # Click en el campo primero
        email_field.click()
        time.sleep(random.uniform(0.5, 1.2))
        
        # Escribir email de manera humana
        human_typing(email_field, email)
        time.sleep(random.uniform(0.8, 1.5))
        
        # Movimiento de mouse aleatorio
        random_mouse_movement(driver)
        
        # Llenar password de manera humana
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.click()
        time.sleep(random.uniform(0.5, 1.0))
        human_typing(password_field, password)
        
        # Esperar un poco antes de hacer click (como haría un humano)
        time.sleep(random.uniform(1.5, 2.5))
        
        # Buscar y hacer click en el botón
        print("[STEALTH AUTH] Buscando botón de Login...")
        selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
        ]
        
        login_button = None
        for selector_type, selector_value in selectors:
            try:
                login_button = wait.until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                break
            except:
                continue
        
        if not login_button:
            print("[STEALTH AUTH] ERROR: No se encontró el botón de login")
            return None
        
        # Click humano (con movimiento previo)
        print("[STEALTH AUTH] Haciendo click en Login...")
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        time.sleep(random.uniform(0.3, 0.7))
        login_button.click()
        
        # Esperar respuesta del servidor
        print("[STEALTH AUTH] Esperando respuesta del servidor...")
        time.sleep(random.uniform(3, 5))
        
        # Verificar login exitoso
        max_wait = 15
        for i in range(max_wait):
            current_url = driver.current_url
            if '/login' not in current_url:
                print(f"[STEALTH AUTH] Login completado exitosamente")
                break
            time.sleep(1)
        
        if '/login' in driver.current_url:
            print("[STEALTH AUTH] ERROR: El login no se completó")
            # Tomar screenshot
            try:
                driver.save_screenshot("stealth_login_error.png")
                print("[STEALTH AUTH] Screenshot guardado: stealth_login_error.png")
            except:
                pass
            return None
        
        # Dar tiempo para que el token se active
        print("[STEALTH AUTH] Esperando activación del token...")
        time.sleep(random.uniform(5, 7))
        
        # Navegar a estadísticas de manera humana
        print("[STEALTH AUTH] Navegando a estadísticas...")
        random_mouse_movement(driver)
        driver.get("https://dash.leadpier.com/marketer-statistics/sources")
        time.sleep(random.uniform(8, 12))
        
        # Simular scroll humano
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            current_position = 0
            
            # Scroll en pequeños incrementos
            while current_position < total_height / 2:
                scroll_amount = random.randint(100, 300)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                current_position += scroll_amount
                time.sleep(random.uniform(0.3, 0.8))
            
            # Volver arriba
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
        except:
            pass
        
        # Extraer token con validación desde el navegador
        print("[STEALTH AUTH] Extrayendo y validando token desde el navegador...")
        
        validate_from_browser = """
        return new Promise((resolve) => {
            try {
                const auth = localStorage.getItem('authentication');
                if (!auth) {
                    resolve({success: false, error: 'No authentication in localStorage'});
                    return;
                }
                
                const parsed = JSON.parse(auth);
                const token = parsed.token;
                
                if (!token) {
                    resolve({success: false, error: 'No token in authentication object'});
                    return;
                }
                
                // Validar el token
                fetch('https://webapi.leadpier.com/v1/api/user/getBalance', {
                    method: 'GET',
                    headers: {
                        'authorization': 'bearer ' + token,
                        'content-type': 'application/json',
                        'accept': 'application/json'
                    }
                })
                .then(response => {
                    resolve({
                        success: response.ok,
                        status: response.status,
                        token: token,
                        tokenLength: token.length
                    });
                })
                .catch(error => {
                    resolve({
                        success: false,
                        error: 'Fetch error: ' + error.toString(),
                        token: token
                    });
                });
            } catch (e) {
                resolve({
                    success: false,
                    error: 'Exception: ' + e.toString()
                });
            }
        });
        """
        
        browser_validation = driver.execute_script(validate_from_browser)
        
        if browser_validation and browser_validation.get('success'):
            bearer_token = browser_validation.get('token')
            print(f"[STEALTH AUTH] ✓ Token validado exitosamente!")
            print(f"[STEALTH AUTH] Token: {bearer_token[:50]}... (longitud: {browser_validation.get('tokenLength')})")
            return bearer_token
        else:
            print(f"[STEALTH AUTH] Validación falló: {browser_validation.get('error', 'Unknown')}")
            
            # Intentar extraer de todas formas
            if browser_validation.get('token'):
                token = browser_validation.get('token')
                print(f"[STEALTH AUTH] Token extraído (no validado): {token[:50]}...")
                return token
            
            return None
        
    except Exception as e:
        print(f"[STEALTH AUTH] Error durante el login: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        if driver:
            print("[STEALTH AUTH] Cerrando navegador...")
            time.sleep(2)  # Dar un poco más de tiempo antes de cerrar
            driver.quit()


def validate_bearer_token():
    """Valida si el bearer token actual funciona"""
    try:
        url = "https://webapi.leadpier.com/v1/api/stats/user/sources"
        payload = {
            "limit": 1,
            "offset": 0,
            "periodFrom": "today",
            "periodTo": "today",
            "source": "BM5_1"
        }
        headers = {
            "authorization": f"bearer {LEADPIER_BEARER}",
            "content-type": "application/json",
            "accept": "application/json",
            "origin": "https://dash.leadpier.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "referer": "https://dash.leadpier.com/",
        }
        
        # NO usar proxy
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        
        if response.status_code == 200:
            return True
        
        if response.status_code in [401, 403]:
            print(f"[AUTH] Token inválido - Status: {response.status_code}")
            return False
        
        print(f"[AUTH] Respuesta inesperada - Status: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"[AUTH] Error al validar token: {e}")
        return False


def update_env_bearer_token(new_token):
    """Actualiza el bearer token en el archivo enviorement.env"""
    global LEADPIER_BEARER
    
    try:
        new_token = new_token.strip()
        
        print(f"\n[AUTH DEBUG] Actualizando token en .env")
        print(f"[AUTH DEBUG] Token a guardar: {new_token[:50]}...")
        print(f"[AUTH DEBUG] Longitud: {len(new_token)} caracteres")
        
        env_path = os.path.join(os.path.dirname(__file__), "enviorement.env")
        
        if not os.path.exists(env_path):
            print("[AUTH] Error: No se encontró enviorement.env")
            return False
        
        # Leer archivo
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Actualizar línea
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('LEADPIER_BEARER='):
                lines[i] = f'LEADPIER_BEARER={new_token}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'LEADPIER_BEARER={new_token}\n')
        
        # Guardar archivo
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"[AUTH DEBUG] ✓ Token actualizado en {env_path}")
        
        LEADPIER_BEARER = new_token
        os.environ['LEADPIER_BEARER'] = new_token
        
        return True
        
    except Exception as e:
        print(f"[AUTH] Error al actualizar enviorement.env: {e}")
        return False


def ensure_leadpier_token_stealth():
    """Valida el token y lo renueva usando técnicas stealth si es necesario"""
    global LEADPIER_BEARER
    
    print("[STEALTH AUTH] Validando bearer token...")
    
    if validate_bearer_token():
        print("[STEALTH AUTH] Token válido")
        return True
    
    print("[STEALTH AUTH] Token inválido. Intentando login con técnicas anti-detección...")
    
    if not LEADPIER_EMAIL or not LEADPIER_PASSWORD:
        print("[STEALTH AUTH] ERROR: Credenciales no encontradas")
        return False
    
    # Intentar con headless primero
    new_token = stealth_login_leadpier(LEADPIER_EMAIL, LEADPIER_PASSWORD, headless=True)
    
    # Si falla, intentar con navegador visible
    if not new_token:
        print("[STEALTH AUTH] Headless falló. Intentando con navegador visible...")
        new_token = stealth_login_leadpier(LEADPIER_EMAIL, LEADPIER_PASSWORD, headless=False)
    
    if not new_token:
        print("\n" + "="*70)
        print("TOKEN NO PUDO SER RENOVADO AUTOMÁTICAMENTE")
        print("="*70)
        print("\nPuede ser que LeadPier esté bloqueando automatización.")
        print("\nOPCIONES:")
        print("\n1. ESPERAR 30-60 MINUTOS (si hay rate limiting temporal)")
        print("2. USAR NAVEGADOR DIFERENTE o IP DIFERENTE")
        print("3. ACTUALIZACIÓN MANUAL:")
        print("   - Ve a https://dash.leadpier.com en tu navegador personal")
        print("   - Inicia sesión normalmente")
        print("   - F12 → Console")
        print("   - Ejecuta: JSON.parse(localStorage.getItem('authentication')).token")
        print("   - Copia el token y actualiza enviorement.env")
        print("="*70 + "\n")
        return False
    
    print("[STEALTH AUTH] Login exitoso. Actualizando token...")
    if update_env_bearer_token(new_token):
        LEADPIER_BEARER = new_token
        
        # Verificar que funciona
        print("[STEALTH AUTH] Verificando token guardado...")
        if validate_bearer_token():
            print("[STEALTH AUTH] ✓ Token verificado exitosamente")
            return True
        else:
            print("[STEALTH AUTH] ⚠ Token guardado pero no pasa validación")
            return False
    else:
        print("[STEALTH AUTH] ERROR: No se pudo actualizar el token")
        return False


if __name__ == "__main__":
    """Test del módulo"""
    print("Probando autenticación stealth...")
    result = ensure_leadpier_token_stealth()
    print(f"\nResultado: {'✓ EXITOSO' if result else '✗ FALLIDO'}")

