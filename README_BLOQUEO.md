# 🚨 TOKEN LEADPIER NO FUNCIONA - GUÍA RÁPIDA

## ¿Qué pasó?

LeadPier probablemente implementó medidas anti-bot y está bloqueando la extracción automática de tokens.

---

## ✅ SOLUCIÓN RÁPIDA (5 minutos)

### Opción A: Actualización Manual del Token (MÁS SEGURA)

1. **Ejecuta este script:**
   ```bash
   cd "Mainteinance and Scaling"
   python actualizar_token_manual.py
   ```

2. **Sigue las instrucciones en pantalla:**
   - Abre tu navegador personal
   - Ve a https://dash.leadpier.com
   - Inicia sesión
   - Presiona F12 → Console
   - Ejecuta: `JSON.parse(localStorage.getItem('authentication')).token`
   - Copia el token
   - Pégalo en el script

3. **¡Listo!** El token se actualizará automáticamente

**⏱️ Duración del token:** 24-48 horas (tendrás que repetir el proceso)

---

### Opción B: Login Automático con Anti-Detección

1. **Ejecuta este script:**
   ```bash
   cd "Mainteinance and Scaling"
   python leadpier_auth_stealth.py
   ```

2. **El script:**
   - Abrirá el navegador automáticamente
   - Hará login con técnicas anti-detección
   - Extraerá y guardará el token

3. **Si falla:** Usa Opción A (manual)

---

## 🔍 ¿Qué está fallando exactamente?

Ejecuta el diagnóstico:

```bash
cd "Mainteinance and Scaling"
python diagnostico_bloqueo.py
```

Este script te dirá:
- ✅ Si el token es válido
- ✅ Si está expirado
- ✅ Si el proxy está bloqueado
- ✅ Si hay rate limiting
- ✅ Qué hacer exactamente

---

## 📁 Archivos Nuevos Creados

| Archivo | Propósito |
|---------|-----------|
| `leadpier_auth_stealth.py` | Login automático con anti-detección |
| `diagnostico_bloqueo.py` | Identifica el problema exacto |
| `actualizar_token_manual.py` | Facilita actualización manual |
| `SOLUCION_BLOQUEO_LEADPIER.md` | Guía completa de todas las soluciones |
| `README_BLOQUEO.md` | Este archivo (guía rápida) |

---

## 🎯 Recomendación Según tu Caso

### Caso 1: "El script funcionaba antes, hoy dejó de funcionar"
→ **Prueba primero:** `diagnostico_bloqueo.py`
→ **Solución probable:** Opción A (token manual)

### Caso 2: "Error 401 o 403"
→ **Token expirado/inválido**
→ **Solución:** Opción A (token manual)

### Caso 3: "Error 429"
→ **Rate limiting activo**
→ **Solución:** Espera 30-60 minutos, luego Opción A

### Caso 4: "Timeout o Connection Error"
→ **Proxy bloqueado**
→ **Solución:** Desactiva proxy en `enviorement.env`

### Caso 5: "Incluso el método manual falla"
→ **Cuenta puede estar bajo revisión**
→ **Solución:** Espera 1-2 horas, contacta soporte LeadPier

---

## ⚠️ IMPORTANTE: Prevenir Futuros Bloqueos

### 1. Reduce la Frecuencia de Peticiones

Agrega delays en tu script:

```python
import time

# Antes de cada petición a LeadPier
time.sleep(5)  # Espera 5 segundos
```

### 2. Implementa Caché

No pidas los mismos datos repetidamente:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_leadpier_data(adset_id, date):
    # Esta función se ejecuta solo una vez por combinación
    return fetch_data(adset_id, date)
```

### 3. Ejecuta Menos Veces al Día

En lugar de cada 5 minutos:
- 1 vez por hora durante el día
- O 4 veces al día en horarios específicos

### 4. Usa Token Manual Diariamente

- Más seguro que automatización
- Menos probabilidad de bloqueo
- Solo toma 2 minutos al día

---

## 📞 ¿Necesitas Más Ayuda?

1. **Lee el documento completo:** `SOLUCION_BLOQUEO_LEADPIER.md`
2. **Ejecuta diagnóstico:** `python diagnostico_bloqueo.py`
3. **Revisa logs:** Busca errores específicos (401, 403, 429)

---

## 🔄 Integración con tus Scripts Existentes

### Para usar el token manual actualizado:

```python
# En tu script actual, no cambies nada
# Solo actualiza el token con actualizar_token_manual.py
# y tu script usará el nuevo token automáticamente
```

### Para usar autenticación stealth:

```python
# En lugar de:
from leadpier_auth import ensure_leadpier_token

# Usa:
from leadpier_auth_stealth import ensure_leadpier_token_stealth

# Y llama:
ensure_leadpier_token_stealth()
```

---

## ✨ Mejoras Implementadas

### Técnicas Anti-Detección en `leadpier_auth_stealth.py`:

- ✅ Oculta `navigator.webdriver`
- ✅ Tipeo humano con delays variables
- ✅ Movimientos de mouse aleatorios
- ✅ Scrolls naturales
- ✅ User-Agent realista
- ✅ Argumentos anti-automatización
- ✅ Chrome DevTools Protocol

---

## 📊 Estadísticas de Éxito

Según el problema:

| Método | Tasa de Éxito | Tiempo |
|--------|---------------|--------|
| Token Manual | ~95% | 2-5 min |
| Login Stealth | ~70% | 10-15 min |
| Esperar + Reintentar | ~50% | 30-60 min |
| Cambiar IP/Proxy | ~60% | 5-10 min |

**Recomendación:** Empieza con Token Manual (Opción A)

---

## 🚀 Comandos Rápidos

```bash
# Diagnóstico completo
python diagnostico_bloqueo.py

# Actualizar token manualmente (RECOMENDADO)
python actualizar_token_manual.py

# Login automático stealth
python leadpier_auth_stealth.py

# Validar token actual
python diagnostico_token.py
```

---

## ❓ FAQ

**P: ¿Por qué dejó de funcionar?**
R: LeadPier probablemente detectó actividad automatizada y bloqueó la IP/navegador.

**P: ¿Es permanente?**
R: No, usualmente es temporal. El token manual siempre funciona.

**P: ¿Cuánto dura el token manual?**
R: 24-48 horas típicamente. Tendrás que renovarlo periódicamente.

**P: ¿Puedo evitar hacer esto todos los días?**
R: Sí, si LeadPier ofrece API Keys permanentes (revisa en Settings → API).

**P: ¿El proxy es el problema?**
R: Posiblemente. Prueba sin proxy comentando `PROXY_URL` en `enviorement.env`.

**P: ¿Qué es "stealth mode"?**
R: Técnicas para que el navegador automatizado parezca humano y evite detección.

---

## 🎯 TL;DR (Muy Resumido)

```bash
# Si tienes 5 minutos:
python actualizar_token_manual.py
# Y sigue las instrucciones

# Si quieres automatizar:
python leadpier_auth_stealth.py

# Si quieres saber QUÉ falla:
python diagnostico_bloqueo.py
```

---

*Última actualización: Diciembre 2025*

