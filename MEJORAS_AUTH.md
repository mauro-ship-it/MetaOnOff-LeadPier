# Mejoras al Sistema de Autenticación Leadpier

## Fecha: 8 de Diciembre de 2025

## Problemas Identificados

1. **Token capturado pero inválido**: El sistema capturaba el token pero fallaba con error 401 al validarlo
2. **Cookies no capturadas**: El navegador reportaba 0 cookies (problema en modo headless)
3. **Token truncado**: Los tokens podían estar incompletos
4. **Timing insuficiente**: El token podía no estar activo inmediatamente después del login

## Soluciones Implementadas

### 1. Método Prioritario: Validación desde el Navegador
- **Qué hace**: Extrae el token de `localStorage.authentication` y lo valida haciendo una petición real desde el contexto del navegador
- **Por qué es mejor**: Si funciona en el navegador, sabemos con certeza que el token es válido
- **Endpoint usado**: `https://webapi.leadpier.com/v1/api/user/getBalance` (más simple y rápido)
- **Resultado**: Si tiene éxito, retorna el token inmediatamente sin validación adicional

### 2. Tiempos de Espera Mejorados
- **Después del login**: 5 segundos (antes: 3) - para que el token se active en el servidor
- **Carga de datos**: 8 segundos (antes: 5) - para que se disparen todos los requests API
- **Antes de validar**: 3 segundos adicionales - para dar tiempo al servidor

### 3. Captura de Cookies Mejorada
- Captura cookies ANTES del refresh
- Si no hay cookies, navega a la página principal
- Debug detallado de cookies encontradas
- Manejo especial para modo headless

### 4. Validación Mejorada del Token
- Verifica que el token tenga formato JWT válido (3 partes separadas por puntos)
- Muestra la longitud del token para detectar truncamiento
- Headers en minúsculas (como el navegador los envía)
- Validación desde el navegador como primer método

### 5. Extracción de Token Más Robusta
- Verifica la estructura JWT antes de aceptar el token
- Debug adicional con longitud y formato
- Prioriza el token de `localStorage.authentication`
- Fallback a múltiples fuentes si el primero falla

## Flujo de Autenticación Mejorado

```
1. Login en el navegador
   ↓
2. Esperar 5 segundos (activación del token)
   ↓
3. Navegar a página de estadísticas
   ↓
4. Esperar 8 segundos (carga de datos)
   ↓
5. Hacer petición API desde el navegador
   ↓
6. [NUEVO] Extraer y validar token directamente desde el navegador
   ↓ (si falla)
7. Intentar capturar token de network requests (selenium-wire)
   ↓ (si falla)
8. Intentar capturar token de Chrome DevTools logs
   ↓ (si falla)
9. Extraer directamente de localStorage
   ↓
10. Esperar 3 segundos adicionales
   ↓
11. Validar token desde el navegador (fetch)
   ↓ (si falla)
12. Validar token con requests.post sin proxy
   ↓ (si falla)
13. Validar token con requests.post con proxy
   ↓ (si falla)
14. Intentar con cookies del navegador
   ↓ (si falla)
15. Buscar tokens alternativos en localStorage/sessionStorage
```

## Cómo Probar

### Opción 1: Ejecutar el script principal
```bash
cd "Mainteinance and Scaling"
python leadpierget.py  # o el script que use leadpier_auth
```

### Opción 2: Probar solo la autenticación
```python
from leadpier_auth import ensure_leadpier_token

# Esto intentará validar el token actual y hacer auto-login si es necesario
result = ensure_leadpier_token()
print(f"Resultado: {result}")
```

## Logs a Observar

### ✅ Login Exitoso (nuevo método)
```
[AUTH] Método prioritario: Extraer y validar token desde el navegador...
[AUTH] ✓ Token validado exitosamente desde el navegador!
[AUTH] Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleH... (longitud: 523)
[AUTH] Partes JWT: 3 (debe ser 3)
[AUTH] Status de validación: 200
[AUTH] Token funcional encontrado - omitiendo validación adicional
```

### ⚠️ Token Inválido
```
[AUTH] Validación desde navegador falló: Invalid authorization token
[AUTH] Token extraído (pero no validado): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 📊 Debug de Token
```
[AUTH DEBUG] Token a validar: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[AUTH DEBUG] Longitud del token: 523 caracteres
[AUTH DEBUG] Token extraído tiene 2 puntos (debe ser 2 para JWT)
```

## Qué Hacer si Sigue Fallando

### Si el token se valida en el navegador pero falla con requests:
- **Causa probable**: Problema con headers o proxy
- **Solución**: El sistema ahora retorna el token si funciona en el navegador, omitiendo la validación con requests

### Si no se capturan cookies:
- **Causa probable**: Modo headless con restricciones
- **Solución**: El sistema automáticamente reintenta sin headless (con ventana visible)

### Si el token tiene formato inválido:
- **Causa probable**: Token truncado o corrupto
- **Solución**: El sistema ahora verifica el formato antes de aceptar el token

### Si nada funciona:
1. Verificar que las credenciales sean correctas en `enviorement.env`
2. Intentar manualmente:
   - Ir a https://dash.leadpier.com
   - Login
   - F12 → Console
   - Ejecutar: `JSON.parse(localStorage.getItem('authentication')).token`
   - Copiar el token al archivo `enviorement.env`

## Diferencias Clave vs Versión Anterior

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Validación | Solo con requests.post | Primero desde el navegador |
| Timing | 3s + 5s = 8s total | 5s + 8s + 3s = 16s total |
| Verificación JWT | No | Sí (verifica 3 partes) |
| Cookies | Captura después de refresh | Captura antes y después |
| Debug | Limitado | Extensivo (longitud, partes, status) |
| Método prioritario | selenium-wire | Validación desde navegador |

## Próximos Pasos

Si el problema persiste después de estas mejoras, considerar:

1. **Agregar selenium-wire**: `pip install selenium-wire` para mejor captura de requests
2. **Investigar autenticación 2FA**: Si Leadpier implementó 2FA, necesitaremos adaptarlo
3. **Cookies de sesión**: Puede que el token necesite cookies específicas además del bearer token
4. **Rate limiting**: Leadpier puede estar bloqueando requests automatizados

## Notas Técnicas

- El token JWT de Leadpier debe tener exactamente 3 partes (header.payload.signature)
- La longitud típica de un token JWT es entre 200-800 caracteres
- Leadpier usa el formato `bearer <token>` en minúsculas en el header Authorization
- El endpoint `/v1/api/user/getBalance` es más rápido que `/v1/api/stats/user/sources` para validación
