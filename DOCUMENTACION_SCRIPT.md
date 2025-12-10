# 📊 DOCUMENTACIÓN COMPLETA - SCRIPT DE AUTOMATIZACIÓN FACEBOOK ADS

## 🎯 **PROPÓSITO GENERAL**
Script de automatización para gestión inteligente de adsets de Facebook basado en métricas de rendimiento (ROI y spend), con integración de datos de Leadpier y Facebook Graph API.

---

## ⚙️ **CONFIGURACIÓN INICIAL**

### **📁 Archivos Requeridos:**
- `leadpiertest1.py` - Script principal
- `enviorement.env` - Tokens de acceso
- `adsets_report.csv` - Reporte de acciones (generado automáticamente)
- `scaling_report.csv` - Reporte de escalamiento (generado automáticamente)

### **🔑 Variables de Entorno:**
```env
FB_ACCESS_TOKEN=EAA7hTdVPjsgBP...  # Token de Facebook Graph API
LEADPIER_BEARER=eyJhbGciOiJIUzI1NiI...  # Token Bearer de Leadpier
```

### **🏢 Cuentas de Facebook Monitoreadas:**
- `act_428549066458338`
- `act_653164011031498`
- `act_1122267929000780`
- `act_1172700037197465`

---

## 🕐 **CONFIGURACIÓN DE HORARIOS**

### **⏰ Zona Horaria:**
- **UTC-4** - Todas las operaciones y datos se manejan en esta zona horaria

### **📅 Horario de Operación:**
- **Inicio:** Manual (cuando ejecutas el script)
- **Fin:** Automático a las **18:00 (6 PM) UTC-4**
- **Reinicio:** Manual al día siguiente

### **⏱️ Frecuencias de Ejecución:**
- **Revisión y Apagado:** Cada **10 minutos**
- **Escalamiento:** Cada **1 hora**

---

## 📈 **LÓGICA DE APAGADO/MANTENIMIENTO**

### **🎛️ Thresholds Configurados:**
```python
SPEND_HIGH_THRESHOLD = 50.0    # USD
SPEND_LOW_THRESHOLD  = 25.0    # USD  
ROI_OFF_THRESHOLD    = 0.0     # %
```

### **📋 Reglas de Negocio:**

#### **✅ Regla 1 - MANTENER:**
- **Condición:** spend ≥ $25 Y ROI > 0%
- **Acción:** Mantener adset activo
- **Ejemplo:** Spend $45, ROI 15% → MANTENER

#### **✅ Regla 2 - MANTENER:**
- **Condición:** spend < $25
- **Acción:** Mantener adset activo (independiente del ROI)
- **Ejemplo:** Spend $20, ROI -50% → MANTENER

#### **❌ Regla 3 - PAUSAR:**
- **Condición:** spend ≥ $25 Y ROI ≤ 0%
- **Acción:** Pausar adset
- **Ejemplo:** Spend $30, ROI -10% → PAUSAR

---

## 🚀 **LÓGICA DE ESCALAMIENTO**

### **⚡ Condiciones de Escalamiento:**

#### **🎯 Condición 0 - ALTO ROI MODERADO SPEND:**
- **Spend:** $40 - $99.99
- **ROI:** ≥ 100%
- **Multiplicador:** 1.25x
- **Ejemplo:** Spend $47, ROI 186% → ESCALAR

#### **🎯 Condición 1 - STANDARD:**
- **Spend:** ≥ $100
- **ROI:** ≥ 80%
- **Multiplicador:** 1.25x

#### **🎯 Condición 2 - VOLUMEN MEDIO:**
- **Spend:** ≥ $500
- **ROI:** ≥ 50%
- **Multiplicador:** 1.25x

#### **🎯 Condición 3 - ALTO VOLUMEN:**
- **Spend:** ≥ $1000
- **ROI:** ≥ 30%
- **Multiplicador:** 1.25x

### **💰 Sistema de Redondeo Inteligente:**
- **≤ $100,000:** Redondeo hacia abajo a miles
  - Ejemplo: $31,250 → $31,000
- **> $100,000:** Redondeo hacia abajo a decenas de miles  
  - Ejemplo: $287,500 → $280,000

---

## 🔗 **INTEGRACIÓN DE APIs**

### **📊 Leadpier API:**
- **Endpoint:** `https://webapi.leadpier.com/v1/api/stats/user/sources`
- **Método:** POST con Bearer Token
- **Datos:** Revenue, EPL, EPC por fuente
- **Fallback:** GET a `https://dash.leadpier.com/marketer-statistics/sources`

