"""
Sistema de monitoreo y detección de bloqueos
Auto-ajusta la estrategia cuando detecta patrones sospechosos
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class DetectionMonitor:
    """
    Monitor de detección con auto-ajuste
    - Rastrea éxitos y fallos
    - Detecta patrones de bloqueo
    - Ajusta estrategia automáticamente
    - Persiste estado entre ejecuciones
    """
    
    def __init__(self, state_file=None, detection_threshold=3, cooldown_minutes=30):
        """
        Args:
            state_file: Archivo para persistir estado
            detection_threshold: Número de fallos antes de activar modo defensivo
            cooldown_minutes: Minutos de cooldown en modo defensivo
        """
        self.state_file = state_file or os.path.join(os.path.dirname(__file__), "detection_state.json")
        self.detection_threshold = detection_threshold
        self.cooldown_minutes = cooldown_minutes
        
        # Estado del monitor
        self.state = self._load_state()
        
        # Contadores
        self.failure_count = self.state.get('failure_count', 0)
        self.success_count = self.state.get('success_count', 0)
        self.total_requests = self.state.get('total_requests', 0)
        
        # Timestamps
        self.last_success = self.state.get('last_success')
        self.last_failure = self.state.get('last_failure')
        self.defensive_mode_until = self.state.get('defensive_mode_until')
        
        # Historial
        self.failure_history = self.state.get('failure_history', [])
        self.success_history = self.state.get('success_history', [])
    
    def _load_state(self) -> Dict:
        """Carga el estado desde disco"""
        if not os.path.exists(self.state_file):
            return {}
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[MONITOR] Error al cargar estado: {e}")
            return {}
    
    def _save_state(self):
        """Guarda el estado a disco"""
        try:
            state = {
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'total_requests': self.total_requests,
                'last_success': self.last_success,
                'last_failure': self.last_failure,
                'defensive_mode_until': self.defensive_mode_until,
                'failure_history': self.failure_history[-50:],  # Últimos 50
                'success_history': self.success_history[-50:],  # Últimos 50
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"[MONITOR] Error al guardar estado: {e}")
    
    def record_success(self, method="unknown"):
        """
        Registra un intento exitoso
        
        Args:
            method: Método usado para obtener datos
        """
        now = datetime.now().isoformat()
        
        self.success_count += 1
        self.total_requests += 1
        self.last_success = now
        self.failure_count = 0  # Reset de fallos consecutivos
        
        self.success_history.append({
            'timestamp': now,
            'method': method
        })
        
        self._save_state()
        
        # Salir de modo defensivo si estamos en él
        if self.is_in_defensive_mode():
            print("[MONITOR] ✓ Éxito detectado - saliendo de modo defensivo")
            self.defensive_mode_until = None
            self._save_state()
    
    def record_failure(self, error_type="unknown", error_message=""):
        """
        Registra un intento fallido
        
        Args:
            error_type: Tipo de error (401, 403, timeout, etc)
            error_message: Mensaje de error
        """
        now = datetime.now().isoformat()
        
        self.failure_count += 1
        self.total_requests += 1
        self.last_failure = now
        
        self.failure_history.append({
            'timestamp': now,
            'error_type': error_type,
            'error_message': error_message
        })
        
        self._save_state()
        
        # Verificar si debemos activar modo defensivo
        if self.failure_count >= self.detection_threshold:
            self.trigger_defensive_mode()
    
    def is_in_defensive_mode(self) -> bool:
        """Verifica si estamos en modo defensivo"""
        if not self.defensive_mode_until:
            return False
        
        try:
            until = datetime.fromisoformat(self.defensive_mode_until)
            return datetime.now() < until
        except:
            return False
    
    def trigger_defensive_mode(self):
        """Activa el modo defensivo"""
        cooldown_until = datetime.now() + timedelta(minutes=self.cooldown_minutes)
        self.defensive_mode_until = cooldown_until.isoformat()
        
        print("\n" + "="*70)
        print("⚠️  MODO DEFENSIVO ACTIVADO")
        print("="*70)
        print(f"Fallos consecutivos: {self.failure_count}")
        print(f"Activo hasta: {cooldown_until.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duración: {self.cooldown_minutes} minutos")
        print("\nAcciones automáticas:")
        print("  - Usar solo caché si disponible")
        print("  - Aumentar delays entre peticiones")
        print("  - Modo más sigiloso activado")
        print("="*70 + "\n")
        
        self._save_state()
    
    def get_defensive_delay(self) -> int:
        """Obtiene el delay recomendado en modo defensivo"""
        if not self.is_in_defensive_mode():
            return 0
        
        # Delay progresivo según fallos
        base_delay = 60  # 1 minuto base
        return base_delay * min(self.failure_count, 5)
    
    def should_skip_request(self) -> bool:
        """Determina si se debe saltar esta petición"""
        if not self.is_in_defensive_mode():
            return False
        
        # En modo defensivo, saltar si no hay caché
        return True
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del monitor"""
        success_rate = 0
        if self.total_requests > 0:
            success_rate = (self.success_count / self.total_requests) * 100
        
        return {
            'total_requests': self.total_requests,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': round(success_rate, 2),
            'consecutive_failures': self.failure_count,
            'in_defensive_mode': self.is_in_defensive_mode(),
            'defensive_mode_until': self.defensive_mode_until,
            'last_success': self.last_success,
            'last_failure': self.last_failure
        }
    
    def print_stats(self):
        """Imprime estadísticas del monitor"""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("ESTADÍSTICAS DEL MONITOR")
        print("="*70)
        print(f"Total de peticiones: {stats['total_requests']}")
        print(f"Exitosas: {stats['success_count']}")
        print(f"Fallidas: {stats['failure_count']}")
        print(f"Tasa de éxito: {stats['success_rate']}%")
        print(f"Fallos consecutivos: {stats['consecutive_failures']}")
        print(f"Modo defensivo: {'✓ ACTIVO' if stats['in_defensive_mode'] else '✗ Inactivo'}")
        
        if stats['in_defensive_mode']:
            try:
                until = datetime.fromisoformat(stats['defensive_mode_until'])
                remaining = until - datetime.now()
                minutes = int(remaining.total_seconds() / 60)
                print(f"  Activo por: {minutes} minutos más")
            except:
                pass
        
        if stats['last_success']:
            print(f"Último éxito: {stats['last_success']}")
        if stats['last_failure']:
            print(f"Último fallo: {stats['last_failure']}")
        
        print("="*70 + "\n")
    
    def get_recent_failures(self, minutes=60) -> List[Dict]:
        """Obtiene fallos recientes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        recent = []
        for failure in reversed(self.failure_history):
            try:
                timestamp = datetime.fromisoformat(failure['timestamp'])
                if timestamp > cutoff:
                    recent.append(failure)
            except:
                continue
        
        return recent
    
    def analyze_failure_pattern(self) -> Dict:
        """Analiza patrones en los fallos"""
        recent = self.get_recent_failures(60)
        
        if not recent:
            return {'pattern': 'none', 'severity': 'low'}
        
        # Contar tipos de error
        error_types = {}
        for failure in recent:
            error_type = failure.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Determinar patrón
        total = len(recent)
        
        if error_types.get('401', 0) > total * 0.5:
            return {'pattern': 'token_invalid', 'severity': 'high', 'recommendation': 'Renovar token'}
        
        if error_types.get('403', 0) > total * 0.5:
            return {'pattern': 'ip_blocked', 'severity': 'critical', 'recommendation': 'Cambiar IP o esperar'}
        
        if error_types.get('429', 0) > total * 0.3:
            return {'pattern': 'rate_limited', 'severity': 'medium', 'recommendation': 'Reducir frecuencia'}
        
        if error_types.get('timeout', 0) > total * 0.5:
            return {'pattern': 'connection_issues', 'severity': 'medium', 'recommendation': 'Verificar conexión'}
        
        if total >= 5:
            return {'pattern': 'multiple_errors', 'severity': 'high', 'recommendation': 'Modo defensivo'}
        
        return {'pattern': 'sporadic', 'severity': 'low', 'recommendation': 'Continuar monitoreando'}
    
    def reset_stats(self):
        """Reinicia las estadísticas (mantiene historial)"""
        self.failure_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.defensive_mode_until = None
        self._save_state()
        print("[MONITOR] Estadísticas reiniciadas")


# Instancia global
_global_monitor = None

def get_detection_monitor():
    """Obtiene la instancia global del monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = DetectionMonitor()
    return _global_monitor


