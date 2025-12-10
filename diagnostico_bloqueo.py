"""
Script de Diagnóstico Completo para Detectar Bloqueos de LeadPier
Identifica si el problema es: token, proxy, IP, rate limiting, o detección de automatización
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(__file__), "enviorement.env")
load_dotenv(dotenv_path=env_path)

LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")
LEADPIER_EMAIL = os.getenv("LEADPIER_EMAIL")
LEADPIER_PASSWORD = os.getenv("LEADPIER_PASSWORD")
PROXY_URL = os.getenv("PROXY_URL")


def print_section(title):
    """Imprime una sección con formato"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def test_1_token_format():
    """Verifica el formato del token JWT"""
    print_section("TEST 1: Formato del Token")
    
    if not LEADPIER_BEARER:
        print("❌ FALLO: Token no encontrado en enviorement.env")
        return False
    
    print(f"✓ Token encontrado")
    print(f"  Longitud: {len(LEADPIER_BEARER)} caracteres")
    print(f"  Primeros 20: {LEADPIER_BEARER[:20]}...")
    print(f"  Últimos 10: ...{LEADPIER_BEARER[-10:]}")
    
    # Verificar formato JWT
    parts = LEADPIER_BEARER.split('.')
    print(f"  Partes JWT: {len(parts)} (debe ser 3)")
    
    if len(parts) != 3:
        print("❌ FALLO: Token no tiene formato JWT válido")
        return False
    
    # Verificar espacios/caracteres extraños
    has_spaces = ' ' in LEADPIER_BEARER
    has_newlines = '\n' in LEADPIER_BEARER or '\r' in LEADPIER_BEARER
    
    if has_spaces or has_newlines:
        print("⚠️  ADVERTENCIA: Token contiene espacios o saltos de línea")
        return False
    
    print("✓ Formato del token es correcto")
    return True


def test_2_token_expiration():
    """Verifica si el token ha expirado"""
    print_section("TEST 2: Expiración del Token")
    
    if not LEADPIER_BEARER:
        print("❌ Token no disponible")
        return False
    
    try:
        import base64
        
        # Decodificar payload
        parts = LEADPIER_BEARER.split('.')
        payload = parts[1]
        
        # Agregar padding
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.b64decode(payload)
        payload_data = json.loads(decoded)
        
        print("✓ Token decodificado exitosamente")
        print(f"  Payload: {json.dumps(payload_data, indent=4)}")
        
        # Verificar expiración
        if 'expires' in payload_data:
            expires_timestamp = payload_data['expires']
            
            # Convertir a segundos (puede estar en microsegundos)
            if expires_timestamp > 10000000000:
                expires_timestamp = expires_timestamp / 1000000
            else:
                expires_timestamp = expires_timestamp / 1000
            
            expires_date = datetime.fromtimestamp(expires_timestamp)
            now = datetime.now()
            
            print(f"  Fecha de expiración: {expires_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Fecha actual: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if now > expires_date:
                print("❌ FALLO: Token EXPIRADO")
                time_diff = now - expires_date
                print(f"  Expiró hace: {time_diff}")
                return False
            else:
                time_left = expires_date - now
                print(f"✓ Token válido, expira en: {time_left}")
                return True
        else:
            print("⚠️  No se encontró fecha de expiración en el token")
            return True
            
    except Exception as e:
        print(f"⚠️  No se pudo decodificar token: {e}")
        return True  # No fallar el test, puede que el formato sea diferente


def test_3_api_without_proxy():
    """Prueba la API sin proxy"""
    print_section("TEST 3: Validación API sin Proxy")
    
    if not LEADPIER_BEARER:
        print("❌ Token no disponible")
        return False
    
    try:
        url = "https://webapi.leadpier.com/v1/api/user/getBalance"
        headers = {
            "authorization": f"bearer {LEADPIER_BEARER}",
            "content-type": "application/json",
            "accept": "application/json",
            "origin": "https://dash.leadpier.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "referer": "https://dash.leadpier.com/",
        }
        
        print("  Haciendo petición GET a /api/user/getBalance...")
        print("  Sin proxy...")
        
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=15, proxies=None)
        elapsed = time.time() - start_time
        
        print(f"  Status Code: {response.status_code}")
        print(f"  Tiempo de respuesta: {elapsed:.2f}s")
        print(f"  Headers de respuesta: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✓ Token VÁLIDO - API respondió correctamente")
            try:
                data = response.json()
                print(f"  Respuesta: {json.dumps(data, indent=4)[:500]}...")
            except:
                pass
            return True
        elif response.status_code == 401:
            print("❌ FALLO: Token INVÁLIDO (401 Unauthorized)")
            try:
                error = response.json()
                print(f"  Error: {error}")
            except:
                print(f"  Respuesta: {response.text[:200]}")
            return False
        elif response.status_code == 403:
            print("❌ FALLO: ACCESO PROHIBIDO (403 Forbidden)")
            print("  Posible bloqueo de IP o detección de bot")
            try:
                error = response.json()
                print(f"  Error: {error}")
            except:
                print(f"  Respuesta: {response.text[:200]}")
            return False
        elif response.status_code == 429:
            print("⚠️  RATE LIMITED (429 Too Many Requests)")
            print("  Demasiadas peticiones - espera 30-60 minutos")
            try:
                retry_after = response.headers.get('Retry-After', 'No especificado')
                print(f"  Retry-After: {retry_after}")
            except:
                pass
            return False
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            print(f"  Respuesta: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ FALLO: TIMEOUT - El servidor no respondió")
        print("  Posible bloqueo o problema de red")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ FALLO: ERROR DE CONEXIÓN")
        print("  No se pudo conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ FALLO: Error inesperado: {e}")
        return False


