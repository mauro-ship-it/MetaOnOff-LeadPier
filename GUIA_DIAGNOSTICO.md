# Guía de Diagnóstico: Token de Leadpier

## Problema Actual

La automatización captura un token pero no funciona, mientras que cuando actualizas el token manualmente sí funciona.

## Pasos para Diagnosticar

### Paso 1: Ejecutar el Script de Diagnóstico

```bash
cd "Mainteinance and Scaling"
python diagnostico_token.py
```

Este script te mostrará:
- ✅ Información detallada del token actual en el `.env`
- ✅ Si el token es válido o no
- ✅ Formato JWT (debe tener 3 partes)
- ✅ Caracteres especiales o errores de formato
- ✅ Comparación con un token manual que funcione

### Paso 2: Comparar Token Manual vs Automatizado

1. **Obtener token manual que funciona:**
   - Ve a https://dash.leadpier.com
   - Inicia sesión
   - Presiona F12 → Console
   - Ejecuta: `JSON.parse(localStorage.getItem('authentication')).token`
   - Copia el token completo

2. **Pegar el token en el script de diagnóstico**
   - El script te pedirá el token manual
   - Pégalo completo

3. **Revisar las diferencias:**
   - El script mostrará si son idénticos o diferentes
   - Si son diferentes, mostrará dónde está la diferencia
   - Si son idénticos pero uno funciona y otro no, el problema está en los headers o cookies

### Paso 3: Ejecutar la Automatización con Debug Extendido

```bash
cd "Mainteinance and Scaling"
python leadpierget.py  # o el script que uses
```

Busca en los logs:

#### ✅ Si ves esto, la automatización funcionó:
```
[AUTH] ✓ Token validado exitosamente desde el navegador!
[AUTH DEBUG] ========== TOKEN COMPLETO ==========
[AUTH DEBUG] eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[AUTH] Token funcional encontrado - omitiendo validación adicional
[AUTH] ✓ Token guardado y verificado exitosamente
```

#### ❌ Si ves esto, hay un problema:
```
[AUTH] ❌ ADVERTENCIA: El token se guardó pero NO pasa la validación
```

### Paso 4: Analizar el Token Capturado

Cuando la automatización ejecute, copia el "TOKEN COMPLETO" que aparece en los logs y compáralo con el token manual:

```
[AUTH DEBUG] ========== TOKEN COMPLETO ==========
[AUTH DEBUG] <COPIA ESTE TOKEN>
[AUTH DEBUG] ========================================
```

**Cosas a verificar:**
1. ¿Tiene la misma longitud que el token manual?
2. ¿Tiene 2 puntos (formato JWT)?
3. ¿Está truncado o cortado?
4. ¿Tiene espacios o saltos de línea?

## Causas Posibles y Soluciones

### Causa 1: Token Diferente
**Síntoma:** El token capturado automáticamente es diferente del token manual

**Posible razón:** El navegador automatizado genera una sesión diferente

**Solución:**
1. El token capturado podría ser de una sesión diferente
2. Asegúrate de que ambos tokens se capturen del mismo lugar: `localStorage.authentication.token`
3. Verifica que el navegador automatizado complete el login correctamente

### Causa 2: Token Necesita Cookies
**Síntoma:** El token capturado es idéntico pero no funciona en requests.post

**Posible razón:** Leadpier requiere cookies de sesión además del bearer token

**Solución:**
- Actualmente la automatización NO captura cookies (aparece "0 cookies")
- Esto podría ser la causa principal del problema
- Necesitaríamos modificar el código para capturar y usar las cookies junto con el token

### Causa 3: Headers Incorrectos
**Síntoma:** El token funciona en el navegador pero no en requests

**Posible razón:** Los headers que usamos en `requests.post` no coinciden con los del navegador

**Solución:**
- Comparar los headers exactos que usa el navegador
- Agregar headers adicionales que puedan ser requeridos

### Causa 4: Token Truncado
**Síntoma:** El token capturado es más corto que el manual

**Posible razón:** El código está cortando el token en algún punto

**Solución:**
- Ya agregamos debugging para mostrar el token completo
- Verificar que no haya `.strip()` o `.split()` que lo estén cortando

## Próximos Pasos Dependiendo del Diagnóstico

### Si el token es diferente:
```python
# Necesitamos capturar el token de la sesión correcta
# Verificar que el navegador complete el login
```

### Si el token es idéntico pero no funciona:
```python
# Probablemente necesitamos las cookies
# Modificar el código para usar requests.Session() con cookies
```

### Si el token está truncado:
```python
# Revisar el código de extracción
# Asegurarse de no cortar el token en ningún punto
```

## Script de Prueba Rápida

Crea un archivo `test_token_manual.py`:

```python
import requests

# Pega aquí el token que obtuviste manualmente y que SÍ funciona
MANUAL_TOKEN = "eyJhbGc..."  # <-- PEGA TU TOKEN AQUÍ

url = "https://webapi.leadpier.com/v1/api/user/getBalance"
headers = {
    "authorization": f"bearer {MANUAL_TOKEN}",
    "content-type": "application/json",
    "accept": "application/json",
    "origin": "https://dash.leadpier.com",
    "user-agent": "Mozilla/5.0",
}

response = requests.get(url, headers=headers, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
```

Si este script funciona con el token manual, el problema está en cómo la automatización captura el token.

Si este script NO funciona ni con el token manual, entonces el problema es que Leadpier requiere cookies adicionales.

## Información Adicional

### Logs Importantes a Buscar

1. **Captura del token:**
```
[AUTH] Token extraído exitosamente de localStorage.authentication
[AUTH] Token: eyJhbGciOi... (longitud: XXX)
```

2. **Validación desde el navegador:**
```
[AUTH] ✓ Token validado exitosamente desde el navegador!
[AUTH] Status de validación: 200
```

3. **Guardado del token:**
```
[AUTH DEBUG] ========== ACTUALIZANDO TOKEN EN .ENV ==========
[AUTH DEBUG] Token a guardar: eyJhbGc...
[AUTH DEBUG] ✓ Verificación: Token guardado correctamente
```

4. **Validación después de guardar:**
```
[AUTH] ✓ Token guardado y verificado exitosamente
```

### Comandos Útiles

```bash
# Ver el token actual en el .env
cat "Mainteinance and Scaling/enviorement.env" | grep LEADPIER_BEARER

# Ejecutar diagnóstico
python "Mainteinance and Scaling/diagnostico_token.py"

# Ejecutar la automatización completa
python "Mainteinance and Scaling/leadpierget.py"
```

## Contacto para Más Ayuda

Si después de seguir estos pasos aún tienes problemas, proporciona:

1. La salida completa del script `diagnostico_token.py`
2. Los logs de la automatización (especialmente las líneas con [AUTH DEBUG])
3. Confirmación de si el token manual funciona con `requests.post` (script de prueba rápida)

Con esta información podremos identificar exactamente cuál es el problema y cómo solucionarlo.