### **📱 Facebook Graph API:**
- **Versión:** v23.0
- **Endpoints:**
  - `/adsets` - Lista de adsets activos
  - `/insights` - Datos de spend por adset
  - `/adsets/{id}` - Actualización de presupuestos y status

### **🔄 Fórmula ROI:**
```python
roi = ((revenue - spend) / spend * 100.0) if spend > 0 else 0.0
```

---

## 📝 **SISTEMA DE REPORTES**

### **📄 adsets_report.csv:**
**Columnas:**
- `account_id` - ID de cuenta Facebook
- `adset_id` - ID del adset
- `name` - Nombre del adset
- `status` - Estado actual (ACTIVE/PAUSED)
- `spend` - Gasto del día en USD
- `revenue` - Ingresos de Leadpier en USD
- `roi` - ROI calculado en %
- `epl` - Earnings per Lead
- `epc` - Earnings per Click
- `action` - Acción tomada (KEEP/PAUSE)
- `reason` - Explicación de la decisión

### **📄 scaling_report.csv:**
**Columnas:**
- `account_id` - ID de cuenta Facebook
- `adset_id` - ID del adset
- `name` - Nombre del adset
- `spend` - Gasto del día en USD
- `revenue` - Ingresos en USD
- `roi` - ROI calculado en %
- `should_scale` - Si debe escalarse (True/False)
- `condition_met` - Número de condición cumplida (0,1,2,3)
- `reason` - Explicación de la decisión
- `scaled` - Si fue escalado exitosamente
- `scaling_result` - Detalles del resultado de escalado

---

## 🛠️ **FUNCIONES PRINCIPALES**

### **📊 Obtención de Datos:**
- `fetch_leadpier_sources_df()` - Datos de Leadpier (método principal)
- `fetch_leadpier_sources_df_fallback()` - Método de respaldo
- `fetch_account_adsets()` - Lista de adsets activos
- `fetch_adset_spend_today()` - Spend diario por adset

### **🧠 Lógica de Decisión:**
- `determine_adset_action()` - Decidir mantener/pausar
- `determine_scaling_action()` - Decidir si escalar
- `round_budget_intelligently()` - Redondeo inteligente

### **💰 Gestión de Presupuestos:**
- `get_adset_budget()` - Obtener presupuesto actual
- `scale_adset_budget()` - Escalar presupuesto
- `pause_adset()` - Pausar adset

### **⏰ Funciones de Tiempo:**
- `today_utc_minus_4_str()` - Fecha actual en UTC-4

### **🔄 Funciones Principales:**
- `revisar_y_actualizar()` - Proceso de apagado (cada 10 min)
- `escalamiento()` - Proceso de escalado (cada 1 hora)

---

## 🚨 **MANEJO DE ERRORES**

### **🔄 Reintentos Automáticos:**
- **Facebook API:** 3 reintentos con pausa de 2 segundos
- **Leadpier API:** Método fallback automático si falla el principal

### **📊 Validaciones:**
- Verificación de estructura de datos de APIs
- Manejo de adsets sin datos de spend
- Validación de presupuestos antes de escalado
- Verificación de tokens de acceso

### **📝 Logging Detallado:**
- Mensajes informativos con emojis
- Debug de adsets sin datos
- Reportes de éxito/error en acciones
- Timestamps en UTC

---

## 🎮 **EJECUCIÓN DEL SCRIPT**

### **▶️ Comando de Inicio:**
```bash
python leadpiertest1.py
```

### **📺 Ejemplo de Salida:**
```
=== RUN 2025-09-11 14:30:45 UTC ===
🕐 Hora actual: 10:30 UTC-4
⏳ Schedulers activos:
   📊 Revisión y apagado: cada 10 minutos
   🚀 Escalamiento: cada 1 hora
   🕕 Límite: Se detendrá a las 18:00 (6 PM) UTC-4

✅ Datos de Leadpier obtenidos: 50 registros
✅ MANTENER: BM5_1_AUTOI9-FP-AUTO_WhyDoYouDoIt-TKv3_Juan-BC_RS...
   💰 Spend: $47.35 | 📊 ROI: 186.46%
   📝 Razón: Regla 1: Spend $47.35 >= $25.0 y ROI 186.46% > 0

🚀 ESCALADO: BM5_1_AUTOI9-FP-AUTO_WhyDoYouDoIt-TKv3_Juan-BPN_RS...
   💰 Spend: $63.70 | 📊 ROI: 105.92%
   📝 Razón: Condición 0: $40.0 <= Spend $63.70 < $100.0 y ROI 105.92% >= 100.0%
   💵 Presupuesto: $2,000.00 → $2,000.00
   🔢 Cálculo: $2,000.00 × 1.25 = $2,500.00 → $2,000.00 (redondeado)

📁 Exportado: adsets_report.csv (31 filas)
📁 Reporte de escalamiento: scaling_report.csv
🚀 Adsets escalados: 1/3 elegibles
```