def test_4_api_with_proxy():
    """Prueba la API con proxy"""
    print_section("TEST 4: Validación API con Proxy")
    
    if not PROXY_URL:
        print("⚠️  Proxy no configurado - saltando test")
        return True
    
    if not LEADPIER_BEARER:
        print("❌ Token no disponible")
        return False
    
    try:
        url = "https://webapi.leadpier.com/v1/api/user/getBalance"
        headers = {
            "authorization": f"bearer {LEADPIER_BEARER}",
            "content-type": "application/json",
            "accept": "application/json",
            "origin": "https://dash.leadpier.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "referer": "https://dash.leadpier.com/",
        }
        
        proxies = {
            "http": PROXY_URL,
            "https": PROXY_URL
        }
        
        print(f"  Usando proxy: {PROXY_URL.split('@')[1] if '@' in PROXY_URL else PROXY_URL}")
        print("  Haciendo petición GET a /api/user/getBalance...")
        
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=15, proxies=proxies)
        elapsed = time.time() - start_time
        
        print(f"  Status Code: {response.status_code}")
        print(f"  Tiempo de respuesta: {elapsed:.2f}s")
        
        if response.status_code == 200:
            print("✓ Proxy funciona correctamente")
            return True
        elif response.status_code == 403:
            print("❌ FALLO: Proxy puede estar BLOQUEADO (403)")
            return False
        elif response.status_code == 407:
            print("❌ FALLO: Proxy requiere autenticación (407)")
            return False
        else:
            print(f"⚠️  Respuesta con proxy: {response.status_code}")
            return False
            
    except requests.exceptions.ProxyError:
        print("❌ FALLO: ERROR DE PROXY")
        print("  Proxy no está respondiendo o credenciales incorrectas")
        return False
    except requests.exceptions.Timeout:
        print("❌ FALLO: TIMEOUT con proxy")
        print("  Proxy muy lento o bloqueado")
        return False
    except Exception as e:
        print(f"❌ FALLO: Error con proxy: {e}")
        return False


