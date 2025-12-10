# Solución al Bloqueo de LeadPier

## 🚨 Problema Detectado

LeadPier parece estar bloqueando IPs o navegadores automatizados que intentan extraer el JWT, incluso cuando se hace manualmente.

## 📋 Señales de Bloqueo

1. ✅ Token funcionaba antes → ❌ Ahora falla (401/403)
2. ✅ Extracción manual funcionaba → ❌ Ahora también falla
3. Posibles errores:
   - Error 401: Unauthorized
   - Error 403: Forbidden
   - Error 429: Too Many Requests
   - Token extraído pero inválido inmediatamente

## 🔍 Causas Posibles

### 1. Detección de Automatización
- **Señales que detectan**: `navigator.webdriver = true`, headers sospechosos, timing no humano
- **Solución**: Usar `leadpier_auth_stealth.py` (ya creado)

### 2. Rate Limiting por IP
- **Señal**: Demasiadas peticiones en poco tiempo
- **Solución**: Esperar 30-60 minutos o cambiar IP

### 3. Proxy Blacklisteado
- **Tu proxy**: `62.216.66.90:29842`
- **Solución**: Probar sin proxy o con otro proxy

### 4. Fingerprinting del Navegador
- **Qué detectan**: Canvas, WebGL, fonts, timezone, screen resolution
- **Solución**: Usar perfil de navegador real (ver abajo)

### 5. Cookies/Session Tracking
- **Problema**: Token necesita cookies específicas de sesión
- **Solución**: Exportar cookies del navegador real

---

## 🛠️ SOLUCIONES (en orden de dificultad)

## ✅ SOLUCIÓN 1: Usar Autenticación Stealth (YA CREADA)

He creado `leadpier_auth_stealth.py` con técnicas anti-detección:

**Qué hace diferente:**
- ✓ Oculta propiedades de automatización (`navigator.webdriver`)
- ✓ Tipeo humano con delays variables
- ✓ Movimientos de mouse aleatorios
- ✓ Scrolls naturales
- ✓ Headers y user-agent realistas

**Cómo usar:**

```python
# En lugar de usar leadpier_auth.py
from leadpier_auth_stealth import ensure_leadpier_token_stealth

result = ensure_leadpier_token_stealth()
if result:
    print("Token renovado con éxito")
```

---

## ✅ SOLUCIÓN 2: Extraer Token Manualmente (SEGURO)

Si la automatización está bloqueada, extrae el token desde tu navegador personal:

### Pasos Detallados:

1. **Abre tu navegador PERSONAL** (no automatizado)
   - Chrome, Firefox, Edge - cualquiera que uses normalmente
   
2. **Navega a** https://dash.leadpier.com

3. **Inicia sesión normalmente**
   - Usa tus credenciales
   - Si hay CAPTCHA, resuélvelo
   
4. **Abre Developer Tools**
   - Presiona `F12` o click derecho → "Inspeccionar"
   
5. **Ve a la pestaña "Console"**

6. **Ejecuta este comando y presiona Enter:**
   ```javascript
   JSON.parse(localStorage.getItem('authentication')).token
   ```

7. **Copia el token** (aparecerá entre comillas)
   - Debe empezar con `eyJ...`
   - Debe tener unos 500-800 caracteres
   - Debe tener 2 puntos (3 partes)

8. **Pega el token en `enviorement.env`:**
   ```
   LEADPIER_BEARER=eyJhbGci....(tu token completo aquí)
   ```

9. **Guarda el archivo y ejecuta tu script**

### ⏱️ Duración del Token Manual
- Típicamente válido por 24-48 horas
- Tendrás que repetir este proceso cuando expire

---

## ✅ SOLUCIÓN 3: Desactivar Proxy Temporalmente

El proxy puede estar blacklisteado. Prueba sin él:

**Edita `enviorement.env`:**
```bash
# Comenta esta línea:
# PROXY_URL=http://mperez07:wV0mrWM4@62.216.66.90:29842

# O déjala vacía:
PROXY_URL=
```

**¿Por qué?**
- Los proxies públicos/compartidos suelen estar en blacklists
- LeadPier puede detectar que múltiples usuarios usan la misma IP del proxy

---

## ✅ SOLUCIÓN 4: Usar Perfil de Navegador Real

En lugar de un navegador vacío, usa tu perfil real de Chrome:

**Modifica `leadpier_auth_stealth.py`:**

```python
# En la función create_stealth_driver(), agrega:
chrome_options.add_argument(r"user-data-dir=C:\Users\mauro\AppData\Local\Google\Chrome\User Data")
chrome_options.add_argument("profile-directory=Default")
```

**⚠️ ADVERTENCIA:**
- Cierra todas las ventanas de Chrome antes de ejecutar el script
- Chrome no puede estar abierto cuando se usa el perfil

**Ventajas:**
- Tienes todas tus cookies reales
- LeadPier ve un navegador "conocido"
- Menos probabilidad de detección

---

## ✅ SOLUCIÓN 5: Usar Extensión de Chrome Real

Si LeadPier usa extensiones para validar, podemos simularlas:

**Crea este archivo: `manifest.json`**
```json
{
  "manifest_version": 3,
  "name": "Normal User",
  "version": "1.0",
  "description": "Extension to look like normal user"
}
```

