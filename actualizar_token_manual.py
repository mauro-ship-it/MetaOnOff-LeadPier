"""
Script para actualizar el token de LeadPier manualmente
Facilita el proceso de copiar y pegar un token nuevo
"""
import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(__file__), "enviorement.env")
load_dotenv(dotenv_path=env_path)

LEADPIER_BEARER_ACTUAL = os.getenv("LEADPIER_BEARER")


def clear_screen():
    """Limpia la pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Imprime el encabezado"""
    print("\n" + "="*70)
    print(" ACTUALIZACIÓN MANUAL DE TOKEN LEADPIER")
    print("="*70 + "\n")


def print_instructions():
    """Imprime instrucciones detalladas"""
    print("📋 INSTRUCCIONES:")
    print()
    print("1. Abre tu navegador personal (Chrome, Firefox, Edge)")
    print("2. Ve a: https://dash.leadpier.com")
    print("3. Inicia sesión con tus credenciales")
    print("4. Una vez dentro, presiona F12 (Developer Tools)")
    print("5. Ve a la pestaña 'Console' (Consola)")
    print("6. Copia y pega este comando exacto:")
    print()
    print("   " + "-"*60)
    print("   JSON.parse(localStorage.getItem('authentication')).token")
    print("   " + "-"*60)
    print()
    print("7. Presiona Enter")
    print("8. El token aparecerá (empieza con 'eyJ')")
    print("9. Haz click derecho sobre el token → Copy string contents")
    print("10. Pégalo aquí cuando se te solicite")
    print()
    print("-"*70)


def validate_token_format(token):
    """Valida el formato básico del token"""
    if not token:
        return False, "Token vacío"
    
    # Limpiar espacios y comillas
    token = token.strip().strip('"').strip("'")
    
    # Verificar que empiece con eyJ (típico de JWT)
    if not token.startswith('eyJ'):
        return False, "Token no parece ser un JWT (debe empezar con 'eyJ')"
    
    # Verificar que tenga 3 partes
    parts = token.split('.')
    if len(parts) != 3:
        return False, f"Token JWT debe tener 3 partes, tiene {len(parts)}"
    
    # Verificar longitud razonable
    if len(token) < 100:
        return False, "Token muy corto, parece incompleto"
    
    if len(token) > 2000:
        return False, "Token muy largo, puede estar corrupto"
    
    return True, token


def decode_token_info(token):
    """Decodifica información del token"""
    try:
        import base64
        
        parts = token.split('.')
        payload = parts[1]
        
        # Agregar padding
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.b64decode(payload)
        data = json.loads(decoded)
        
        return data
    except Exception as e:
        return None


def test_token_api(token):
    """Prueba el token contra la API"""
    try:
        url = "https://webapi.leadpier.com/v1/api/user/getBalance"
        headers = {
            "authorization": f"bearer {token}",
            "content-type": "application/json",
            "accept": "application/json",
            "origin": "https://dash.leadpier.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "referer": "https://dash.leadpier.com/",
        }
        
        print("\n⏳ Validando token contra API de LeadPier...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✓ Token VÁLIDO - API respondió correctamente")
            try:
                data = response.json()
                balance = data.get('data', {}).get('balance', 'N/A')
                print(f"  Balance de cuenta: {balance}")
            except:
                pass
            return True
        elif response.status_code == 401:
            print("❌ Token INVÁLIDO - API rechazó el token (401)")
            return False
        elif response.status_code == 403:
            print("⚠️  Token rechazado con 403 (posible bloqueo de IP)")
            print("   El token puede ser válido pero hay restricciones de acceso")
            return None
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error al validar token: {e}")
        return None


def update_env_file(new_token):
    """Actualiza el archivo enviorement.env"""
    try:
        if not os.path.exists(env_path):
            print(f"❌ Error: No se encontró {env_path}")
            return False
        
        # Leer archivo actual
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Actualizar línea del token
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('LEADPIER_BEARER='):
                lines[i] = f'LEADPIER_BEARER={new_token}\n'
                updated = True
                break
        
        # Si no existía, agregar
        if not updated:
            lines.append(f'LEADPIER_BEARER={new_token}\n')
        
        # Guardar archivo
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"\n✓ Token actualizado en: {env_path}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error al actualizar archivo: {e}")
        return False