def test_5_ip_info():
    """Obtiene información sobre la IP actual"""
    print_section("TEST 5: Información de IP")
    
    try:
        # Sin proxy
        print("  IP sin proxy:")
        response = requests.get("https://api.ipify.org?format=json", timeout=10)
        if response.status_code == 200:
            ip_data = response.json()
            print(f"    IP: {ip_data.get('ip', 'Unknown')}")
        
        # Con proxy (si existe)
        if PROXY_URL:
            print("\n  IP con proxy:")
            proxies = {"http": PROXY_URL, "https": PROXY_URL}
            response = requests.get("https://api.ipify.org?format=json", timeout=10, proxies=proxies)
            if response.status_code == 200:
                ip_data = response.json()
                print(f"    IP: {ip_data.get('ip', 'Unknown')}")
                
                # Información adicional
                try:
                    info_response = requests.get(f"http://ip-api.com/json/{ip_data['ip']}", timeout=10)
                    if info_response.status_code == 200:
                        info = info_response.json()
                        print(f"    País: {info.get('country', 'Unknown')}")
                        print(f"    Ciudad: {info.get('city', 'Unknown')}")
                        print(f"    ISP: {info.get('isp', 'Unknown')}")
                        print(f"    Tipo: {info.get('org', 'Unknown')}")
                        
                        # Detectar si es datacenter
                        org = info.get('org', '').lower()
                        isp = info.get('isp', '').lower()
                        if any(word in org or word in isp for word in ['datacenter', 'hosting', 'cloud', 'server']):
                            print("    ⚠️  ADVERTENCIA: IP parece ser de datacenter/hosting")
                            print("       (Es más fácil de detectar y bloquear)")
                except:
                    pass
        
        return True
        
    except Exception as e:
        print(f"  No se pudo obtener info de IP: {e}")
        return True


def test_6_check_selenium_detection():
    """Verifica si las técnicas anti-detección están disponibles"""
    print_section("TEST 6: Disponibilidad de Herramientas Anti-Detección")
    
    try:
        from selenium import webdriver
        print("✓ Selenium disponible")
    except ImportError:
        print("❌ Selenium NO disponible")
        print("   Instala con: pip install selenium")
        return False
    
    try:
        from selenium.webdriver.chrome.options import Options
        print("✓ Chrome WebDriver disponible")
    except ImportError:
        print("❌ Chrome WebDriver NO disponible")
        return False
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("✓ WebDriver Manager disponible")
    except ImportError:
        print("⚠️  WebDriver Manager NO disponible")
        print("   Instala con: pip install webdriver-manager")
    
    # Verificar si existe el archivo stealth
    stealth_path = os.path.join(os.path.dirname(__file__), "leadpier_auth_stealth.py")
    if os.path.exists(stealth_path):
        print(f"✓ Módulo stealth disponible: {stealth_path}")
    else:
        print("⚠️  Módulo stealth NO encontrado")
        print("   Debería estar en: leadpier_auth_stealth.py")
    
    return True


def test_7_credentials():
    """Verifica que las credenciales estén configuradas"""
    print_section("TEST 7: Verificación de Credenciales")
    
    all_ok = True
    
    if LEADPIER_EMAIL:
        print(f"✓ Email configurado: {LEADPIER_EMAIL}")
    else:
        print("❌ Email NO configurado en enviorement.env")
        all_ok = False
    
    if LEADPIER_PASSWORD:
        print(f"✓ Password configurado: {'*' * len(LEADPIER_PASSWORD)}")
    else:
        print("❌ Password NO configurado en enviorement.env")
        all_ok = False
    
    if LEADPIER_BEARER:
        print(f"✓ Bearer token configurado")
    else:
        print("⚠️  Bearer token NO configurado")
        print("   (Se puede obtener mediante login automático)")
    
    if PROXY_URL:
        # Ocultar credenciales del proxy
        proxy_display = PROXY_URL.split('@')[1] if '@' in PROXY_URL else PROXY_URL
        print(f"✓ Proxy configurado: {proxy_display}")
    else:
        print("⚠️  Proxy NO configurado (opcional)")
    
    return all_ok