**Carga la extensión en el navegador automatizado:**
```python
chrome_options.add_argument(f"--load-extension={ruta_a_la_carpeta_con_manifest}")
```

---

## ✅ SOLUCIÓN 6: Esperar y Rate Limit Propio

Si hay rate limiting temporal:

**Modifica tu script para:**
1. Hacer menos peticiones
2. Agregar delays más largos entre peticiones
3. Cachear resultados para no pedir datos repetidos

**Ejemplo:**
```python
import time

# Antes de cada petición a LeadPier
time.sleep(5)  # 5 segundos entre peticiones

# O usar caché
from functools import lru_cache

@lru_cache(maxsize=100)
def get_leadpier_data(adset_id, date):
    # Solo se ejecuta una vez por combinación de parámetros
    return fetch_data(adset_id, date)
```

---

## ✅ SOLUCIÓN 7: Usar API Key en Lugar de JWT (si existe)

**Verifica si LeadPier ofrece:**
- API Key permanente
- OAuth tokens
- Credenciales para integración

**Dónde buscar:**
- Settings → API
- Integrations
- Developer Settings
- Contactar soporte de LeadPier

---

## 🔍 DIAGNÓSTICO: ¿Cuál es MI problema?

Ejecuta este script de diagnóstico:

```bash
cd "Mainteinance and Scaling"
python diagnostico_bloqueo.py
```

---

## 📊 Tabla de Decisiones

| Síntoma | Causa Probable | Solución |
|---------|----------------|----------|
| Error 401 inmediato | Token expirado | Solución 1 o 2 |
| Error 403 después de funcionar | IP/Proxy bloqueado | Solución 3 |
| Error 429 | Rate limiting | Solución 6 |
| Token se extrae pero falla | Fingerprinting | Solución 4 o 5 |
| Extracción manual también falla | Bloqueo temporal de cuenta | Esperar 1-2 horas |
| CAPTCHA aparece | Anti-bot agresivo | Solución 2 (manual) |

---

## 🎯 RECOMENDACIÓN INMEDIATA

1. **PRIMERO**: Intenta extraer token manualmente (Solución 2) - 5 minutos
   - Si funciona → Problema es automatización
   
2. **SEGUNDO**: Prueba sin proxy (Solución 3) - 2 minutos
   - Si funciona → Problema es el proxy
   
3. **TERCERO**: Usa el script stealth (Solución 1) - 10 minutos
   - Si funciona → Problema era detección básica
   
4. **CUARTO**: Espera 30-60 minutos y reintenta - 0 minutos de trabajo
   - Si funciona → Era rate limiting temporal

---

## ⚠️ Señales de Bloqueo PERMANENTE

Si ves esto, puede que tu cuenta esté siendo monitoreada:

- ❌ CAPTCHA aparece SIEMPRE al hacer login
- ❌ Email de LeadPier sobre "actividad sospechosa"
- ❌ Token manual también falla después de 5 minutos
- ❌ No puedes acceder ni desde navegador personal

**Solución**: Contactar soporte de LeadPier explicando que es integración legítima

---

## 📝 Logs a Monitorear

Cuando ejecutes cualquier script, observa estos mensajes:

### ✅ BUENAS SEÑALES:
```
[AUTH] Token validado exitosamente
Status: 200
```

### ⚠️ ADVERTENCIAS:
```
Status: 429 (Rate limited - esperar)
Status: 401 (Token expirado - renovar)
```

### 🚨 SEÑALES DE BLOQUEO:
```
Status: 403 (Bloqueado - cambiar estrategia)
Connection refused
Timeout después de 30 segundos
CAPTCHA detectado en página
```

---

## 🔄 Plan B: Si TODO falla

### Opción 1: Reducir Frecuencia
- Ejecutar script 1 vez por hora (no cada 5 minutos)
- Usar caché agresivo
- Solo pedir datos cuando sea crítico

### Opción 2: Usar Headful Browser
- Abrir navegador visible
- Hacer login manual una vez al día
- Dejar script ejecutándose con esa sesión

### Opción 3: Browser Cookie Export
```python
# Exportar cookies del navegador real y usarlas
import pickle

# Guardar cookies
pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

# Cargar cookies
cookies = pickle.load(open("cookies.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)
```

### Opción 4: Selenium Grid con IP Rotativa
- Usar servicio como BrightData, Oxylabs
- IPs residenciales (no datacenter)
- Rotar IPs cada request

---

## 📞 ¿Necesitas Más Ayuda?

Si ninguna solución funciona:

1. **Ejecuta**: `python diagnostico_token.py`
2. **Captura**: Screenshot del error
3. **Anota**: Hora exacta cuando empezó a fallar
4. **Revisa**: Email de LeadPier por notificaciones

**Posibles causas externas:**
- LeadPier cambió su API
- Mantenimiento temporal
- Cambio en política de uso
- Cuenta bajo revisión

---

## 🚀 Próximos Pasos

1. Prueba **Solución 2** (manual) AHORA - es la más confiable
2. Mientras tanto, implementa **Solución 6** (rate limiting)
3. Para largo plazo, considera **Solución 7** (API oficial)

¿Qué solución quieres que implementemos primero?