if __name__ == "__main__":
    """Test del sistema de monitoreo"""
    print("\n" + "="*70)
    print(" TEST: Sistema de Monitoreo")
    print("="*70 + "\n")
    
    monitor = DetectionMonitor()
    
    # Test 1: Registrar éxitos
    print("Test 1: Registrar éxitos...")
    for i in range(5):
        monitor.record_success("undetected")
        time.sleep(0.1)
    print(f"✓ Éxitos registrados: {monitor.success_count}")
    
    # Test 2: Registrar fallos
    print("\nTest 2: Registrar fallos...")
    for i in range(3):
        monitor.record_failure("401", "Token inválido")
        time.sleep(0.1)
    
    if monitor.is_in_defensive_mode():
        print("✓ Modo defensivo activado correctamente")
    else:
        print("✗ Modo defensivo no se activó")
    
    # Test 3: Estadísticas
    print("\nTest 3: Estadísticas...")
    monitor.print_stats()
    
    # Test 4: Análisis de patrones
    print("\nTest 4: Análisis de patrones...")
    pattern = monitor.analyze_failure_pattern()
    print(f"Patrón detectado: {pattern['pattern']}")
    print(f"Severidad: {pattern['severity']}")
    print(f"Recomendación: {pattern['recommendation']}")
    
    # Test 5: Reset
    print("\nTest 5: Reset de estadísticas...")
    monitor.reset_stats()
    monitor.print_stats()
    
    print("\n" + "="*70)