def show_comparison(old_token, new_token):
    """Muestra comparación entre token viejo y nuevo"""
    print("\n" + "="*70)
    print(" COMPARACIÓN DE TOKENS")
    print("="*70)
    
    if old_token:
        print(f"\n  Token ANTERIOR:")
        print(f"    Primeros 40 chars: {old_token[:40]}...")
        print(f"    Longitud: {len(old_token)} caracteres")
        
        old_data = decode_token_info(old_token)
        if old_data and 'expires' in old_data:
            try:
                expires = old_data['expires']
                if expires > 10000000000:
                    expires = expires / 1000000
                else:
                    expires = expires / 1000
                exp_date = datetime.fromtimestamp(expires)
                print(f"    Expiraba: {exp_date.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                pass
    else:
        print("\n  Token ANTERIOR: No había token configurado")
    
    print(f"\n  Token NUEVO:")
    print(f"    Primeros 40 chars: {new_token[:40]}...")
    print(f"    Longitud: {len(new_token)} caracteres")
    
    new_data = decode_token_info(new_token)
    if new_data and 'expires' in new_data:
        try:
            expires = new_data['expires']
            if expires > 10000000000:
                expires = expires / 1000000
            else:
                expires = expires / 1000
            exp_date = datetime.fromtimestamp(expires)
            now = datetime.now()
            time_left = exp_date - now
            print(f"    Expira: {exp_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Válido por: {time_left}")
        except:
            pass
    
    if old_token and old_token == new_token:
        print("\n  ⚠️  ADVERTENCIA: El token nuevo es IDÉNTICO al anterior")
        print("     Puede que hayas copiado el token viejo por error")
    
    print()


def main():
    """Función principal"""
    clear_screen()
    print_header()
    
    # Mostrar token actual si existe
    if LEADPIER_BEARER_ACTUAL:
        print("📌 Token actual encontrado en enviorement.env:")
        print(f"   Primeros 40 caracteres: {LEADPIER_BEARER_ACTUAL[:40]}...")
        print(f"   Longitud: {len(LEADPIER_BEARER_ACTUAL)} caracteres")
        
        # Decodificar info del token actual
        current_data = decode_token_info(LEADPIER_BEARER_ACTUAL)
        if current_data and 'expires' in current_data:
            try:
                expires = current_data['expires']
                if expires > 10000000000:
                    expires = expires / 1000000
                else:
                    expires = expires / 1000
                exp_date = datetime.fromtimestamp(expires)
                now = datetime.now()
                
                if now > exp_date:
                    print(f"   Estado: ❌ EXPIRADO (el {exp_date.strftime('%Y-%m-%d %H:%M:%S')})")
                else:
                    time_left = exp_date - now
                    print(f"   Estado: ✓ Válido (expira en {time_left})")
            except:
                pass
        print()
    else:
        print("⚠️  No hay token configurado actualmente en enviorement.env\n")
    
    print_instructions()
    
    # Solicitar nuevo token
    print("\n" + "="*70)
    print("Pega el token aquí (o 'q' para salir):")
    print("-"*70)
    
    try:
        user_input = input().strip()
        
        if user_input.lower() == 'q':
            print("\nCancelado por el usuario")
            return
        
        # Validar formato
        print("\n⏳ Validando formato del token...")
        is_valid, result = validate_token_format(user_input)
        
        if not is_valid:
            print(f"❌ Error: {result}")
            print("\nEl token no es válido. Asegúrate de:")
            print("  - Copiar el token completo")
            print("  - No incluir comillas extras")
            print("  - Que empiece con 'eyJ'")
            return
        
        new_token = result
        print("✓ Formato válido")
        print(f"  Longitud: {len(new_token)} caracteres")
        print(f"  Partes JWT: 3")
        
        # Decodificar información
        token_data = decode_token_info(new_token)
        if token_data:
            print("\n📋 Información del token:")
            for key, value in token_data.items():
                if key == 'expires':
                    try:
                        expires = value
                        if expires > 10000000000:
                            expires = expires / 1000000
                        else:
                            expires = expires / 1000
                        exp_date = datetime.fromtimestamp(expires)
                        print(f"  {key}: {exp_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
        
        # Probar token contra API
        api_result = test_token_api(new_token)
        
        if api_result == False:
            print("\n⚠️  ADVERTENCIA: El token no pasó la validación de API")
            print("\n¿Quieres guardarlo de todas formas? (s/n): ", end='')
            confirm = input().strip().lower()
            if confirm != 's':
                print("\nToken no guardado")
                return
        
        # Mostrar comparación
        show_comparison(LEADPIER_BEARER_ACTUAL, new_token)
        
        # Confirmar actualización
        print("="*70)
        print("¿Actualizar el token en enviorement.env? (s/n): ", end='')
        confirm = input().strip().lower()
        
        if confirm == 's':
            if update_env_file(new_token):
                print("\n" + "="*70)
                print(" ✓ TOKEN ACTUALIZADO EXITOSAMENTE")
                print("="*70)
                print("\nPuedes ejecutar tu script ahora:")
                print("  python leadpierget.py")
                print("  python scaling.py")
                print("  etc.")
                print()
            else:
                print("\n❌ No se pudo actualizar el archivo")
        else:
            print("\nToken no guardado")
    
    except KeyboardInterrupt:
        print("\n\nCancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError fatal: {e}")
        sys.exit(1)

