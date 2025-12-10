"""
Módulo de sesión indetectable para LeadPier
Usa undetected-chromedriver con técnicas avanzadas anti-detección
"""
import os
import json
import time
import pickle
import atexit
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd

try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    print("[WARNING] undetected-chromedriver no disponible. Instalar con: pip install undetected-chromedriver")

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

LEADPIER_EMAIL = os.getenv("LEADPIER_EMAIL")
LEADPIER_PASSWORD = os.getenv("LEADPIER_PASSWORD")

# Importar monitor de detección
try:
    from detection_monitor import get_detection_monitor
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    print("[WARNING] detection_monitor no disponible")


class LeadPierUndetectedSession:
    """
    Sesión persistente e indetectable para LeadPier
    - Usa undetected-chromedriver
    - Modo headless por defecto
    - Caché de datos con TTL
    - Persistencia de cookies
    - Session keep-alive
    """
    
    _instance = None  # Singleton para reutilizar sesión
    
    def __init__(self, headless=True, cache_ttl=300):
        """
        Args:
            headless: Si True, ejecuta en modo headless
            cache_ttl: Tiempo de vida del caché en segundos (default: 5 minutos)
        """
        self.headless = headless
        self.driver = None
        self.session_active = False
        self.last_activity = None
        
        # Archivos de persistencia
        self.base_dir = os.path.dirname(__file__)
        self.cookies_file = os.path.join(self.base_dir, "leadpier_cookies.pkl")
        self.cache_file = os.path.join(self.base_dir, "leadpier_cache.json")
        self.cache_ttl = cache_ttl
        
        # Registrar cleanup al salir
        atexit.register(self.cleanup)
    
    @classmethod
    def get_instance(cls, headless=True):
        """Obtener instancia singleton"""
        if cls._instance is None:
            cls._instance = cls(headless=headless)
        return cls._instance
    
    def _create_undetected_driver(self):
        """Crea un driver indetectable con undetected-chromedriver"""
        if not UNDETECTED_AVAILABLE:
            raise ImportError("undetected-chromedriver no está instalado")
        
        print("[UNDETECTED] Creando driver indetectable...")
        
        # Fix para Windows Error 183 (archivo ya existe)
        import shutil
        uc_cache_dir = os.path.join(os.environ.get('APPDATA', ''), 'undetected_chromedriver')
        uc_exe_path = os.path.join(uc_cache_dir, 'undetected_chromedriver.exe')
        
        if os.path.exists(uc_exe_path):
            try:
                os.remove(uc_exe_path)
                print("[UNDETECTED] Limpieza preventiva de caché...")
            except:
                pass
        
        options = uc.ChromeOptions()
        
        # Modo headless con configuración avanzada
        if self.headless:
            options.add_argument("--headless=new")
            print("[UNDETECTED] Modo headless activado")
        
        # Configuraciones anti-detección
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # Window size para headless
        if self.headless:
            options.add_argument("--window-size=1920,1080")
        
        # User agent realista
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # Crear driver con undetected-chromedriver
            driver = uc.Chrome(options=options, version_main=120, use_subprocess=True)
            print("[UNDETECTED] Driver creado exitosamente")
            
            # Aplicar stealth adicional
            self._apply_stealth_scripts(driver)
            
            return driver
        except Exception as e:
            print(f"[UNDETECTED] Error al crear driver: {e}")
            raise
    
    def _apply_stealth_scripts(self, driver):
        """Aplica scripts avanzados de stealth y anti-detección"""
        try:
            # Script completo para ocultar automation y modificar fingerprints
            stealth_script = """
            // 1. Ocultar webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 2. Simular plugins realistas
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                    {name: 'Native Client', filename: 'internal-nacl-plugin'}
                ]
            });
            
            // 3. Agregar chrome runtime completo
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 4. Canvas fingerprint randomization avanzado
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {
                const imageData = originalGetImageData.apply(this, args);
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {
                    data[i] = data[i] + Math.floor(Math.random() * 3) - 1;
                    data[i+1] = data[i+1] + Math.floor(Math.random() * 3) - 1;
                    data[i+2] = data[i+2] + Math.floor(Math.random() * 3) - 1;
                }
                return imageData;
            };
            
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                if (type === 'image/png' && this.width === 16 && this.height === 16) {
                    return originalToDataURL.apply(this, ['image/png']);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // 5. WebGL fingerprint evasion avanzado
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) UHD Graphics 620';
                }
                if (parameter === 7936) {
                    return 'WebKit';
                }
                if (parameter === 7937) {
                    return 'WebKit WebGL';
                }
                return originalGetParameter.call(this, parameter);
            };
            
            // 6. AudioContext fingerprint protection
            const originalGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function(channel) {
                const data = originalGetChannelData.call(this, channel);
                for (let i = 0; i < data.length; i += 100) {
                    data[i] = data[i] + Math.random() * 0.0001;
                }
                return data;
            };
            
            // 7. Screen resolution consistency
            Object.defineProperty(screen, 'availWidth', {
                get: () => 1920
            });
            Object.defineProperty(screen, 'availHeight', {
                get: () => 1080
            });
            Object.defineProperty(screen, 'width', {
                get: () => 1920
            });
            Object.defineProperty(screen, 'height', {
                get: () => 1080
            });
            
            // 8. Timezone consistency
            Date.prototype.getTimezoneOffset = function() {
                return 240; // UTC-4
            };
            
            // 9. Language consistency
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'language', {
                get: () => 'en-US'
            });
            
            // 10. Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 11. Battery API spoofing
            if (navigator.getBattery) {
                const originalGetBattery = navigator.getBattery;
                navigator.getBattery = function() {
                    return originalGetBattery.call(this).then(battery => {
                        Object.defineProperty(battery, 'charging', { value: true });
                        Object.defineProperty(battery, 'level', { value: 1.0 });
                        return battery;
                    });
                };
            }
            
            // 12. Hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // 13. Device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // 14. Connection API
            if (navigator.connection) {
                Object.defineProperty(navigator.connection, 'rtt', {
                    get: () => 50
                });
                Object.defineProperty(navigator.connection, 'downlink', {
                    get: () => 10
                });
            }
            
            // 15. Media devices
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                navigator.mediaDevices.enumerateDevices = function() {
                    return originalEnumerateDevices.call(this).then(devices => {
                        return devices.map(device => ({
                            ...device,
                            deviceId: 'default',
                            groupId: 'default'
                        }));
                    });
                };
            }
            """
            
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": stealth_script
            })
            
            print("[UNDETECTED] Scripts avanzados de stealth aplicados (15 técnicas)")
        except Exception as e:
            print(f"[UNDETECTED] Error al aplicar stealth: {e}")
    
    def _create_fallback_driver(self):
        """Crea driver con selenium normal si undetected falla"""
        print("[FALLBACK] Usando Selenium estándar con stealth...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        return driver
    
    def get_driver(self):
        """Obtiene o crea el driver"""
        if self.driver and self.is_session_active():
            print("[UNDETECTED] Reutilizando sesión activa")
            return self.driver
        
        try:
            self.driver = self._create_undetected_driver()
        except Exception as e:
            print(f"[UNDETECTED] Fallando a selenium estándar: {e}")
            self.driver = self._create_fallback_driver()
        
        self.session_active = True
        self.last_activity = datetime.now()
        return self.driver
    
    def is_session_active(self):
        """Verifica si la sesión está activa"""
        if not self.driver:
            return False
        
        try:
            # Verificar que el driver responde
            self.driver.execute_script("return document.readyState")
            return True
        except:
            self.session_active = False
            return False
    
    def load_cookies(self):
        """Carga cookies guardadas si existen y son válidas"""
        if not os.path.exists(self.cookies_file):
            return False
        
        # Verificar edad de cookies (máximo 12 horas)
        age = time.time() - os.path.getmtime(self.cookies_file)
        if age > 43200:  # 12 horas
            print("[COOKIES] Cookies expiradas (más de 12 horas)")
            return False
        
        try:
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # Navegar a dominio primero
            self.driver.get("https://dash.leadpier.com")
            time.sleep(1)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"[COOKIES] Error al cargar cookie: {e}")
            
            print(f"[COOKIES] {len(cookies)} cookies cargadas")
            return True
        except Exception as e:
            print(f"[COOKIES] Error al cargar cookies: {e}")
            return False
    
    def save_cookies(self):
        """Guarda cookies actuales"""
        if not self.driver:
            return
        
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            print(f"[COOKIES] {len(cookies)} cookies guardadas")
        except Exception as e:
            print(f"[COOKIES] Error al guardar cookies: {e}")
    
    def get_cached_data(self):
        """Obtiene datos del caché si son válidos"""
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            # Verificar TTL
            cached_time = datetime.fromisoformat(cache['timestamp'])
            age = (datetime.now() - cached_time).total_seconds()
            
            if age < self.cache_ttl:
                print(f"[CACHE] Usando datos cacheados (edad: {int(age)}s)")
                return cache['data']
            else:
                print(f"[CACHE] Caché expirado (edad: {int(age)}s, TTL: {self.cache_ttl}s)")
                return None
        except Exception as e:
            print(f"[CACHE] Error al leer caché: {e}")
            return None
    
    def save_to_cache(self, data):
        """Guarda datos en caché"""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': data,
                'ttl': self.cache_ttl
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f)
            print("[CACHE] Datos guardados en caché")
        except Exception as e:
            print(f"[CACHE] Error al guardar caché: {e}")
    
    def do_login(self):
        """Realiza login en LeadPier"""
        driver = self.get_driver()
        
        try:
            print("[LOGIN] Navegando a login...")
            driver.get("https://dash.leadpier.com/login")
            time.sleep(3)
            
            # Intentar cargar cookies primero
            if self.load_cookies():
                # Verificar si el login persiste
                driver.get("https://dash.leadpier.com/marketer-statistics/sources")
                time.sleep(2)
                
                if '/login' not in driver.current_url:
                    print("[LOGIN] Login restaurado desde cookies")
                    return True
            
            # Si cookies no funcionan, hacer login manual
            print("[LOGIN] Haciendo login con credenciales...")
            driver.get("https://dash.leadpier.com/login")
            time.sleep(2)
            
            wait = WebDriverWait(driver, 30)
            
            # Llenar email
            email_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[placeholder*='email' i]"))
            )
            email_field.clear()
            email_field.send_keys(LEADPIER_EMAIL)
            
            # Llenar password
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(LEADPIER_PASSWORD)
            
            # Click login
            login_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            
            print("[LOGIN] Esperando autenticación...")
            time.sleep(5)
            
            # Verificar login exitoso
            for i in range(15):
                if '/login' not in driver.current_url:
                    print("[LOGIN] Login exitoso")
                    self.save_cookies()
                    return True
                time.sleep(1)
            
            print("[LOGIN] ERROR: Login falló")
            return False
            
        except Exception as e:
            print(f"[LOGIN] Error: {e}")
            return False
    
    def fetch_data(self):
        """Obtiene datos de LeadPier ejecutando fetch desde el navegador"""
        driver = self.get_driver()
        
        try:
            # Asegurar que estamos en la página correcta
            if '/marketer-statistics' not in driver.current_url:
                driver.get("https://dash.leadpier.com/marketer-statistics/sources")
                time.sleep(3)
            
            print("[DATA] Obteniendo datos de LeadPier...")
            
            # Script para hacer fetch desde el navegador
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
            
            if result.get('success'):
                print("[DATA] Datos obtenidos exitosamente")
                return result.get('data')
            else:
                print(f"[DATA] Error: {result.get('error')}")
                return None
                
        except Exception as e:
            print(f"[DATA] Error al obtener datos: {e}")
            return None
    
    def get_data(self):
        """
        Método principal para obtener datos con sistema de fallback multi-nivel
        Integrado con monitor de detección
        
        Fallback order:
        1. Caché (si válida)
        2. Sesión activa existente
        3. Nueva sesión con cookies guardadas
        4. Nueva sesión con login completo
        5. Selenium básico como último recurso
        """
        monitor = get_detection_monitor() if MONITOR_AVAILABLE else None
        
        # Verificar modo defensivo
        if monitor and monitor.is_in_defensive_mode():
            print("[DEFENSIVE] En modo defensivo - solo usando caché")
            cached = self.get_cached_data()
            if cached is not None:
                return cached
            
            delay = monitor.get_defensive_delay()
            print(f"[DEFENSIVE] No hay caché - esperando {delay}s antes de continuar")
            time.sleep(min(delay, 300))  # Máximo 5 minutos
        
        # Nivel 1: Intentar caché primero
        cached = self.get_cached_data()
        if cached is not None:
            if monitor:
                monitor.record_success("cache")
            return cached
        
        # Nivel 2: Sesión activa existente
        try:
            if self.is_session_active():
                print("[FALLBACK] Nivel 2: Usando sesión activa")
                data = self.fetch_data()
                if data:
                    self.save_to_cache(data)
                    self.last_activity = datetime.now()
                    if monitor:
                        monitor.record_success("active_session")
                    return data
        except Exception as e:
            print(f"[FALLBACK] Nivel 2 falló: {e}")
            if monitor:
                monitor.record_failure("session_error", str(e))
        
        # Nivel 3: Nueva sesión con cookies guardadas
        try:
            print("[FALLBACK] Nivel 3: Nueva sesión con cookies guardadas")
            self.get_driver()  # Crear driver si no existe
            
            if self.load_cookies():
                # Verificar que las cookies funcionan
                self.driver.get("https://dash.leadpier.com/marketer-statistics/sources")
                time.sleep(2)
                
                if '/login' not in self.driver.current_url:
                    print("[FALLBACK] Nivel 3: Cookies válidas, obteniendo datos")
                    data = self.fetch_data()
                    if data:
                        self.save_to_cache(data)
                        self.last_activity = datetime.now()
                        if monitor:
                            monitor.record_success("cookies")
                        return data
        except Exception as e:
            print(f"[FALLBACK] Nivel 3 falló: {e}")
            if monitor:
                monitor.record_failure("cookies_error", str(e))
        
        # Nivel 4: Nueva sesión con login completo
        try:
            print("[FALLBACK] Nivel 4: Login completo")
            if self.do_login():
                data = self.fetch_data()
                if data:
                    self.save_to_cache(data)
                    self.last_activity = datetime.now()
                    if monitor:
                        monitor.record_success("full_login")
                    return data
        except Exception as e:
            print(f"[FALLBACK] Nivel 4 falló: {e}")
            if monitor:
                monitor.record_failure("login_error", str(e))
        
        # Nivel 5: Último recurso - cerrar y reintentar con driver limpio
        try:
            print("[FALLBACK] Nivel 5: Reiniciando con driver limpio")
            self.close()
            time.sleep(2)
            
            self.get_driver()
            if self.do_login():
                data = self.fetch_data()
                if data:
                    self.save_to_cache(data)
                    self.last_activity = datetime.now()
                    if monitor:
                        monitor.record_success("clean_restart")
                    return data
        except Exception as e:
            print(f"[FALLBACK] Nivel 5 falló: {e}")
            if monitor:
                monitor.record_failure("restart_error", str(e))
        
        print("[FALLBACK] TODOS LOS NIVELES FALLARON")
        if monitor:
            monitor.record_failure("all_levels_failed", "Complete system failure")
        return None
    
    def keep_alive(self):
        """Mantiene la sesión activa con pequeña actividad"""
        if not self.is_session_active():
            return
        
        try:
            # Pequeña actividad para mantener sesión
            self.driver.execute_script("return document.readyState")
            self.last_activity = datetime.now()
        except Exception as e:
            print(f"[KEEP-ALIVE] Error: {e}")
            self.session_active = False
    
    def close(self):
        """Cierra la sesión y el driver"""
        if self.driver:
            try:
                print("[SESSION] Cerrando navegador...")
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                self.session_active = False
    
    def cleanup(self):
        """Limpieza al salir"""
        self.close()


