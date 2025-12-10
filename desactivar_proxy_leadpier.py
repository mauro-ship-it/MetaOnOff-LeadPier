"""
Script para desactivar el proxy en las peticiones a LeadPier
El proxy está bloqueado, pero el token es válido
"""
import os
import re

def comentar_proxy_en_archivo(filepath):
    """Comenta las líneas que usan proxy en peticiones a LeadPier"""
    if not os.path.exists(filepath):
        print(f"⚠️  Archivo no encontrado: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = 0
        
        # Patrón 1: requests.get/post con proxies=get_proxies()
        # Buscar peticiones a leadpier.com
        pattern1 = r'(requests\.(get|post)\([^)]*leadpier\.com[^)]*proxies=)get_proxies\(\)'
        if re.search(pattern1, content):
            content = re.sub(pattern1, r'\1None  # Proxy bloqueado por LeadPier', content)
            changes += len(re.findall(pattern1, original_content))
        
        # Patrón 2: Asignación de proxies antes de request
        pattern2 = r'(\s+)(proxies = get_proxies\(\))\s*\n\s*(response = requests\.(get|post)\([^)]*leadpier\.com)'
        if re.search(pattern2, content):
            content = re.sub(pattern2, r'\1# \2  # Proxy bloqueado por LeadPier\n\1proxies = None\n\1\3', content)
            changes += 1
        
        if content != original_content:
            # Hacer backup
            backup_path = filepath + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Guardar cambios
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ {os.path.basename(filepath)}: {changes} cambio(s) realizado(s)")
            print(f"  Backup guardado en: {os.path.basename(backup_path)}")
            return True
        else:
            print(f"⚠️  {os.path.basename(filepath)}: No se encontraron peticiones con proxy")
            return False
            
    except Exception as e:
        print(f"❌ Error al procesar {filepath}: {e}")
        return False


def main():
    print("\n" + "="*70)
    print(" DESACTIVAR PROXY PARA LEADPIER")
    print("="*70)
    print("\nEl diagnóstico mostró que el token es válido pero el proxy está")
    print("bloqueado. Este script desactivará el proxy solo para LeadPier.\n")
    
    script_dir = os.path.dirname(__file__)
    
    # Lista de archivos a modificar
    archivos = [
        os.path.join(script_dir, "leadpierget.py"),
        os.path.join(script_dir, "leadpiertest1.py"),
        os.path.join(script_dir, "leadpier_auth.py"),
        # Agregar otros archivos que usen LeadPier
    ]
    
    print("Archivos a modificar:")
    for archivo in archivos:
        if os.path.exists(archivo):
            print(f"  ✓ {os.path.basename(archivo)}")
        else:
            print(f"  ⚠️  {os.path.basename(archivo)} (no encontrado)")
    
    print("\n¿Continuar? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta != 's':
        print("\nCancelado por el usuario")
        return
    
    print("\nProcesando archivos...\n")
    
    modificados = 0
    for archivo in archivos:
        if comentar_proxy_en_archivo(archivo):
            modificados += 1
    
    print("\n" + "="*70)
    if modificados > 0:
        print(f"✓ {modificados} archivo(s) modificado(s) exitosamente")
        print("\nPuedes ejecutar tus scripts ahora:")
        print("  python leadpiertest1.py")
        print("  python leadpierget.py")
        print("\nSi algo sale mal, puedes restaurar desde los .backup")
    else:
        print("⚠️  No se modificaron archivos")
        print("\nPROCESO MANUAL:")
        print("1. Abre tus scripts de LeadPier")
        print("2. Busca las líneas con: proxies=get_proxies()")
        print("3. Cámbialo por: proxies=None")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelado por el usuario")
    except Exception as e:
        print(f"\n\nError: {e}")

