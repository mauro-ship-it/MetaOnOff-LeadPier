"""
Módulo de autenticación para Leadpier
Valida el bearer token y realiza auto-login si es necesario
"""
import os
import time
import json
import requests

# Intentar importar selenium-wire
try:
    from seleniumwire import webdriver as wire_webdriver
    SELENIUM_WIRE_AVAILABLE = True
    print("[DEBUG] selenium-wire importado exitosamente")
except ImportError as e:
    wire_webdriver = None
    SELENIUM_WIRE_AVAILABLE = False
    print(f"[DEBUG] selenium-wire no disponible: {e}")

# Importar clases estándar de selenium (siempre necesarias)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Cargar variables de entorno desde la ubicación correcta
env_path = os.path.join(os.path.dirname(__file__), "enviorement.env")
load_dotenv(dotenv_path=env_path)

LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")
LEADPIER_EMAIL = os.getenv("LEADPIER_EMAIL")
LEADPIER_PASSWORD = os.getenv("LEADPIER_PASSWORD")
PROXY_URL = os.getenv("PROXY_URL")


def get_proxies():
    """Retorna el diccionario de proxies para usar en requests"""
    if PROXY_URL:
        return {"http": PROXY_URL, "https": PROXY_URL}
    return None


def validate_bearer_token():
    """
    Valida si el bearer token actual funciona haciendo una petición POST a webapi.leadpier.com
    Returns:
        bool: True si el token es válido, False si está expirado o es inválido
    """
    try:
        # Usar el mismo endpoint POST que usa el script principal
        url = "https://webapi.leadpier.com/v1/api/stats/user/sources"
        payload = {
            "limit": 1,
            "offset": 0,
            "periodFrom": "today",
            "periodTo": "today",
            "source": "BM5_1"
        }
        headers = {
            "authorization": f"bearer {LEADPIER_BEARER}",  # minúsculas - como el navegador
            "content-type": "application/json",
            "accept": "application/json",
            "origin": "https://dash.leadpier.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "referer": "https://dash.leadpier.com/",
        }
        
        # IMPORTANTE: NO usar proxy para Leadpier - lo bloquea con 401
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        
        # Si recibimos 200, el token es válido
        if response.status_code == 200:
            return True
        
        # Si recibimos 401 o 403, el token es inválido/expirado
        if response.status_code in [401, 403]:
            print(f"[AUTH] Token invalido - Status: {response.status_code}")
            return False
        
        # Otros códigos, consideramos que el token podría estar mal
        print(f"[AUTH] Respuesta inesperada - Status: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"[AUTH] Error al validar token: {e}")
        return False


def auto_login_leadpier(email, password, headless=True):
    """
    Realiza login automático en Leadpier usando Selenium con Chrome DevTools Protocol
    Captura el bearer token del header Authorization en el request XHR
    
    Args:
        email (str): Email de login
        password (str): Password de login
        headless (bool): Si True, ejecuta el navegador en modo headless (sin ventana)
    
    Returns:
        str: Bearer token si el login es exitoso, None si falla
    """
    driver = None
    try:
        print("[AUTH] Iniciando proceso de login automatico...")
        
        # Configurar opciones de Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")  # Ejecutar sin ventana visible
            print("[AUTH] Modo headless activado")
        else:
            print("[AUTH] Modo visible activado (para debugging de cookies)")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # NO agregar proxy para Selenium/auto-login ya que puede causar problemas de timeout
        # El proxy solo se usa para las llamadas API normales, no para el navegador automatizado
        
        # Configurar selenium-wire si está disponible
        seleniumwire_options = {}
        if SELENIUM_WIRE_AVAILABLE:
            # Configurar selenium-wire para capturar requests
            seleniumwire_options = {
                'disable_encoding': True,  # Deshabilitar compresión para ver responses
                'verify_ssl': True,
            }
            print("[AUTH] Usando selenium-wire para capturar requests...")
        else:
            # Fallback: usar logging de Chrome DevTools
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            print("[AUTH] Usando Chrome DevTools logs (instala selenium-wire para mejor captura)")
        
        # Inicializar driver
        print("[AUTH] Iniciando navegador...")
        if SELENIUM_WIRE_AVAILABLE and wire_webdriver:
            driver = wire_webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options,
                seleniumwire_options=seleniumwire_options
            )
        else:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
        
        # Navegar a la página de login
        print("[AUTH] Navegando a https://dash.leadpier.com/login...")
        driver.get("https://dash.leadpier.com/login")
        
        # Esperar a que cargue la página
        wait = WebDriverWait(driver, 30)
        
        # Esperar y llenar el campo de email
        print("[AUTH] Ingresando credenciales...")
        email_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[placeholder*='email' i]"))
        )
        email_field.clear()
        email_field.send_keys(email)
        
        # Llenar el campo de password
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.clear()
        password_field.send_keys(password)
        
        # Hacer clic en el botón de login (intentar diferentes selectores)
        print("[AUTH] Buscando boton de Login...")
        
        # Selectores ordenados por especificidad (más específico primero)
        selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[@type='submit' and contains(@class, 'bg-button-primary')]"),
            (By.XPATH, "//button[@type='submit']//span[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(@class, 'bg-button-primary')]"),
            (By.XPATH, "//button[@type='submit']"),
        ]
        
        login_button = None
        for selector_type, selector_value in selectors:
            try:
                # Esperar a que el botón esté presente y sea clickeable
                login_button = wait.until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print(f"[AUTH] Boton encontrado y clickeable")
                break
            except:
                continue
        
        if not login_button:
            print("[AUTH] ERROR: No se pudo encontrar el boton de login")
            return None
        
        # Hacer click en el botón
        print("[AUTH] Haciendo clic en Login...")
        try:
            # Método 1: Click normal
            login_button.click()
            print("[AUTH] Click exitoso")
        except:
            try:
                # Método 2: Scroll y click
                driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                time.sleep(0.5)
                login_button.click()
                print("[AUTH] Click exitoso (con scroll)")
            except:
                try:
                    # Método 3: Click con JavaScript
                    print("[AUTH] Usando JavaScript click...")
                    driver.execute_script("arguments[0].click();", login_button)
                    print("[AUTH] Click exitoso (JavaScript)")
                except Exception as e:
                    print(f"[AUTH] ERROR: No se pudo hacer click en el boton: {e}")
                    return None
        
        # Esperar a que el login se complete
        print("[AUTH] Esperando respuesta del servidor...")
        time.sleep(3)
        
        # Verificar si el login fue exitoso (debe redirigir fuera de /login)
        current_url = driver.current_url
        
        # Esperar a que la URL cambie (indicando login exitoso)
        max_wait = 15
        for i in range(max_wait):
            current_url = driver.current_url
            if '/login' not in current_url:
                print(f"[AUTH] Login completado exitosamente")
                break
            time.sleep(1)
        
        if '/login' in current_url:
            print("[AUTH] ERROR: El login no se completó (aún en página de login)")
            
            # Intentar capturar mensajes de error en la página
            try:
                error_messages = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .message, [class*='error'], [class*='alert']")
                if error_messages:
                    print("[AUTH] Mensajes encontrados en la página:")
                    for msg in error_messages[:3]:  # Mostrar máximo 3 mensajes
                        text = msg.text.strip()
                        if text:
                            print(f"  - {text}")
            except:
                pass
            
            # Tomar screenshot para debugging
            try:
                screenshot_path = "login_error_screenshot.png"
                driver.save_screenshot(screenshot_path)
                print(f"[AUTH] Screenshot guardado en: {screenshot_path}")
            except:
                pass
            
            print("[AUTH] Puede ser credenciales incorrectas o problema de conectividad")
            print("[AUTH] Verifica las credenciales en enviorement.env")
            return None
        
        # Dar tiempo para que se cargue la página inicial después del login
        # IMPORTANTE: Dar más tiempo para que el token se active en el servidor
        print("[AUTH] Esperando a que el token se active en el servidor...")
        time.sleep(5)
        
        # Navegar a la página de estadísticas que dispare requests API para capturar el token
        print("[AUTH] Navegando a pagina de estadisticas para capturar requests API...")
        try:
            # Navegar a la página correcta de estadísticas de marketer
            driver.get("https://dash.leadpier.com/marketer-statistics/sources")
            
            # Esperar a que la página cargue completamente
            print("[AUTH] Esperando que carguen los datos...")
            time.sleep(8)
            
            # Verificar que la página cargó correctamente
            current_url = driver.current_url
            page_title = driver.title
            print(f"[AUTH DEBUG] URL actual: {current_url}")
            print(f"[AUTH DEBUG] Titulo de pagina: {page_title}")
            
            # Hacer scroll para activar lazy loading y disparar más requests
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except:
                pass
            
            # Esperar adicional para que se disparen todos los requests
            time.sleep(2)
            
            # NUEVO: Intentar hacer que el navegador ejecute una petición API y capturar el token usado
            try:
                print("[AUTH] Intentando hacer peticion API desde el navegador...")
                api_test_script = """
                return new Promise((resolve) => {
                    // Obtener el token de localStorage
                    let token = null;
                    try {
                        const auth = localStorage.getItem('authentication');
                        if (auth) {
                            const parsed = JSON.parse(auth);
                            token = parsed.token;
                        }
                    } catch (e) {
                        console.error('Error al obtener token:', e);
                    }
                    
                    if (!token) {
                        resolve({success: false, error: 'No se encontró token en localStorage'});
                        return;
                    }
                    
                    // Hacer una petición real
                    fetch('https://webapi.leadpier.com/v1/api/user/getBalance', {
                        method: 'GET',
                        headers: {
                            'authorization': 'bearer ' + token,
                            'content-type': 'application/json',
                            'accept': 'application/json'
                        }
                    })
                    .then(response => {
                        return response.json().then(data => {
                            resolve({
                                success: response.ok,
                                status: response.status,
                                token: token,
                                data: response.ok ? data : null,
                                error: !response.ok ? data : null
                            });
                        });
                    })
                    .catch(error => {
                        resolve({
                            success: false,
                            error: error.toString(),
                            token: token
                        });
                    });
                });
                """
                
                api_result = driver.execute_script(api_test_script)
                
                if api_result and api_result.get('success'):
                    working_token = api_result.get('token')
                    print(f"[AUTH] Petición API exitosa desde el navegador!")
                    print(f"[AUTH] Token funcional extraído: {working_token[:50]}... (longitud: {len(working_token)})")
                    # Guardar este token como bearer_token ya que sabemos que funciona
                    bearer_token = working_token
                else:
                    print(f"[AUTH] Petición API desde navegador falló: {api_result.get('error', 'Unknown')}")
                    print(f"[AUTH] Status: {api_result.get('status', 'N/A')}")
                    
            except Exception as e:
                print(f"[AUTH] Error al hacer petición API desde navegador: {e}")
            
        except Exception as e:
            print(f"[AUTH] Error al navegar a marketer-statistics: {e}")
            # Continuar de todos modos, puede que ya tengamos el token
        
        # Intentar extraer el token de network requests o localStorage
        print("[AUTH] Buscando bearer token...")
        bearer_token = None
        
        # MÉTODO 0 - MÁS CONFIABLE: Extraer de localStorage y validar desde el navegador
        try:
            print("[AUTH] Método prioritario: Extraer y validar token desde el navegador...")
            
            validate_from_browser = """
            return new Promise((resolve) => {
                // Obtener el token de localStorage
                let token = null;
                try {
                    const auth = localStorage.getItem('authentication');
                    if (auth) {
                        const parsed = JSON.parse(auth);
                        token = parsed.token;
                    }
                } catch (e) {
                    resolve({success: false, error: 'Error al parsear localStorage: ' + e.toString()});
                    return;
                }
                
                if (!token) {
                    resolve({success: false, error: 'No se encontró token en localStorage.authentication'});
                    return;
                }
                
                // Validar el token haciendo una petición real
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
                        tokenLength: token.length,
                        tokenParts: token.split('.').length
                    });
                })
                .catch(error => {
                    resolve({
                        success: false,
                        error: 'Fetch error: ' + error.toString(),
                        token: token
                    });
                });
            });
            """
            
            browser_validation = driver.execute_script(validate_from_browser)
            
            if browser_validation and browser_validation.get('success'):
                bearer_token = browser_validation.get('token')
                print(f"[AUTH] ✓ Token validado exitosamente desde el navegador!")
                print(f"[AUTH] Token: {bearer_token[:50]}... (longitud: {browser_validation.get('tokenLength')})")
                print(f"[AUTH] Partes JWT: {browser_validation.get('tokenParts')} (debe ser 3)")
                print(f"[AUTH] Status de validación: {browser_validation.get('status')}")
                
                # IMPORTANTE: Imprimir el token COMPLETO para debugging
                print(f"\n[AUTH DEBUG] ========== TOKEN COMPLETO ==========")
                print(f"[AUTH DEBUG] {bearer_token}")
                print(f"[AUTH DEBUG] ========================================\n")
                
                # Este token YA está validado, podemos retornarlo directamente
                print("[AUTH] Token funcional encontrado - omitiendo validación adicional")
                return bearer_token
            else:
                print(f"[AUTH] Validación desde navegador falló: {browser_validation.get('error', 'Unknown')}")
                if browser_validation.get('token'):
                    bearer_token = browser_validation.get('token')
                    print(f"[AUTH] Token extraído (pero no validado): {bearer_token[:50]}...")
                    print(f"\n[AUTH DEBUG] ========== TOKEN COMPLETO (NO VALIDADO) ==========")
                    print(f"[AUTH DEBUG] {bearer_token}")
                    print(f"[AUTH DEBUG] ====================================================\n")
                    
        except Exception as e:
            print(f"[AUTH] Error en método prioritario: {e}")
        
        # Método 1 PRIORITARIO: Usar selenium-wire para capturar requests (más confiable)
        if SELENIUM_WIRE_AVAILABLE and hasattr(driver, 'requests'):
            try:
                print("[AUTH] Buscando token en requests capturados por selenium-wire...")
                leadpier_requests_count = 0
                api_requests_with_auth = []
                
                # Iterar sobre todos los requests capturados
                for request in driver.requests:
                    try:
                        url = request.url
                        
                        # Buscar requests a Leadpier API
                        if 'leadpier.com' in url and request.headers:
                            leadpier_requests_count += 1
                            
                            # Buscar el header Authorization
                            auth_header = request.headers.get('Authorization') or request.headers.get('authorization')
                            if auth_header:
                                api_requests_with_auth.append(url)
                                if auth_header.startswith('Bearer '):
                                    bearer_token = auth_header.replace('Bearer ', '').strip()
                                    print(f"[AUTH] Token encontrado en request a: {url}")
                                    break
                    except:
                        continue
                
                print(f"[AUTH] Se capturaron {leadpier_requests_count} requests a leadpier.com")
                if api_requests_with_auth:
                    print(f"[AUTH] Requests con Authorization: {len(api_requests_with_auth)}")
                
                if not bearer_token and leadpier_requests_count == 0:
                    print("[AUTH] No se capturaron requests API con selenium-wire.")
                    
            except Exception as e:
                print(f"[AUTH] Error al analizar requests de selenium-wire: {e}")
        
        # Método 2: Analizar logs de Chrome DevTools (fallback si no hay selenium-wire)
        if not bearer_token and not SELENIUM_WIRE_AVAILABLE:
            try:
                print("[AUTH] Buscando token en Chrome DevTools logs...")
                logs = driver.get_log('performance')
                leadpier_requests_count = 0
                api_requests_with_auth = []
                
                for entry in logs:
                    try:
                        log = json.loads(entry['message'])['message']
                        
                        # Buscar eventos de red
                        if log.get('method') == 'Network.requestWillBeSent':
                            request_data = log.get('params', {})
                            headers = request_data.get('request', {}).get('headers', {})
                            url = request_data.get('request', {}).get('url', '')
                            
                            # Contar requests a Leadpier para debugging
                            if 'leadpier.com' in url:
                                leadpier_requests_count += 1
                                
                                # Buscar Authorization header en requests a Leadpier
                                if 'Authorization' in headers:
                                    auth_header = headers['Authorization']
                                    api_requests_with_auth.append(url)
                                    
                                    # Debug: mostrar el formato del header completo para el primer request
                                    if len(api_requests_with_auth) == 1:
                                        print(f"[AUTH DEBUG] Primer Authorization header: '{auth_header[:80]}...'")
                                        print(f"[AUTH DEBUG] Longitud del header: {len(auth_header)} caracteres")
                                    
                                    # Intentar extraer el token (probar diferentes formatos)
                                    extracted_token = None
                                    if auth_header.startswith('Bearer '):
                                        extracted_token = auth_header.replace('Bearer ', '').strip()
                                        print(f"[AUTH] Token encontrado en request a: {url}")
                                    elif auth_header.startswith('bearer '):
                                        extracted_token = auth_header.replace('bearer ', '').strip()
                                        print(f"[AUTH] Token encontrado (lowercase) en request a: {url}")
                                    elif ' ' in auth_header:
                                        # Formato: "TipoToken token_value"
                                        parts = auth_header.split(' ', 1)
                                        if len(parts) == 2:
                                            extracted_token = parts[1].strip()
                                            print(f"[AUTH] Token encontrado (formato generico) en request a: {url}")
                                    
                                    # Verificar que el token extraído tenga formato JWT válido
                                    if extracted_token:
                                        token_parts = extracted_token.count('.')
                                        print(f"[AUTH DEBUG] Token extraído tiene {token_parts} puntos (debe ser 2 para JWT)")
                                        print(f"[AUTH DEBUG] Longitud del token: {len(extracted_token)} caracteres")
                                        
                                        if token_parts == 2:
                                            bearer_token = extracted_token
                                            break
                                        else:
                                            print(f"[AUTH WARNING] Token extraído no parece ser un JWT válido, continuando búsqueda...")
                    except:
                        continue
                
                print(f"[AUTH] Se capturaron {leadpier_requests_count} requests a leadpier.com")
                if api_requests_with_auth:
                    print(f"[AUTH] Requests con Authorization: {len(api_requests_with_auth)}")
                    if not bearer_token:
                        print(f"[AUTH WARNING] Se encontraron {len(api_requests_with_auth)} headers Authorization pero ninguno con formato valido")
                
                if not bearer_token and leadpier_requests_count == 0:
                    print("[AUTH] No se capturaron requests API. Puede que se necesite mas tiempo de espera.")
                    
            except Exception as e:
                print(f"[AUTH] Error al analizar logs de performance: {e}")
        
        # Método 3 FALLBACK: Buscar en localStorage solo si no se encontró en network requests
        if not bearer_token:
            try:
                print("[AUTH] Buscando token en localStorage...")
                local_storage_data = driver.execute_script("""
                    let data = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        data[key] = localStorage.getItem(key);
                    }
                    return data;
                """)
                
                for key, value in local_storage_data.items():
                    if value and isinstance(value, str):
                        # Buscar tokens JWT directamente
                        if value.startswith('eyJ') and '.' in value:
                            bearer_token = value
                            print(f"[AUTH] Token encontrado directamente en localStorage: {key}")
                            break
                        
                        # Intentar parsear como JSON y buscar tokens dentro
                        try:
                            parsed = json.loads(value)
                            if isinstance(parsed, dict):
                                # Buscar el token en diferentes posibles claves
                                for token_key in ['token', 'accessToken', 'access_token', 'bearerToken', 'bearer_token', 'jwt', 'authToken', 'auth_token']:
                                    if token_key in parsed:
                                        potential_token = parsed[token_key]
                                        if isinstance(potential_token, str) and potential_token.startswith('eyJ') and '.' in potential_token:
                                            bearer_token = potential_token
                                            print(f"[AUTH] Token encontrado en localStorage['{key}']['{token_key}']")
                                            break
                                
                                if bearer_token:
                                    break
                        except:
                            pass
            except Exception as e:
                print(f"[AUTH] Error al buscar en localStorage: {e}")
        
        # Método 4 PRIORITARIO: Extraer directamente de localStorage (más confiable)
        if not bearer_token:
            try:
                print("[AUTH] Intentando extraer token directamente de localStorage...")
                
                # Script para extraer el token de localStorage
                storage_script = """
                try {
                    // Intentar obtener de authentication
                    const auth = localStorage.getItem('authentication');
                    if (auth) {
                        const parsed = JSON.parse(auth);
                        if (parsed.token) {
                            return {success: true, token: parsed.token, source: 'localStorage.authentication'};
                        }
                    }
                    
                    // Intentar obtener directamente
                    const directToken = localStorage.getItem('token');
                    if (directToken && directToken.startsWith('eyJ')) {
                        return {success: true, token: directToken, source: 'localStorage.token'};
                    }
                    
                    // Buscar en todas las claves
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        const value = localStorage.getItem(key);
                        if (value && value.startsWith('eyJ') && value.split('.').length === 3) {
                            return {success: true, token: value, source: 'localStorage.' + key};
                        }
                    }
                    
                    return {success: false, error: 'No se encontró token en localStorage'};
                } catch (e) {
                    return {success: false, error: e.toString()};
                }
                """
                
                # Ejecutar el script
                result = driver.execute_script(storage_script)
                
                if result and result.get('success'):
                    bearer_token = result['token']
                    print(f"[AUTH] Token extraído exitosamente de {result['source']}")
                    print(f"[AUTH DEBUG] Token: {bearer_token[:50]}... (longitud: {len(bearer_token)})")
                else:
                    print(f"[AUTH] No se pudo extraer token de localStorage: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"[AUTH] Error al extraer token de localStorage: {e}")
        
        # VALIDAR el token extraído antes de devolverlo
        if bearer_token:
            print("[AUTH] Validando token extraido...")
            print(f"[AUTH DEBUG] Token a validar: {bearer_token[:50]}...")
            print(f"[AUTH DEBUG] Longitud del token: {len(bearer_token)} caracteres")
            
            # Verificar que el token tenga el formato JWT correcto (3 partes separadas por puntos)
            token_parts = bearer_token.count('.')
            if token_parts != 2:
                print(f"[AUTH WARNING] El token no tiene formato JWT válido (tiene {token_parts} puntos, debería tener 2)")
                print(f"[AUTH DEBUG] Token completo: {bearer_token}")
            
            # Esperar un poco más antes de validar para dar tiempo a que el token se active
            print("[AUTH] Esperando 3 segundos adicionales antes de validar...")
            time.sleep(3)
            
            # Validar temporalmente el token
            temp_validate_url = "https://webapi.leadpier.com/v1/api/stats/user/sources"
            temp_payload = {"limit": 1, "offset": 0, "periodFrom": "today", "periodTo": "today", "source": "BM5_1"}
            temp_headers = {
                "authorization": f"bearer {bearer_token}",  # lowercase como en el navegador
                "content-type": "application/json",
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "origin": "https://dash.leadpier.com",
                "referer": "https://dash.leadpier.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            
            # NUEVO MÉTODO: Hacer la petición desde el navegador directamente para validar
            try:
                print("[AUTH] Validando token haciendo request desde el navegador...")
                
                validation_script = """
                return fetch('https://webapi.leadpier.com/v1/api/stats/user/sources', {
                    method: 'POST',
                    headers: {
                        'authorization': 'bearer REPLACE_TOKEN',
                        'content-type': 'application/json',
                        'accept': 'application/json, text/plain, */*'
                    },
                    body: JSON.stringify({
                        limit: 1,
                        offset: 0,
                        periodFrom: 'today',
                        periodTo: 'today',
                        source: 'BM5_1'
                    })
                })
                .then(response => {
                    return {
                        status: response.status,
                        ok: response.ok,
                        statusText: response.statusText
                    };
                })
                .catch(error => {
                    return {
                        status: 0,
                        ok: false,
                        error: error.toString()
                    };
                });
                """.replace('REPLACE_TOKEN', bearer_token)
                
                browser_result = driver.execute_script(validation_script)
                
                if browser_result and browser_result.get('ok'):
                    print(f"[AUTH] Token validado exitosamente desde el navegador (Status: {browser_result.get('status')})")
                    return bearer_token
                else:
                    print(f"[AUTH] Validacion desde navegador fallo (Status: {browser_result.get('status', 'unknown')})")
            except Exception as e:
                print(f"[AUTH] Error al validar desde navegador: {e}")
            
            # Intentar SIN proxy primero
            try:
                print("[AUTH] Intentando validar SIN proxy con requests.post...")
                validate_response = requests.post(temp_validate_url, headers=temp_headers, 
                                                 data=json.dumps(temp_payload), timeout=10, 
                                                 proxies=None)
                if validate_response.status_code == 200:
                    print("[AUTH] Token validado exitosamente SIN proxy - Login exitoso")
                    return bearer_token
                else:
                    print(f"[AUTH] Validacion sin proxy fallo (Status: {validate_response.status_code})")
            except Exception as e:
                print(f"[AUTH] Error al validar sin proxy: {e}")
            
            # Si falla sin proxy, intentar CON proxy
            try:
                print("[AUTH] Intentando validar CON proxy...")
                validate_response = requests.post(temp_validate_url, headers=temp_headers, 
                                                 data=json.dumps(temp_payload), timeout=10, 
                                                 proxies=get_proxies())
                if validate_response.status_code == 200:
                    print("[AUTH] Token validado exitosamente CON proxy - Login exitoso")
                    return bearer_token
                else:
                    print(f"[AUTH] Validacion con proxy fallo (Status: {validate_response.status_code})")
                    print(f"[AUTH] Respuesta: {validate_response.text[:200]}")
            except Exception as e:
                print(f"[AUTH] Error al validar con proxy: {e}")
            
            # Si ambos fallan, intentar con cookies del navegador
            print("[AUTH] Token no valido solo. Intentando con cookies del navegador...")
            try:
                # Primero, extraer cookies ANTES del refresh
                cookies_before = driver.get_cookies()
                print(f"[AUTH DEBUG] Cookies antes del refresh: {len(cookies_before)}")
                
                # Asegurarse de estar en el dominio correcto para obtener cookies
                current_url = driver.current_url
                print(f"[AUTH DEBUG] URL actual: {current_url}")
                
                # Si no estamos en la página correcta, navegar allí
                if 'leadpier.com' not in current_url:
                    print("[AUTH] Navegando a leadpier.com para obtener cookies...")
                    driver.get("https://dash.leadpier.com/marketer-statistics/sources")
                    time.sleep(5)
                
                # Extraer todas las cookies del navegador
                cookies = driver.get_cookies()
                print(f"[AUTH DEBUG] Se encontraron {len(cookies)} cookies")
                
                # Si no hay cookies, intentar navegar a la página principal y obtenerlas
                if len(cookies) == 0:
                    print("[AUTH] No hay cookies, intentando navegar a página principal...")
                    driver.get("https://dash.leadpier.com/")
                    time.sleep(3)
                    cookies = driver.get_cookies()
                    print(f"[AUTH DEBUG] Cookies después de navegar a /: {len(cookies)}")
                
                # Si aún no hay cookies, es posible que el navegador esté en modo headless restrictivo
                if len(cookies) == 0:
                    print("[AUTH WARNING] No se capturaron cookies. Esto puede deberse a:")
                    print("[AUTH WARNING] - Modo headless con restricciones de seguridad")
                    print("[AUTH WARNING] - Cookies bloqueadas por el navegador")
                    
                    # Si estamos en headless, retornar None para reintentar sin headless
                    if headless:
                        print("[AUTH] Retornando None para reintentar sin headless...")
                        return None
                
                # Debug: mostrar todas las cookies
                if cookies:
                    for cookie in cookies[:5]:  # Mostrar las primeras 5
                        print(f"[AUTH DEBUG] Cookie: {cookie['name']} (domain: {cookie.get('domain', 'N/A')})")
                else:
                    print("[AUTH DEBUG] No se encontraron cookies - el navegador puede haber limpiado la sesion")
                
                # Crear un objeto session con las cookies
                session = requests.Session()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
                
                # Intentar validar con cookies + token
                print("[AUTH] Validando con token + cookies...")
                validate_response = session.post(
                    temp_validate_url, 
                    headers=temp_headers, 
                    data=json.dumps(temp_payload), 
                    timeout=10,
                    proxies=None  # Sin proxy para testing
                )
                
                if validate_response.status_code == 200:
                    print("[AUTH] Token validado exitosamente con cookies - Login exitoso")
                    print("[AUTH] NOTA: Este token requiere cookies de sesion para funcionar")
                    return bearer_token
                else:
                    print(f"[AUTH] Validacion con cookies fallo (Status: {validate_response.status_code})")
                    
                    # Debug: mostrar nombres de cookies
                    cookie_names = [c['name'] for c in cookies if 'leadpier' in c.get('domain', '').lower() or 'session' in c['name'].lower() or 'auth' in c['name'].lower()]
                    if cookie_names:
                        print(f"[AUTH DEBUG] Cookies relevantes: {cookie_names}")
                        
            except Exception as e:
                print(f"[AUTH] Error al intentar con cookies: {e}")
            
            # Buscar en localStorage, sessionStorage y extraer TODOS los JWT
            print("[AUTH] Buscando tokens JWT en localStorage y sessionStorage...")
            try:
                all_tokens = driver.execute_script("""
                    let tokens = [];
                    
                    // Función para buscar JWTs en un objeto
                    function findJWTs(obj, source) {
                        if (typeof obj === 'string') {
                            // Buscar patrones JWT (eyJ...)
                            const jwtPattern = /eyJ[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+/g;
                            const matches = obj.match(jwtPattern);
                            if (matches) {
                                matches.forEach(token => {
                                    tokens.push({source: source, token: token});
                                });
                            }
                        } else if (typeof obj === 'object' && obj !== null) {
                            Object.keys(obj).forEach(key => {
                                findJWTs(obj[key], source + '.' + key);
                            });
                        }
                    }
                    
                    // Buscar en localStorage
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        let value = localStorage.getItem(key);
                        try {
                            let parsed = JSON.parse(value);
                            findJWTs(parsed, 'localStorage.' + key);
                        } catch (e) {
                            findJWTs(value, 'localStorage.' + key);
                        }
                    }
                    
                    // Buscar en sessionStorage
                    for (let i = 0; i < sessionStorage.length; i++) {
                        let key = sessionStorage.key(i);
                        let value = sessionStorage.getItem(key);
                        try {
                            let parsed = JSON.parse(value);
                            findJWTs(parsed, 'sessionStorage.' + key);
                        } catch (e) {
                            findJWTs(value, 'sessionStorage.' + key);
                        }
                    }
                    
                    return tokens;
                """)
                
                print(f"[AUTH DEBUG] Se encontraron {len(all_tokens)} tokens JWT")
                
                # Probar cada token encontrado
                for token_info in all_tokens:
                    token = token_info['token']
                    source = token_info['source']
                    print(f"[AUTH DEBUG] Probando token de: {source}")
                    print(f"[AUTH DEBUG] Token: {token[:50]}...")
                    
                    # Validar este token
                    try:
                        validate_response = requests.post(
                            temp_validate_url, 
                            headers={
                                "Authorization": f"bearer {token}",
                                "Content-Type": "application/json",
                                "Accept": "application/json, text/plain, */*",
                                "Origin": "https://dash.leadpier.com",
                                "User-Agent": "Mozilla/5.0",
                            },
                            data=json.dumps(temp_payload), 
                            timeout=10,
                            proxies=None
                        )
                        
                        if validate_response.status_code == 200:
                            print(f"[AUTH] TOKEN VALIDO ENCONTRADO en: {source}")
                            return token
                        else:
                            print(f"[AUTH DEBUG] Token de {source} no valido (Status: {validate_response.status_code})")
                    except Exception as e:
                        print(f"[AUTH DEBUG] Error validando token de {source}: {e}")
                
                print("[AUTH] Ningun token JWT encontrado fue valido")
                
            except Exception as e:
                print(f"[AUTH] Error al buscar tokens JWT: {e}")
            
            print("[AUTH] No se pudo validar el token extraido - puede requerir autenticacion adicional")
            return None
        else:
            print("[AUTH] No se pudo extraer el bearer token")
            print("[AUTH] SUGERENCIA: Intenta ejecutar el script sin --headless para depurar")
            return None
            
    except Exception as e:
        print(f"[AUTH] Error durante el login automatico: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        if driver:
            print("[AUTH] Cerrando navegador...")
            driver.quit()


def update_env_bearer_token(new_token):
    """
    Actualiza el bearer token en el archivo enviorement.env
    
    Args:
        new_token (str): Nuevo bearer token
    """
    global LEADPIER_BEARER
    
    try:
        # IMPORTANTE: Limpiar el token de espacios y saltos de línea
        new_token = new_token.strip()
        
        print(f"\n[AUTH DEBUG] ========== ACTUALIZANDO TOKEN EN .ENV ==========")
        print(f"[AUTH DEBUG] Token a guardar: {new_token[:50]}...")
        print(f"[AUTH DEBUG] Longitud: {len(new_token)} caracteres")
        print(f"[AUTH DEBUG] Partes JWT: {new_token.count('.')} puntos")
        
        # Buscar el archivo enviorement.env en diferentes ubicaciones posibles
        possible_paths = [
            "enviorement.env",  # Si se ejecuta desde Mainteinance and Scaling
            "../Mainteinance and Scaling/enviorement.env",  # Si se ejecuta desde Post Id
            "Mainteinance and Scaling/enviorement.env",  # Si se ejecuta desde la raíz
            os.path.join(os.path.dirname(__file__), "enviorement.env"),  # Mismo directorio que leadpier_auth.py
        ]
        
        env_path = None
        for path in possible_paths:
            if os.path.exists(path):
                env_path = path
                break
        
        if not env_path:
            print("[AUTH] Error: No se pudo encontrar enviorement.env en ninguna ubicacion conocida")
            return False
        
        print(f"[AUTH DEBUG] Archivo encontrado: {env_path}")
        
        # Leer el archivo actual
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Comparar con el token actual si existe
        old_token = None
        for line in lines:
            if line.startswith('LEADPIER_BEARER='):
                old_token = line.replace('LEADPIER_BEARER=', '').strip()
                break
        
        if old_token:
            print(f"[AUTH DEBUG] Token anterior: {old_token[:50]}... (longitud: {len(old_token)})")
            if old_token == new_token:
                print(f"[AUTH DEBUG] ⚠️ El token nuevo es IDÉNTICO al anterior")
            else:
                print(f"[AUTH DEBUG] ✓ El token nuevo es DIFERENTE al anterior")
        
        # Buscar y reemplazar la línea del LEADPIER_BEARER
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('LEADPIER_BEARER='):
                lines[i] = f'LEADPIER_BEARER={new_token}\n'
                updated = True
                break
        
        # Si no existía la línea, agregarla
        if not updated:
            lines.append(f'LEADPIER_BEARER={new_token}\n')
        
        # Guardar el archivo
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"[AUTH DEBUG] ✓ Archivo guardado correctamente")
        
        # Verificar que se guardó correctamente leyendo de nuevo
        with open(env_path, 'r', encoding='utf-8') as f:
            verify_lines = f.readlines()
        
        saved_token = None
        for line in verify_lines:
            if line.startswith('LEADPIER_BEARER='):
                saved_token = line.replace('LEADPIER_BEARER=', '').strip()
                break
        
        if saved_token == new_token:
            print(f"[AUTH DEBUG] ✓ Verificación: Token guardado correctamente")
        else:
            print(f"[AUTH DEBUG] ✗ ERROR: Token guardado NO coincide")
            print(f"[AUTH DEBUG] Esperado: {new_token[:50]}...")
            print(f"[AUTH DEBUG] Guardado: {saved_token[:50]}...")
        
        print(f"[AUTH DEBUG] ================================================\n")
        
        # Actualizar variable global y recargar entorno
        LEADPIER_BEARER = new_token
        os.environ['LEADPIER_BEARER'] = new_token
        
        print(f"[AUTH] Token actualizado en {env_path}")
        return True
        
    except Exception as e:
        print(f"[AUTH] Error al actualizar enviorement.env: {e}")
        import traceback
        traceback.print_exc()
        return False


def ensure_leadpier_token():
    """Valida el token de Leadpier y lo renueva si es necesario"""
    global LEADPIER_BEARER
    
    print("[AUTH] Validando bearer token de Leadpier...")
    
    if validate_bearer_token():
        print("[AUTH] Token valido")
        return True
    
    print("[AUTH] Token invalido o expirado. Intentando login automatico...")
    
    if not LEADPIER_EMAIL or not LEADPIER_PASSWORD:
        print("[AUTH] ERROR: Credenciales no encontradas en enviorement.env")
        return False
    
    # Intentar con headless primero
    new_token = auto_login_leadpier(LEADPIER_EMAIL, LEADPIER_PASSWORD, headless=True)
    
    # Si falla con headless, intentar sin headless (puede ser problema de cookies o necesitar búsqueda más profunda)
    if not new_token:
        print("[AUTH] Login con headless fallo. Intentando con navegador visible...")
        print("[AUTH] NOTA: Se abrira una ventana del navegador por 15-20 segundos")
        new_token = auto_login_leadpier(LEADPIER_EMAIL, LEADPIER_PASSWORD, headless=False)
    
    if not new_token:
        # Mostrar instrucciones para actualización manual como último recurso
        print("\n" + "="*70)
        print("TOKEN DE LEADPIER EXPIRADO - ACTUALIZACION MANUAL REQUERIDA")
        print("="*70)
        print("\nEl login automatico fallo. Por favor, actualiza el token manualmente:")
        print("\nPASOS PARA OBTENER UN NUEVO TOKEN:")
        print("\n1. Abre tu navegador y ve a: https://dash.leadpier.com")
        print("2. Inicia sesion con tus credenciales")
        print("3. Presiona F12 para abrir Developer Tools")
        print("4. Ve a la pestaña 'Console' (Consola)")
        print("5. Copia y pega este comando y presiona Enter:")
        print("\n   JSON.parse(localStorage.getItem('authentication')).token")
        print("\n6. Copia el token que aparece (sin las comillas)")
        print("7. Abre el archivo: Mainteinance and Scaling/enviorement.env")
        print("8. Busca la linea que dice: LEADPIER_BEARER=...")
        print("9. Reemplaza el token viejo con el nuevo token")
        print("10. Guarda el archivo y ejecuta el script nuevamente")
        print("\n" + "="*70)
        print("\nNOTA: El script continuara SIN datos de Leadpier por ahora.")
        print("      Los adsets se gestionaran solo con datos de Facebook.")
        print("="*70 + "\n")
        return False
    
    print("[AUTH] Login exitoso. Actualizando token...")
    if update_env_bearer_token(new_token):
        LEADPIER_BEARER = new_token
        print("[AUTH] Token actualizado correctamente en el archivo")
        
        # VERIFICAR que el token guardado funciona
        print("[AUTH] Verificando que el token guardado funciona...")
        if validate_bearer_token():
            print("[AUTH] ✓ Token guardado y verificado exitosamente")
            return True
        else:
            print("[AUTH] ❌ ADVERTENCIA: El token se guardó pero NO pasa la validación")
            print("[AUTH] Esto puede indicar:")
            print("[AUTH]   - El token necesita cookies de sesión adicionales")
            print("[AUTH]   - El token fue capturado incorrectamente")
            print("[AUTH]   - Hay un problema con los headers de validación")
            print("\n[AUTH] RECOMENDACIÓN: Ejecuta 'python diagnostico_token.py' para más detalles")
            return False
    else:
        print("[AUTH] ERROR: No se pudo actualizar el token en el archivo")
        return False

