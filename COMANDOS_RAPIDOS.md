# ⚡ COMANDOS RÁPIDOS - Sistema Anti-Bloqueo

Referencia rápida de comandos más usados.

---

## 🚀 EJECUCIÓN

### Ejecutar script principal:
```bash
python leadpiertest1.py
```

### Test completo del sistema:
```bash
python test_anti_bloqueo.py
```

---

## 📊 MONITOREO

### Ver estadísticas del monitor:
```bash
python -c "from detection_monitor import get_detection_monitor; get_detection_monitor().print_stats()"
```

### Ver estadísticas del caché:
```bash
python -c "from leadpier_cache_manager import get_leadpier_cache; get_leadpier_cache().manager.print_stats()"
```

### Ver info de cookies:
```bash
python -c "from cookie_manager import get_leadpier_cookie_manager; get_leadpier_cookie_manager().info()"
```

---

## 🧹 LIMPIEZA

### Limpiar caché:
```bash
python -c "from leadpier_cache_manager import get_leadpier_cache; get_leadpier_cache().clear()"
```

### Eliminar cookies:
```bash
python -c "from cookie_manager import get_leadpier_cookie_manager; get_leadpier_cookie_manager().delete()"
```

### Reset del monitor:
```bash
python -c "from detection_monitor import get_detection_monitor; get_detection_monitor().reset_stats()"
```

### Salir de modo defensivo:
```bash
python -c "from detection_monitor import get_detection_monitor; m = get_detection_monitor(); m.defensive_mode_until = None; m._save_state(); print('Modo defensivo desactivado')"
```

### Limpieza completa (reset total):
```bash
del leadpier_*.pkl
del leadpier_*.json
del detection_state.json
del cache_*.json
```

---

## 🔧 INSTALACIÓN

### Instalar dependencias:
```bash
pip install -r requirements.txt
```

### Instalar solo undetected-chromedriver:
```bash
pip install undetected-chromedriver
```

### Actualizar dependencias:
```bash
pip install --upgrade undetected-chromedriver selenium
```

---

## 🐛 TROUBLESHOOTING

### Verificar que todo está instalado:
```bash
python -c "import undetected_chromedriver; print('✓ UC instalado'); import selenium; print('✓ Selenium instalado')"
```

### Ver versión de Chrome:
```bash
chrome --version
```

### Test rápido de sesión:
```bash
python -c "from leadpier_undetected_session import get_leadpier_session; s = get_leadpier_session(); print('✓ Sesión OK')"
```

### Ver logs del último error:
```bash
python -c "from detection_monitor import get_detection_monitor; m = get_detection_monitor(); failures = m.get_recent_failures(60); print(f'Fallos últimos 60min: {len(failures)}'); [print(f) for f in failures[-5:]]"
```

---

## 📈 ANÁLISIS

### Tasa de éxito actual:
```bash
python -c "from detection_monitor import get_detection_monitor; stats = get_detection_monitor().get_stats(); print(f\"Tasa de éxito: {stats['success_rate']}%\")"
```

### Patrón de errores:
```bash
python -c "from detection_monitor import get_detection_monitor; pattern = get_detection_monitor().analyze_failure_pattern(); print(f\"Patrón: {pattern['pattern']}\"); print(f\"Severidad: {pattern['severity']}\"); print(f\"Recomendación: {pattern['recommendation']}\")"
```

### Uso de caché (hit rate):
```bash
python -c "from leadpier_cache_manager import get_leadpier_cache; stats = get_leadpier_cache().get_stats(); print(f\"Entradas válidas: {stats['valid_entries']}/{stats['total_entries']}\")"
```

---

## 🎮 TESTING

### Test individual de componentes:

```bash
# Test caché
python leadpier_cache_manager.py

# Test cookies
python cookie_manager.py

# Test monitor
python detection_monitor.py

# Test sesión
python leadpier_undetected_session.py

# Test completo
python test_anti_bloqueo.py
```

---

## ⚙️ CONFIGURACIÓN

### Cambiar TTL del caché (editar leadpier_undetected_session.py):
```python
cache_ttl = 600  # 10 minutos en lugar de 5
```

### Cambiar frecuencia de ejecución (editar leadpiertest1.py):
```python
schedule.every(15).minutes.do(revisar_con_jitter)  # 15 min en lugar de 10
```

### Desactivar headless para debug (editar leadpiertest1.py):
```python
session = get_leadpier_session(headless=False)  # Ver navegador
```

### Ajustar modo defensivo (editar detection_monitor.py):
```python
detection_threshold = 5  # 5 fallos en lugar de 3
cooldown_minutes = 60    # 60 min en lugar de 30
```

---

## 📱 ONE-LINERS ÚTILES

### Estado general del sistema:
```bash
python -c "from detection_monitor import get_detection_monitor; from leadpier_cache_manager import get_leadpier_cache; m = get_detection_monitor(); c = get_leadpier_cache(); print(f'Éxito: {m.get_stats()[\"success_rate\"]}% | Caché: {c.is_valid()} | Defensivo: {m.is_in_defensive_mode()}')"
```

### Forzar obtención de datos frescos:
```bash
python -c "from leadpier_cache_manager import get_leadpier_cache; from leadpier_undetected_session import get_leadpier_session; get_leadpier_cache().clear(); s = get_leadpier_session(); data = s.get_data(); print(f'Datos: {len(data.get(\"data\", []))} registros' if data else 'Error')"
```

### Verificar edad de cookies:
```bash
python -c "from cookie_manager import get_leadpier_cookie_manager; info = get_leadpier_cookie_manager().get_cookie_info('leadpier'); print(f'Edad: {info[\"age_hours\"]:.1f}h | Válidas: {info[\"is_valid\"]}' if info else 'No hay cookies')"
```

---

## 🔥 COMANDOS DE EMERGENCIA

### Si todo falla, reset completo:
```bash
# 1. Detener script si está corriendo (Ctrl+C)

# 2. Limpiar todo
del leadpier_*.pkl
del leadpier_*.json
del detection_state.json
del cache_*.json

# 3. Reset del monitor
python -c "from detection_monitor import get_detection_monitor; m = get_detection_monitor(); m.reset_stats(); m.defensive_mode_until = None; m._save_state()"

# 4. Reiniciar
python leadpiertest1.py
```

### Si Chrome no responde:
```bash
# Matar procesos de Chrome
taskkill /F /IM chrome.exe /T

# Limpiar caché de undetected-chromedriver
del %APPDATA%\undetected_chromedriver\undetected_chromedriver.exe

# Reiniciar script
python leadpiertest1.py
```

---

## 📖 DOCUMENTACIÓN COMPLETA

- `GUIA_USO_FINAL.md` - Guía completa de uso
- `IMPLEMENTACION_COMPLETA.md` - Detalles técnicos
- `RESUMEN_SISTEMA_ANTI_BLOQUEO.md` - Resumen ejecutivo
- `SOLUCION_BLOQUEO_LEADPIER.md` - Soluciones alternativas

---

## ✅ CHECKLIST DIARIO

```
□ Ejecutar: python leadpiertest1.py
□ Verificar tasa de éxito >95%
□ Confirmar que no está en modo defensivo
□ Revisar logs por errores inusuales
```

**Si todo está ✓ → No hacer nada, el sistema se auto-gestiona**

---

*Última actualización: Diciembre 10, 2025*