### **🛑 Finalización Automática:**
```
🕕 FINALIZANDO: Son las 18:00 UTC-4 (después de las 6 PM)
   El script se detendrá hasta mañana.
```

---

## 🎯 **CASOS DE USO TÍPICOS**

### **✅ Adset Mantenido (Alto ROI):**
- Spend: $47.35, ROI: 186.46% → **MANTENER** + **ESCALAR** (Condición 0)

### **✅ Adset Mantenido (Bajo Spend):**
- Spend: $12.69, ROI: -38.22% → **MANTENER** (Regla 2)

### **❌ Adset Pausado (ROI Negativo):**
- Spend: $34.57, ROI: -1.62% → **PAUSAR** (Regla 3)

### **🚀 Adset Escalado (Condiciones Múltiples):**
- Spend: $125, ROI: 85% → **MANTENER** + **ESCALAR** (Condición 1)

---

## 📋 **REQUISITOS TÉCNICOS**

### **🐍 Dependencias Python:**
```python
requests      # APIs HTTP
pandas        # Manipulación de datos
schedule      # Programación de tareas
python-dotenv # Variables de entorno
datetime      # Manejo de fechas
json          # Procesamiento JSON
os            # Variables del sistema
time          # Control de tiempo
```

### **🔐 Permisos Requeridos:**
- **Facebook:** ads_management, ads_read
- **Leadpier:** API access con Bearer token válido

---

## 🎛️ **CONFIGURACIONES PERSONALIZABLES**

### **💰 Thresholds Económicos:**
```python
SPEND_HIGH_THRESHOLD = 50.0    # Cambiar según necesidades
SPEND_LOW_THRESHOLD  = 25.0    # Cambiar según necesidades
SCALING_MULTIPLIER   = 1.25    # Factor de escalado
```

### **⏰ Frecuencias:**
```python
schedule.every(10).minutes.do(revisar_y_actualizar)  # Personalizable
schedule.every(1).hours.do(escalamiento)            # Personalizable
```

### **🎯 Condiciones de Escalado:**
```python
SCALING_CONDITIONS = [
    {"spend_min": 40.0, "spend_max": 99.99, "roi_min": 100.0},
    {"spend_min": 100.0, "roi_min": 80.0},
    {"spend_min": 500.0, "roi_min": 50.0},
    {"spend_min": 1000.0, "roi_min": 30.0},
]
```

---

## 🚀 **CARACTERÍSTICAS AVANZADAS**

### **🧠 Inteligencia de Redondeo:**
- Optimización automática de presupuestos
- Redondeo hacia abajo para conservar capital
- Diferentes estrategias según el volumen

### **🔄 Sistema de Fallback:**
- Múltiples métodos para obtener datos de Leadpier
- Reintentos automáticos en APIs
- Continuidad de operación ante fallos parciales

### **📊 Reportes Detallados:**
- CSV exportables para análisis
- Tracking completo de todas las acciones
- Métricas de rendimiento del sistema

### **⏰ Gestión Temporal Inteligente:**
- Zona horaria específica para Facebook
- Límites de operación automáticos
- Sincronización con ciclos de negocio

---

## 🎯 **RESULTADOS ESPERADOS**

### **📈 Optimización Automática:**
- Pausado de adsets no rentables (ROI ≤ 0% con spend ≥ $25)
- Escalado de adsets de alto rendimiento
- Conservación de adsets en prueba (spend < $25)

### **💰 Gestión de Capital:**
- Redondeo inteligente de presupuestos
- Multiplicador conservador (1.25x)
- Protección contra over-spending

### **📊 Visibilidad Completa:**
- Reportes detallados de todas las acciones
- Tracking de ROI y spend en tiempo real
- Historial completo de decisiones automatizadas

---

*Documento generado automáticamente - Versión 1.0*
*Fecha: 11 de Septiembre, 2025*
*Script: leadpiertest1.py*