# Instancia global singleton
_global_session = None

def get_leadpier_session(headless=True):
    """Obtiene la instancia global de la sesión"""
    global _global_session
    if _global_session is None:
        _global_session = LeadPierUndetectedSession.get_instance(headless=headless)
    return _global_session


def get_leadpier_data_undetected():
    """Función de conveniencia para obtener datos de LeadPier"""
    session = get_leadpier_session(headless=True)
    return session.get_data()


def process_leadpier_data(data):
    """Procesa los datos de LeadPier a DataFrame"""
    if not data or 'data' not in data:
        print("[PROCESS] No hay datos para procesar")
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
        print("[PROCESS] ADVERTENCIA: No se encontró columna de nombre de adset")
        return pd.DataFrame()
    
    # Convertir revenue a numérico
    if 'revenue' in df.columns:
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
    else:
        df['revenue'] = 0
    
    # Normalizar nombres
    df['adset_name_norm'] = df['adset_name'].str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
    
    print(f"[PROCESS] Procesados {len(df)} registros de LeadPier")
    return df[['adset_name', 'revenue', 'adset_name_norm']]


if __name__ == "__main__":
    """Test del módulo"""
    print("\n" + "="*70)
    print(" TEST: LeadPier Undetected Session")
    print("="*70 + "\n")
    
    session = get_leadpier_session(headless=True)
    
    print("Test 1: Obtener datos...")
    data = session.get_data()
    
    if data:
        df = process_leadpier_data(data)
        print(f"\n✓ Datos obtenidos: {len(df)} registros")
        print(df.head())
    else:
        print("\n✗ No se pudieron obtener datos")
    
    print("\n" + "="*70)

