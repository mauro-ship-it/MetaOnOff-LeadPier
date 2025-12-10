"""
Script de diagnóstico para comparar tokens de Leadpier
Ayuda a identificar diferencias entre el token manual y el automatizado
"""
import os
import json
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = os.path.join(os.path.dirname(__file__), "enviorement.env")
load_dotenv(dotenv_path=env_path)

LEADPIER_BEARER = os.getenv("LEADPIER_BEARER")

def analyze_token(token, label="Token"):
    """Analiza un token y muestra información detallada"""
    print(f"\n{'='*70}")
    print(f"{label.upper()}")
    print(f"{'='*70}")
    
    if not token:
        print("❌ Token vacío o None")
        return False
    
    # Información básica
    print(f"Longitud: {len(token)} caracteres")
    print(f"Primeros 50 caracteres: {token[:50]}")
    print(f"Últimos 20 caracteres: {token[-20:]}")
    print(f"Puntos (debe ser 2): {token.count('.')}")
    
    # Verificar formato JWT
    parts = token.split('.')
    print(f"\nPartes JWT: {len(parts)} (debe ser 3)")
    
    if len(parts) == 3:
        print(f"  - Header length: {len(parts[0])} caracteres")
        print(f"  - Payload length: {len(parts[1])} caracteres")
        print(f"  - Signature length: {len(parts[2])} caracteres")
        
        # Decodificar payload (sin verificar firma)
        try:
            import base64
            # Agregar padding si es necesario
            payload = parts[1]
            padding = 4 - (len(payload) % 4)
            if padding != 4:
                payload += '=' * padding
            
            decoded_payload = base64.b64decode(payload)
            payload_json = json.loads(decoded_payload)
            
            print(f"\n  Payload decodificado:")
            for key, value in payload_json.items():
                if key == 'expires':
                    # Convertir timestamp a fecha legible
                    from datetime import datetime
                    try:
                        # El timestamp parece estar en microsegundos
                        timestamp_seconds = value / 1000000 if value > 10000000000 else value / 1000
                        exp_date = datetime.fromtimestamp(timestamp_seconds)
                        print(f"    - {key}: {exp_date.strftime('%Y-%m-%d %H:%M:%S')} (timestamp: {value})")
                    except:
                        print(f"    - {key}: {value}")
                else:
                    print(f"    - {key}: {value}")
        except Exception as e:
            print(f"  ⚠️ No se pudo decodificar payload: {e}")
    
    # Verificar caracteres especiales
    has_spaces = ' ' in token
    has_newlines = '\n' in token or '\r' in token
    has_tabs = '\t' in token
    
    print(f"\nCaracteres especiales:")
    print(f"  - Espacios: {'❌ SÍ' if has_spaces else '✓ No'}")
    print(f"  - Saltos de línea: {'❌ SÍ' if has_newlines else '✓ No'}")
    print(f"  - Tabulaciones: {'❌ SÍ' if has_tabs else '✓ No'}")
    
    # Validar contra API
    print(f"\nValidación contra API:")
    try:
        url = "https://webapi.leadpier.com/v1/api/user/getBalance"
        headers = {
            "authorization": f"bearer {token}",
            "content-type": "application/json",
            "accept": "application/json",
            "origin": "https://dash.leadpier.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✓ Token VÁLIDO (Status: 200)")
            try:
                data = response.json()
                print(f"  Balance: {data.get('data', {}).get('balance', 'N/A')}")
            except:
                pass
            return True
        else:
            print(f"  ❌ Token INVÁLIDO (Status: {response.status_code})")
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('errorMessage', 'Unknown')}")
            except:
                print(f"  Respuesta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error al validar: {e}")
        return False

