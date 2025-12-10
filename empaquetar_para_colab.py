"""
Script para empaquetar archivos necesarios para Google Colab o servidor
"""
import os
import zipfile
from datetime import datetime

# Archivos necesarios para ejecutar el sistema
ARCHIVOS_NECESARIOS = [
    'leadpiertest1.py',
    'leadpier_undetected_session.py',
    'leadpier_cache_manager.py',
    'cookie_manager.py',
    'detection_monitor.py',
    'leadpier_auth.py',
    'leadpier_auth_stealth.py',
    'leadpier_browser_session.py',
    'leadpier_colab_fix.py',  # FIX para Google Colab
    'enviorement.env',
    'requirements.txt',
]

# Archivos de documentación (opcionales)
ARCHIVOS_DOCUMENTACION = [
    'GUIA_USO_FINAL.md',
    'IMPLEMENTACION_COMPLETA.md',
    'RESUMEN_SISTEMA_ANTI_BLOQUEO.md',
    'COMANDOS_RAPIDOS.md',
    'GUIA_EJECUTAR_EN_NUBE.md',
    'RESUMEN_VIAJE.md',
    'README_SISTEMA_ANTI_BLOQUEO.md',
]

def crear_paquete():
    """Crear archivo ZIP con todos los archivos necesarios"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f'LeadPier_Sistema_Anti_Bloqueo_{timestamp}.zip'
    
    print(f"📦 Creando paquete: {zip_filename}\n")
    
    archivos_agregados = 0
    archivos_faltantes = []
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Agregar archivos necesarios
        print("✅ ARCHIVOS PRINCIPALES:")
        for archivo in ARCHIVOS_NECESARIOS:
            if os.path.exists(archivo):
                zipf.write(archivo)
                size = os.path.getsize(archivo)
                print(f"   ✓ {archivo} ({size:,} bytes)")
                archivos_agregados += 1
            else:
                print(f"   ✗ {archivo} (NO ENCONTRADO)")
                archivos_faltantes.append(archivo)
        
        # Agregar documentación
        print("\n📚 DOCUMENTACIÓN:")
        for archivo in ARCHIVOS_DOCUMENTACION:
            if os.path.exists(archivo):
                zipf.write(archivo)
                size = os.path.getsize(archivo)
                print(f"   ✓ {archivo} ({size:,} bytes)")
                archivos_agregados += 1
            else:
                print(f"   ⚠️  {archivo} (no encontrado, opcional)")
    
    # Resumen
    print("\n" + "="*70)
    print(f"✅ Paquete creado: {zip_filename}")
    print(f"📊 Total de archivos: {archivos_agregados}")
    
    if archivos_faltantes:
        print(f"\n⚠️  Archivos faltantes ({len(archivos_faltantes)}):")
        for archivo in archivos_faltantes:
            print(f"   - {archivo}")
    else:
        print("\n✓ Todos los archivos principales incluidos")
    
    # Tamaño total
    zip_size = os.path.getsize(zip_filename)
    print(f"\n📁 Tamaño del paquete: {zip_size:,} bytes ({zip_size/1024:.1f} KB)")
    
    # Instrucciones
    print("\n" + "="*70)
    print("📱 PRÓXIMOS PASOS:")
    print("\n1. PARA GOOGLE COLAB:")
    print(f"   - Sube {zip_filename} a tu Google Drive")
    print("   - O sube los archivos individuales en la celda 3 del notebook")
    print("\n2. PARA SERVIDOR (GCP/AWS/DigitalOcean):")
    print(f"   - Transfiere {zip_filename} al servidor")
    print("   - Descomprime: unzip {zip_filename}")
    print("   - Instala: pip install -r requirements.txt")
    print("   - Ejecuta: python leadpiertest1.py")
    print("\n3. VERIFICAR:")
    print("   - Asegúrate de editar enviorement.env con tus credenciales")
    print("="*70)

def main():
    print("="*70)
    print(" EMPAQUETADOR - Sistema Anti-Bloqueo LeadPier")
    print("="*70 + "\n")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('leadpiertest1.py'):
        print("❌ ERROR: No se encuentra leadpiertest1.py")
        print("   Ejecuta este script desde la carpeta 'Mainteinance and Scaling'")
        return
    
    crear_paquete()
    
    print("\n✅ ¡Paquete listo para subir a la nube!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelado por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

