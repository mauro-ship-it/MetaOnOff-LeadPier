"""
Fix para ejecutar el sistema en Google Colab
Reemplaza las configuraciones de Chrome para que funcionen en Colab
"""

def get_colab_chrome_options():
    """Retorna opciones de Chrome optimizadas para Google Colab"""
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    
    # Opciones CRÍTICAS para Colab
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')  # NECESARIO en Colab
    options.add_argument('--disable-dev-shm-usage')  # NECESARIO en Colab
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-setuid-sandbox')
    
    # Opciones de performance
    options.add_argument('--single-process')
    options.add_argument('--no-zygote')
    
    # User agent realista
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Anti-detección
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Directorio temporal para perfil
    import tempfile
    options.add_argument(f'--user-data-dir={tempfile.mkdtemp()}')
    
    return options

def patch_leadpier_auth_for_colab():
    """Parchea leadpier_auth.py para funcionar en Colab"""
    import leadpier_auth
    
    # Guardar función original
    original_auto_login = leadpier_auth.auto_login_leadpier
    
    def colab_auto_login(email=None, password=None, headless=True):
        """Versión de auto_login adaptada para Colab"""
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        import os
        import time
        
        if not email:
            email = os.getenv('LEADPIER_EMAIL')
        if not password:
            password = os.getenv('LEADPIER_PASSWORD')
        
        print(f"[AUTH COLAB] Iniciando login para: {email}")
        print(f"[AUTH COLAB] Modo headless: {headless}")
        
        try:
            # Usar opciones de Colab
            options = get_colab_chrome_options()
            
            # Service para chromedriver
            service = Service('/usr/bin/chromedriver')
            
            print("[AUTH COLAB] Iniciando navegador...")
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            
            print("[AUTH COLAB] Navegando a login...")
            driver.get("https://dash.leadpier.com/login")
            time.sleep(3)
            
            print("[AUTH COLAB] Ingresando credenciales...")
            
            # Email
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
            )
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(1)
            
            # Password
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(1)
            
            # Submit
            print("[AUTH COLAB] Enviando formulario...")
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            # Esperar autenticación
            print("[AUTH COLAB] Esperando autenticación...")
            time.sleep(5)
            
            # Buscar token en localStorage
            print("[AUTH COLAB] Extrayendo token...")
            token = driver.execute_script("""
                try {
                    const auth = JSON.parse(localStorage.getItem('authentication'));
                    return auth ? auth.token : null;
                } catch (e) {
                    return null;
                }
            """)
            
            driver.quit()
            
            if token:
                print(f"[AUTH COLAB] ✅ Token obtenido exitosamente")
                return token
            else:
                print("[AUTH COLAB] ❌ No se pudo obtener el token")
                return None
                
        except Exception as e:
            print(f"[AUTH COLAB] ❌ Error: {e}")
            try:
                driver.quit()
            except:
                pass
            return None
    
    # Reemplazar función
    leadpier_auth.auto_login_leadpier = colab_auto_login
    print("✅ leadpier_auth parcheado para Colab")

def patch_undetected_session_for_colab():
    """Parchea leadpier_undetected_session.py para funcionar en Colab"""
    try:
        from leadpier_undetected_session import LeadPierUndetectedSession
        
        # Guardar método original
        original_create_driver = LeadPierUndetectedSession._create_undetected_driver
        
        def colab_create_driver(self):
            """Versión adaptada para Colab - usa Selenium estándar"""
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            print("[UNDETECTED COLAB] Usando Selenium estándar (Colab)")
            
            options = get_colab_chrome_options()
            service = Service('/usr/bin/chromedriver')
            
            driver = webdriver.Chrome(service=service, options=options)
            
            # Aplicar stealth
            self.setup_stealth(driver)
            
            return driver
        
        # Reemplazar método
        LeadPierUndetectedSession._create_undetected_driver = colab_create_driver
        print("✅ leadpier_undetected_session parcheado para Colab")
        
    except ImportError:
        print("⚠️ leadpier_undetected_session no disponible")

def apply_colab_patches():
    """Aplica todos los parches necesarios para Colab"""
    print("\n" + "="*70)
    print(" APLICANDO PARCHES PARA GOOGLE COLAB")
    print("="*70 + "\n")
    
    patch_leadpier_auth_for_colab()
    patch_undetected_session_for_colab()
    
    print("\n✅ Todos los parches aplicados")
    print("="*70 + "\n")

if __name__ == "__main__":
    apply_colab_patches()

