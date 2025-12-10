"""
Script rápido para ver el estado del sistema anti-bloqueo
"""
import os
import sys

def print_header():
    print("\n" + "="*70)
    print(" ESTADO DEL SISTEMA ANTI-BLOQUEO LEADPIER")
    print("="*70 + "\n")

def check_system():
    """Verifica el estado general del sistema"""
    
    # 1. Verificar imports
    print("📦 DEPENDENCIAS:")
    try:
        import undetected_chromedriver
        print("  ✓ undetected-chromedriver")
    except ImportError:
        print("  ✗ undetected-chromedriver (instalar: pip install undetected-chromedriver)")
        return False
    
    try:
        from leadpier_undetected_session import get_leadpier_session
        print("  ✓ leadpier_undetected_session")
    except ImportError:
        print("  ✗ leadpier_undetected_session")
        return False
    
    # 2. Monitor
    print("\n📊 MONITOR DE DETECCIÓN:")
    try:
        from detection_monitor import get_detection_monitor
        monitor = get_detection_monitor()
        stats = monitor.get_stats()
        
        print(f"  Peticiones totales: {stats['total_requests']}")
        print(f"  Tasa de éxito: {stats['success_rate']}%")
        print(f"  Fallos consecutivos: {stats['consecutive_failures']}")
        
        if stats['in_defensive_mode']:
            print(f"  ⚠️  MODO DEFENSIVO ACTIVO")
        else:
            print(f"  ✓ Modo normal")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    
    # 3. Caché
    print("\n💾 CACHÉ:")
    try:
        from leadpier_cache_manager import get_leadpier_cache
        cache = get_leadpier_cache()
        
        if cache.is_valid():
            print("  ✓ Caché válida disponible")
        else:
            print("  ⚠️  No hay caché válida")
        
        stats = cache.get_stats()
        print(f"  Entradas: {stats['valid_entries']}/{stats['total_entries']}")
        print(f"  Tamaño: {stats['total_size_mb']} MB")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    
    # 4. Cookies
    print("\n🍪 COOKIES:")
    try:
        from cookie_manager import get_leadpier_cookie_manager
        cookie_mgr = get_leadpier_cookie_manager()
        
        if cookie_mgr.is_valid():
            info = cookie_mgr.get_cookie_info('leadpier')
            print(f"  ✓ Cookies válidas ({info['count']} cookies)")
            print(f"  Edad: {info['age_hours']:.1f} horas")
            print(f"  Expiran en: {info['expires_in_hours']:.1f} horas")
        else:
            print("  ⚠️  No hay cookies válidas")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    
    # 5. Archivos
    print("\n📁 ARCHIVOS DEL SISTEMA:")
    base_dir = os.path.dirname(__file__)
    files = [
        "leadpier_cookies.pkl",
        "leadpier_cache.json",
        "detection_state.json",
        "cache_index.json"
    ]
    
    for filename in files:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size} bytes)")
        else:
            print(f"  ⚠️  {filename} (no existe)")
    
    return True

def main():
    print_header()
    
    if check_system():
        print("\n" + "="*70)
        print(" ✓ SISTEMA OPERATIVO")
        print("="*70)
        print("\nPara ejecutar: python leadpiertest1.py")
        print("Para más info: python test_anti_bloqueo.py")
    else:
        print("\n" + "="*70)
        print(" ✗ SISTEMA CON PROBLEMAS")
        print("="*70)
        print("\nInstalar dependencias: pip install -r requirements.txt")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrumpido")
    except Exception as e:
        print(f"\n\nError: {e}")

