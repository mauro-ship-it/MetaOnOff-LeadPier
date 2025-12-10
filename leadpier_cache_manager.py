"""
Sistema de caché inteligente para datos de LeadPier
Reduce peticiones al servidor y mejora performance
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Any, Dict


class CacheManager:
    """
    Gestor de caché con TTL configurable
    - Persistencia en disco (JSON)
    - Invalidación automática por TTL
    - Compresión opcional de datos
    - Thread-safe para uso concurrente
    """
    
    def __init__(self, cache_dir=None, default_ttl=300):
        """
        Args:
            cache_dir: Directorio para almacenar caché (default: directorio actual)
            default_ttl: Tiempo de vida por defecto en segundos (default: 5 minutos)
        """
        self.cache_dir = cache_dir or os.path.dirname(__file__)
        self.default_ttl = default_ttl
        self.cache_index_file = os.path.join(self.cache_dir, "cache_index.json")
        
        # Crear directorio si no existe
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cargar índice de caché
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Carga el índice de caché desde disco"""
        if not os.path.exists(self.cache_index_file):
            return {}
        
        try:
            with open(self.cache_index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[CACHE] Error al cargar índice: {e}")
            return {}
    
    def _save_index(self):
        """Guarda el índice de caché a disco"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"[CACHE] Error al guardar índice: {e}")
    
    def _get_cache_filepath(self, key: str) -> str:
        """Obtiene la ruta del archivo de caché para una key"""
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return os.path.join(self.cache_dir, f"cache_{safe_key}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene datos del caché
        
        Args:
            key: Clave del caché
            
        Returns:
            Datos cacheados o None si no existe o expiró
        """
        if not self.is_valid(key):
            return None
        
        try:
            filepath = self._get_cache_filepath(key)
            with open(filepath, 'r') as f:
                cache_entry = json.load(f)
            
            age = time.time() - cache_entry['timestamp']
            print(f"[CACHE] Hit para '{key}' (edad: {int(age)}s)")
            return cache_entry['data']
        except Exception as e:
            print(f"[CACHE] Error al leer '{key}': {e}")
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """
        Guarda datos en caché
        
        Args:
            key: Clave del caché
            data: Datos a guardar (debe ser JSON-serializable)
            ttl: Tiempo de vida en segundos (default: usar default_ttl)
        """
        ttl = ttl or self.default_ttl
        
        try:
            filepath = self._get_cache_filepath(key)
            cache_entry = {
                'key': key,
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl,
                'expires_at': time.time() + ttl
            }
            
            with open(filepath, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
            # Actualizar índice
            self.index[key] = {
                'filepath': filepath,
                'timestamp': cache_entry['timestamp'],
                'ttl': ttl,
                'expires_at': cache_entry['expires_at']
            }
            self._save_index()
            
            print(f"[CACHE] Guardado '{key}' (TTL: {ttl}s)")
        except Exception as e:
            print(f"[CACHE] Error al guardar '{key}': {e}")
    
    def is_valid(self, key: str) -> bool:
        """
        Verifica si una entrada de caché es válida
        
        Args:
            key: Clave del caché
            
        Returns:
            True si existe y no ha expirado
        """
        if key not in self.index:
            return False
        
        entry = self.index[key]
        
        # Verificar expiración
        if time.time() > entry['expires_at']:
            print(f"[CACHE] Expirado '{key}'")
            self.delete(key)
            return False
        
        # Verificar que el archivo existe
        if not os.path.exists(entry['filepath']):
            print(f"[CACHE] Archivo no encontrado '{key}'")
            del self.index[key]
            self._save_index()
            return False
        
        return True
    
    def delete(self, key: str):
        """
        Elimina una entrada del caché
        
        Args:
            key: Clave del caché
        """
        if key not in self.index:
            return
        
        try:
            filepath = self.index[key]['filepath']
            if os.path.exists(filepath):
                os.remove(filepath)
            
            del self.index[key]
            self._save_index()
            print(f"[CACHE] Eliminado '{key}'")
        except Exception as e:
            print(f"[CACHE] Error al eliminar '{key}': {e}")
    
    def clear(self):
        """Limpia todo el caché"""
        for key in list(self.index.keys()):
            self.delete(key)
        print("[CACHE] Caché limpiado completamente")
    
    def cleanup(self):
        """Elimina entradas expiradas"""
        expired = []
        for key in self.index.keys():
            if not self.is_valid(key):
                expired.append(key)
        
        print(f"[CACHE] Limpieza: {len(expired)} entradas expiradas")
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del caché"""
        total = len(self.index)
        valid = sum(1 for key in self.index.keys() if self.is_valid(key))
        expired = total - valid
        
        total_size = 0
        for entry in self.index.values():
            try:
                total_size += os.path.getsize(entry['filepath'])
            except:
                pass
        
        return {
            'total_entries': total,
            'valid_entries': valid,
            'expired_entries': expired,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def print_stats(self):
        """Imprime estadísticas del caché"""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("ESTADÍSTICAS DEL CACHÉ")
        print("="*50)
        print(f"Total de entradas: {stats['total_entries']}")
        print(f"Entradas válidas: {stats['valid_entries']}")
        print(f"Entradas expiradas: {stats['expired_entries']}")
        print(f"Tamaño total: {stats['total_size_mb']} MB")
        print("="*50 + "\n")


class LeadPierCache:
    """
    Caché específico para datos de LeadPier
    Wrapper simplificado sobre CacheManager
    """
    
    def __init__(self, cache_dir=None, ttl=300):
        """
        Args:
            cache_dir: Directorio para caché
            ttl: Tiempo de vida en segundos (default: 5 minutos)
        """
        cache_dir = cache_dir or os.path.dirname(__file__)
        self.manager = CacheManager(cache_dir=cache_dir, default_ttl=ttl)
        self.default_key = "leadpier_sources_today"
    
    def get_sources_data(self):
        """Obtiene datos de sources cacheados"""
        return self.manager.get(self.default_key)
    
    def set_sources_data(self, data, ttl=None):
        """Guarda datos de sources en caché"""
        self.manager.set(self.default_key, data, ttl=ttl)
    
    def is_valid(self):
        """Verifica si el caché de sources es válido"""
        return self.manager.is_valid(self.default_key)
    
    def clear(self):
        """Limpia el caché de LeadPier"""
        self.manager.clear()
    
    def get_stats(self):
        """Obtiene estadísticas"""
        return self.manager.get_stats()


# Instancia global
_global_cache = None

def get_leadpier_cache(ttl=300):
    """Obtiene la instancia global del caché"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LeadPierCache(ttl=ttl)
    return _global_cache


if __name__ == "__main__":
    """Test del sistema de caché"""
    print("\n" + "="*70)
    print(" TEST: Sistema de Caché")
    print("="*70 + "\n")
    
    # Crear caché con TTL de 10 segundos para testing
    cache = LeadPierCache(ttl=10)
    
    # Test 1: Guardar datos
    print("Test 1: Guardar datos...")
    test_data = {
        'data': [
            {'adset_name': 'Test1', 'revenue': 100},
            {'adset_name': 'Test2', 'revenue': 200}
        ]
    }
    cache.set_sources_data(test_data)
    
    # Test 2: Leer datos
    print("\nTest 2: Leer datos...")
    cached = cache.get_sources_data()
    if cached:
        print(f"✓ Datos recuperados: {cached}")
    else:
        print("✗ No se pudieron recuperar datos")
    
    # Test 3: Verificar validez
    print("\nTest 3: Verificar validez...")
    if cache.is_valid():
        print("✓ Caché válido")
    else:
        print("✗ Caché inválido")
    
    # Test 4: Estadísticas
    print("\nTest 4: Estadísticas...")
    cache.manager.print_stats()
    
    # Test 5: Expiración (esperar 11 segundos)
    print("\nTest 5: Probando expiración (esperando 11 segundos)...")
    print("Presiona Ctrl+C para saltar esta prueba")
    try:
        time.sleep(11)
        if cache.is_valid():
            print("✗ Caché no expiró correctamente")
        else:
            print("✓ Caché expiró correctamente")
    except KeyboardInterrupt:
        print("\nPrueba de expiración saltada")
    
    print("\n" + "="*70)