def generate_report(results):
    """Genera reporte final con recomendaciones"""
    print_section("REPORTE FINAL")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nTests completados: {passed}/{total} exitosos\n")
    
    # Mostrar resultados
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    # Diagnóstico y recomendaciones
    print("\n" + "-"*70)
    print("DIAGNÓSTICO Y RECOMENDACIONES")
    print("-"*70 + "\n")
    
    # Escenario 1: Token inválido o expirado
    if not results.get('Token Format', True) or not results.get('Token Expiration', True):
        print("🔴 PROBLEMA: Token inválido o expirado")
        print("\n   SOLUCIÓN:")
        print("   1. Extrae token manualmente de tu navegador")
        print("   2. O ejecuta: python leadpier_auth_stealth.py")
        print("   3. Lee: SOLUCION_BLOQUEO_LEADPIER.md (Solución 2)")
        print()
    
    # Escenario 2: API falla sin proxy pero token OK
    if results.get('Token Format', True) and not results.get('API Without Proxy', True):
        print("🔴 PROBLEMA: Token rechazado por la API")
        print("\n   POSIBLES CAUSAS:")
        print("   - IP bloqueada")
        print("   - Rate limiting activo")
        print("   - Detección de bot")
        print("\n   SOLUCIÓN:")
        print("   1. Espera 30-60 minutos")
        print("   2. Intenta con VPN o IP diferente")
        print("   3. Usa extracción manual (más segura)")
        print("   4. Lee: SOLUCION_BLOQUEO_LEADPIER.md (Solución 1)")
        print()
    
    # Escenario 3: API funciona sin proxy pero falla con proxy
    if results.get('API Without Proxy', True) and not results.get('API With Proxy', True):
        print("🟡 PROBLEMA: Proxy está bloqueado")
        print("\n   SOLUCIÓN:")
        print("   1. Desactiva el proxy en enviorement.env")
        print("   2. O consigue un proxy residencial (no datacenter)")
        print("   3. Lee: SOLUCION_BLOQUEO_LEADPIER.md (Solución 3)")
        print()
    
    # Escenario 4: Todo funciona
    if all(results.values()):
        print("🟢 TODO FUNCIONA CORRECTAMENTE")
        print("\n   Tu configuración está bien.")
        print("   Si tienes problemas intermitentes:")
        print("   - Implementa rate limiting (espera entre peticiones)")
        print("   - Usa caché para reducir peticiones")
        print()
    
    # Escenario 5: No hay credenciales
    if not results.get('Credentials', True):
        print("🔴 PROBLEMA: Credenciales faltantes")
        print("\n   SOLUCIÓN:")
        print("   1. Completa el archivo enviorement.env")
        print("   2. Asegúrate de incluir:")
        print("      - LEADPIER_EMAIL")
        print("      - LEADPIER_PASSWORD")
        print("      - LEADPIER_BEARER (o se obtendrá automáticamente)")
        print()
    
    print("-"*70)
    print("\n📖 Para más información detallada, lee:")
    print("   SOLUCION_BLOQUEO_LEADPIER.md")
    print()


def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*70)
    print(" DIAGNÓSTICO DE BLOQUEO LEADPIER")
    print(" " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*70)
    
    results = {}
    
    # Ejecutar tests en orden
    try:
        results['Token Format'] = test_1_token_format()
        results['Token Expiration'] = test_2_token_expiration()
        results['API Without Proxy'] = test_3_api_without_proxy()
        results['API With Proxy'] = test_4_api_with_proxy()
        results['IP Info'] = test_5_ip_info()
        results['Anti-Detection Tools'] = test_6_check_selenium_detection()
        results['Credentials'] = test_7_credentials()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnóstico interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado durante diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Generar reporte
    generate_report(results)
    
    # Preguntar si quiere probar el login stealth
    if not results.get('API Without Proxy', True):
        print("\n¿Quieres intentar login con técnicas anti-detección ahora? (s/n): ", end='')
        try:
            response = input().strip().lower()
            if response == 's':
                print("\nEjecutando login stealth...")
                try:
                    from leadpier_auth_stealth import ensure_leadpier_token_stealth
                    result = ensure_leadpier_token_stealth()
                    if result:
                        print("\n✓ Login stealth exitoso - token renovado")
                    else:
                        print("\n✗ Login stealth falló - revisa los logs arriba")
                except Exception as e:
                    print(f"\n✗ Error al ejecutar login stealth: {e}")
        except:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnóstico cancelado")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError fatal: {e}")
        sys.exit(1)