def compare_tokens(token1, token2):
    """Compara dos tokens y muestra las diferencias"""
    print(f"\n{'='*70}")
    print("COMPARACIÓN DE TOKENS")
    print(f"{'='*70}")
    
    if token1 == token2:
        print("✓ Los tokens son IDÉNTICOS")
        return
    
    print("❌ Los tokens son DIFERENTES")
    
    # Diferencias básicas
    print(f"\nLongitudes:")
    print(f"  Token 1: {len(token1)} caracteres")
    print(f"  Token 2: {len(token2)} caracteres")
    print(f"  Diferencia: {abs(len(token1) - len(token2))} caracteres")
    
    # Comparar caracter por caracter
    min_len = min(len(token1), len(token2))
    first_diff = None
    
    for i in range(min_len):
        if token1[i] != token2[i]:
            first_diff = i
            break
    
    if first_diff is not None:
        print(f"\nPrimera diferencia en posición: {first_diff}")
        start = max(0, first_diff - 10)
        end = min(min_len, first_diff + 10)
        print(f"  Token 1: ...{token1[start:end]}...")
        print(f"  Token 2: ...{token2[start:end]}...")
    
    # Comparar partes JWT
    parts1 = token1.split('.')
    parts2 = token2.split('.')
    
    if len(parts1) == 3 and len(parts2) == 3:
        print(f"\nComparación por partes:")
        for i, (p1, p2) in enumerate(zip(parts1, parts2)):
            part_name = ['Header', 'Payload', 'Signature'][i]
            if p1 == p2:
                print(f"  {part_name}: ✓ Idéntico")
            else:
                print(f"  {part_name}: ❌ Diferente (long1: {len(p1)}, long2: {len(p2)})")

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("DIAGNÓSTICO DE TOKEN LEADPIER")
    print("="*70)
    
    # Analizar token actual del .env
    print("\n1. ANALIZANDO TOKEN DEL ARCHIVO .ENV")
    token_valid = analyze_token(LEADPIER_BEARER, "Token del .env")
    
    # Solicitar token manual para comparar
    print("\n" + "="*70)
    print("COMPARACIÓN CON TOKEN MANUAL")
    print("="*70)
    print("\nPara comparar con un token que funcione manualmente:")
    print("1. Ve a https://dash.leadpier.com")
    print("2. Inicia sesión")
    print("3. Presiona F12 y ve a Console")
    print("4. Ejecuta: JSON.parse(localStorage.getItem('authentication')).token")
    print("5. Copia el token completo y pégalo aquí\n")
    
    manual_token = input("Pega el token manual aquí (o Enter para omitir): ").strip()
    
    if manual_token:
        print("\n2. ANALIZANDO TOKEN MANUAL")
        manual_valid = analyze_token(manual_token, "Token manual")
        
        # Comparar ambos tokens
        if LEADPIER_BEARER and manual_token:
            compare_tokens(LEADPIER_BEARER, manual_token)
        
        # Resumen
        print("\n" + "="*70)
        print("RESUMEN")
        print("="*70)
        print(f"Token .env: {'✓ VÁLIDO' if token_valid else '❌ INVÁLIDO'}")
        print(f"Token manual: {'✓ VÁLIDO' if manual_valid else '❌ INVÁLIDO'}")
        
        if not token_valid and manual_valid:
            print("\n❗ RECOMENDACIÓN: Actualiza el token del .env con el token manual")
            update = input("\n¿Quieres actualizar el archivo .env ahora? (s/n): ").strip().lower()
            if update == 's':
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    updated = False
                    for i, line in enumerate(lines):
                        if line.startswith('LEADPIER_BEARER='):
                            lines[i] = f'LEADPIER_BEARER={manual_token}\n'
                            updated = True
                            break
                    
                    if not updated:
                        lines.append(f'LEADPIER_BEARER={manual_token}\n')
                    
                    with open(env_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                    print("✓ Token actualizado exitosamente en el archivo .env")
                except Exception as e:
                    print(f"❌ Error al actualizar: {e}")
    else:
        print("\nComparación omitida")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
