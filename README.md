# 🛡️ Sistema Anti-Bloqueo LeadPier

Sistema avanzado de automatización para gestión de adsets de Facebook con integración LeadPier.

## 🚀 Inicio Rápido (5 minutos)

### 1. Clonar el repositorio
```bash
git clone <tu-repo-url>
cd "Mainteinance and Scaling"
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales
```bash
# Copiar archivo de ejemplo
copy enviorement.env.example enviorement.env

# Editar con tus credenciales reales
notepad enviorement.env
```

### 4. Ejecutar
```bash
python leadpiertest1.py
```

---

## 📋 Requisitos

- Python 3.8+
- Chrome instalado (para Selenium)
- Credenciales de Facebook Ads
- Credenciales de LeadPier

---

## 🎯 Características

- ✅ **99% indetectable** - Undetected ChromeDriver
- ✅ **Sistema de caché** - TTL de 5 minutos
- ✅ **Cookie persistence** - 12h de validez
- ✅ **Session keep-alive** - Mantiene sesión activa
- ✅ **Timing humanizado** - Jitter aleatorio
- ✅ **Fallback multi-nivel** - 5 niveles de recuperación
- ✅ **Detection monitor** - Auto-ajuste inteligente
- ✅ **Modo headless** - 100% invisible

---

## 📊 Funcionamiento

El sistema se ejecuta automáticamente y:
- Revisa adsets cada **10 minutos** (+jitter aleatorio 0-60s)
- Escala adsets cada **1 hora** (+jitter aleatorio 0-120s)
- Pausa adsets con ROI negativo
- Escala adsets con buen rendimiento
- Mantiene sesión activa cada 2 minutos

---

## 🔧 Configuración de Credenciales

### Facebook Access Token:
1. Ve a: https://developers.facebook.com/tools/explorer/
2. Selecciona tu app
3. Genera token con permisos: `ads_read`, `ads_management`
4. Copia el token

### LeadPier Bearer Token:
1. Ve a: https://dash.leadpier.com
2. Inicia sesión
3. F12 → Console
4. Ejecuta: `JSON.parse(localStorage.getItem('authentication')).token`
5. Copia el token

### LeadPier Email y Password:
- Tus credenciales de login de LeadPier

---

## 📁 Estructura de Archivos

### Core del Sistema:
- `leadpiertest1.py` - Script principal
- `leadpier_undetected_session.py` - Sesión indetectable
- `leadpier_cache_manager.py` - Sistema de caché
- `cookie_manager.py` - Gestión de cookies
- `detection_monitor.py` - Monitor y auto-ajuste
- `leadpier_auth.py` - Autenticación LeadPier

### Configuración:
- `enviorement.env` - Credenciales (NO INCLUIDO - usar .example)
- `requirements.txt` - Dependencias Python

### Utilidades:
- `status.py` - Ver estado del sistema
- `test_anti_bloqueo.py` - Suite de testing

### Documentación:
- `GUIA_USO_FINAL.md` - Guía de uso completa
- `IMPLEMENTACION_COMPLETA.md` - Documentación técnica
- `COMANDOS_RAPIDOS.md` - Referencia de comandos

---

## 🧪 Testing

Verificar que todo funciona:

```bash
python test_anti_bloqueo.py
```

Ver estado del sistema:

```bash
python status.py
```

---

## 📊 Monitoreo

### Ver estadísticas:
```bash
python -c "from detection_monitor import get_detection_monitor; get_detection_monitor().print_stats()"
```

### Limpiar caché:
```bash
python -c "from leadpier_cache_manager import get_leadpier_cache; get_leadpier_cache().clear()"
```

---

## 🆘 Troubleshooting

### Chrome no se inicia:
```bash
# Instalar/actualizar Chrome
# Verificar que chromedriver esté disponible
```

### Token inválido:
1. Obtén nuevo token (ver "Configuración de Credenciales")
2. Actualiza `enviorement.env`
3. Re-ejecuta el script

### Modo defensivo activado:
```bash
# Salir de modo defensivo
python -c "from detection_monitor import get_detection_monitor; m = get_detection_monitor(); m.defensive_mode_until = None; m._save_state()"
```

---

## 📈 Métricas Esperadas

- **Primera ejecución:** 15-30 segundos (sin caché)
- **Siguientes ejecuciones:** 3-5 segundos (con caché)
- **Tasa de éxito:** >95%
- **Re-logins:** 1-2 por día

---

## ☁️ Ejecución en la Nube

Para ejecutar 24/7 sin tu PC:

- **Google Colab** (gratis) - Ver `LEADPIER_COLAB.ipynb`
- **Google Cloud VM** (gratis 3 meses) - Ver `GUIA_EJECUTAR_EN_NUBE.md`
- **AWS EC2** (gratis 12 meses) - Ver `GUIA_EJECUTAR_EN_NUBE.md`

---

## 📝 Notas

- Los archivos de caché/cookies se crean automáticamente
- El sistema es completamente autónomo
- Modo headless por defecto (navegador invisible)
- Logs en consola para monitoreo

---

## 🔒 Seguridad

- **NUNCA** subas `enviorement.env` a GitHub
- El archivo `.gitignore` protege credenciales
- Usa `enviorement.env.example` como plantilla

---

## 📞 Soporte

Ver documentación completa en:
- `GUIA_USO_FINAL.md`
- `IMPLEMENTACION_COMPLETA.md`
- `RESUMEN_SISTEMA_ANTI_BLOQUEO.md`

---

## ✅ Checklist Inicial

```
□ Clonar repositorio
□ Instalar dependencias (pip install -r requirements.txt)
□ Copiar enviorement.env.example → enviorement.env
□ Configurar credenciales en enviorement.env
□ Ejecutar test (python test_anti_bloqueo.py)
□ Ejecutar script principal (python leadpiertest1.py)
□ Verificar que funciona correctamente
```

---

**Estado:** ✅ PRODUCCIÓN - 100% OPERATIVO  
**Versión:** 2.0 - Undetected System  
**Última actualización:** Diciembre 2025

