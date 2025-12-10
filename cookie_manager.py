"""
Gestor de cookies para persistencia de sesiones
Permite guardar y restaurar cookies entre sesiones del navegador
"""
import os
import pickle
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class CookieManager:
    """
    Gestor de cookies con persistencia
    - Guarda cookies en disco
    - Valida edad de cookies
    - Filtra cookies por dominio
    - Gestiona expiración
    """
    
    def __init__(self, cookies_dir=None, max_age_hours=12):
        """
        Args:
            cookies_dir: Directorio para guardar cookies (default: directorio actual)
            max_age_hours: Edad máxima de cookies en horas (default: 12 horas)
        """
        self.cookies_dir = cookies_dir or os.path.dirname(__file__)
        self.max_age_hours = max_age_hours
        self.max_age_seconds = max_age_hours * 3600
        
        # Crear directorio si no existe
        os.makedirs(self.cookies_dir, exist_ok=True)
    
    def _get_filepath(self, identifier: str) -> str:
        """Obtiene la ruta del archivo de cookies"""
        safe_id = "".join(c if c.isalnum() else "_" for c in identifier)
        return os.path.join(self.cookies_dir, f"cookies_{safe_id}.pkl")
    
    def save_cookies(self, driver, identifier: str = "leadpier") -> bool:
        """
        Guarda las cookies del driver
        
        Args:
            driver: Instancia del WebDriver
            identifier: Identificador para el archivo de cookies
            
        Returns:
            True si se guardaron exitosamente
        """
        try:
            cookies = driver.get_cookies()
            filepath = self._get_filepath(identifier)
            
            # Agregar metadata
            cookie_data = {
                'cookies': cookies,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'count': len(cookies)
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(cookie_data, f)
            
            print(f"[COOKIES] Guardadas {len(cookies)} cookies para '{identifier}'")
            return True
        except Exception as e:
            print(f"[COOKIES] Error al guardar cookies: {e}")
            return False
    
    def load_cookies(self, driver, identifier: str = "leadpier", domain: str = None) -> bool:
        """
        Carga cookies al driver
        
        Args:
            driver: Instancia del WebDriver
            identifier: Identificador del archivo de cookies
            domain: Dominio específico a cargar (opcional)
            
        Returns:
            True si se cargaron exitosamente
        """
        filepath = self._get_filepath(identifier)
        
        if not os.path.exists(filepath):
            print(f"[COOKIES] No se encontró archivo de cookies para '{identifier}'")
            return False
        
        # Verificar edad
        if not self.are_cookies_valid(identifier):
            print(f"[COOKIES] Cookies de '{identifier}' expiradas")
            return False
        
        try:
            with open(filepath, 'rb') as f:
                cookie_data = pickle.load(f)
            
            cookies = cookie_data['cookies']
            loaded_count = 0
            failed_count = 0
            
            for cookie in cookies:
                # Filtrar por dominio si se especifica
                if domain and domain not in cookie.get('domain', ''):
                    continue
                
                try:
                    # Selenium requiere que estemos en el dominio correcto
                    driver.add_cookie(cookie)
                    loaded_count += 1
                except Exception as e:
                    failed_count += 1
            
            print(f"[COOKIES] Cargadas {loaded_count} cookies para '{identifier}' ({failed_count} fallidas)")
            return loaded_count > 0
        except Exception as e:
            print(f"[COOKIES] Error al cargar cookies: {e}")
            return False
    
    def are_cookies_valid(self, identifier: str = "leadpier") -> bool:
        """
        Verifica si las cookies son válidas (no expiradas)
        
        Args:
            identifier: Identificador del archivo de cookies
            
        Returns:
            True si existen y no han expirado
        """
        filepath = self._get_filepath(identifier)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            # Verificar edad del archivo
            file_age = time.time() - os.path.getmtime(filepath)
            
            if file_age > self.max_age_seconds:
                age_hours = file_age / 3600
                print(f"[COOKIES] Cookies expiradas (edad: {age_hours:.1f}h, máximo: {self.max_age_hours}h)")
                return False
            
            # Verificar que el contenido sea válido
            with open(filepath, 'rb') as f:
                cookie_data = pickle.load(f)
            
            if 'cookies' not in cookie_data or not cookie_data['cookies']:
                print(f"[COOKIES] Archivo de cookies vacío o corrupto")
                return False
            
            return True
        except Exception as e:
            print(f"[COOKIES] Error al validar cookies: {e}")
            return False
    
    def get_cookie_info(self, identifier: str = "leadpier") -> Optional[Dict]:
        """
        Obtiene información sobre las cookies guardadas
        
        Args:
            identifier: Identificador del archivo de cookies
            
        Returns:
            Diccionario con información o None si no existe
        """
        filepath = self._get_filepath(identifier)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'rb') as f:
                cookie_data = pickle.load(f)
            
            file_age = time.time() - os.path.getmtime(filepath)
            
            return {
                'identifier': identifier,
                'filepath': filepath,
                'count': cookie_data.get('count', 0),
                'saved_at': cookie_data.get('datetime', 'Unknown'),
                'age_seconds': int(file_age),
                'age_hours': round(file_age / 3600, 2),
                'is_valid': file_age < self.max_age_seconds,
                'expires_in_seconds': max(0, int(self.max_age_seconds - file_age)),
                'expires_in_hours': max(0, round((self.max_age_seconds - file_age) / 3600, 2))
            }
        except Exception as e:
            print(f"[COOKIES] Error al obtener info: {e}")
            return None
    
    def delete_cookies(self, identifier: str = "leadpier") -> bool:
        """
        Elimina archivo de cookies
        
        Args:
            identifier: Identificador del archivo de cookies
            
        Returns:
            True si se eliminó exitosamente
        """
        filepath = self._get_filepath(identifier)
        
        if not os.path.exists(filepath):
            print(f"[COOKIES] No existe archivo para '{identifier}'")
            return False
        
        try:
            os.remove(filepath)
            print(f"[COOKIES] Eliminadas cookies para '{identifier}'")
            return True
        except Exception as e:
            print(f"[COOKIES] Error al eliminar cookies: {e}")
            return False
    
    def cleanup_expired(self):
        """Elimina todos los archivos de cookies expirados"""
        deleted = 0
        
        try:
            for filename in os.listdir(self.cookies_dir):
                if filename.startswith("cookies_") and filename.endswith(".pkl"):
                    filepath = os.path.join(self.cookies_dir, filename)
                    file_age = time.time() - os.path.getmtime(filepath)
                    
                    if file_age > self.max_age_seconds:
                        os.remove(filepath)
                        deleted += 1
            
            if deleted > 0:
                print(f"[COOKIES] Limpieza: eliminados {deleted} archivos expirados")
        except Exception as e:
            print(f"[COOKIES] Error en limpieza: {e}")
    
    def print_info(self, identifier: str = "leadpier"):
        """Imprime información sobre las cookies"""
        info = self.get_cookie_info(identifier)
        
        if not info:
            print(f"\n[COOKIES] No hay cookies guardadas para '{identifier}'")
            return
        
        print("\n" + "="*50)
        print(f"INFORMACIÓN DE COOKIES: {identifier}")
        print("="*50)
        print(f"Cantidad: {info['count']} cookies")
        print(f"Guardadas: {info['saved_at']}")
        print(f"Edad: {info['age_hours']:.2f} horas")
        print(f"Estado: {'✓ Válidas' if info['is_valid'] else '✗ Expiradas'}")
        if info['is_valid']:
            print(f"Expiran en: {info['expires_in_hours']:.2f} horas")
        print("="*50 + "\n")


class LeadPierCookieManager(CookieManager):
    """
    Gestor de cookies específico para LeadPier
    Wrapper simplificado con configuración preestablecida
    """
    
    def __init__(self, cookies_dir=None):
        """
        Args:
            cookies_dir: Directorio para guardar cookies
        """
        cookies_dir = cookies_dir or os.path.dirname(__file__)
        super().__init__(cookies_dir=cookies_dir, max_age_hours=12)
        self.identifier = "leadpier"
        self.domain = "leadpier.com"
    
    def save(self, driver) -> bool:
        """Guarda cookies de LeadPier"""
        return self.save_cookies(driver, self.identifier)
    
    def load(self, driver) -> bool:
        """Carga cookies de LeadPier"""
        # Asegurar que estamos en el dominio correcto
        try:
            if self.domain not in driver.current_url:
                driver.get(f"https://dash.{self.domain}")
                time.sleep(1)
        except:
            pass
        
        return self.load_cookies(driver, self.identifier, self.domain)
    
    def is_valid(self) -> bool:
        """Verifica si las cookies de LeadPier son válidas"""
        return self.are_cookies_valid(self.identifier)
    
    def delete(self) -> bool:
        """Elimina cookies de LeadPier"""
        return self.delete_cookies(self.identifier)
    
    def info(self):
        """Imprime información de cookies de LeadPier"""
        return self.print_info(self.identifier)


# Instancia global
_global_cookie_manager = None

def get_leadpier_cookie_manager():
    """Obtiene la instancia global del gestor de cookies"""
    global _global_cookie_manager
    if _global_cookie_manager is None:
        _global_cookie_manager = LeadPierCookieManager()
    return _global_cookie_manager


if __name__ == "__main__":
    """Test del sistema de cookies"""
    print("\n" + "="*70)
    print(" TEST: Sistema de Cookies")
    print("="*70 + "\n")
    
    manager = LeadPierCookieManager()
    
    # Test 1: Verificar estado
    print("Test 1: Verificar cookies existentes...")
    if manager.is_valid():
        print("✓ Cookies válidas encontradas")
        manager.info()
    else:
        print("✗ No hay cookies válidas")
    
    # Test 2: Obtener información
    print("\nTest 2: Información detallada...")
    info = manager.get_cookie_info(manager.identifier)
    if info:
        print(f"Cookies guardadas: {info['count']}")
        print(f"Edad: {info['age_hours']:.2f} horas")
        print(f"Válidas: {info['is_valid']}")
    else:
        print("No hay información disponible")
    
    # Test 3: Limpieza
    print("\nTest 3: Limpieza de cookies expiradas...")
    manager.cleanup_expired()
    
    print("\n" + "="*70)
    print("NOTA: Para test completo, ejecutar desde un navegador activo")
    print("="*70 + "\n")

