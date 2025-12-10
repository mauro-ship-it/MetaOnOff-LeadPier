# ☁️ GUÍA: Ejecutar LeadPier en la Nube

**Problema:** No puedes ejecutar el script en tu laptop suspendida durante viajes.  
**Solución:** Migrar a un servidor en la nube que corre 24/7.

---

## 🎯 OPCIONES DISPONIBLES

| Opción | Costo | Dificultad | Tiempo Setup | Recomendado |
|--------|-------|------------|--------------|-------------|
| **Google Colab** | Gratis | ⭐ Fácil | 10 min | ✅ SÍ (empezar aquí) |
| **Google Cloud** | Gratis 3 meses | ⭐⭐ Media | 30 min | ✅ Muy bueno |
| **AWS EC2** | Gratis 12 meses | ⭐⭐⭐ Difícil | 45 min | ✅ Potente |
| **DigitalOcean** | $4-6/mes | ⭐⭐ Media | 20 min | ✅ Simple |
| **PythonAnywhere** | Gratis | ⭐ Fácil | 15 min | ❌ No soporta Selenium |

---

## 🌟 OPCIÓN 1: Google Colab (RECOMENDADO)

### ✅ Ventajas:
- **100% GRATIS** (sin tarjeta de crédito)
- **Más fácil** (listo en 10 minutos)
- **Accesible desde móvil**
- **No necesitas conocimientos de servidores**

### ⚠️ Limitaciones:
- Se desconecta cada ~12 horas (necesitas reconectar desde móvil)
- Necesitas mantener una pestaña abierta

### 📱 Instrucciones:

1. **Abre Google Colab:**
   - Ve a: https://colab.research.google.com/
   - Inicia sesión con tu cuenta de Google

2. **Sube el notebook:**
   - Usa el archivo `LEADPIER_COLAB.ipynb` que te preparé
   - En Colab: File → Upload notebook → Seleccionar archivo

3. **Ejecuta las celdas en orden:**
   - Celda 1: Instala dependencias (2-3 min)
   - Celda 2: Monta Google Drive (1 clic autorizar)
   - Celda 3: Sube tus archivos Python
   - Celda 4: Configura credenciales
   - Celda 5: Test rápido
   - Celda 6: **EJECUTAR** (deja corriendo)

4. **Desde tu móvil:**
   - Abre la misma notebook en Chrome/Safari
   - Verás el script ejecutándose
   - Cuando se desconecte (~12h), haz clic en "Reconnect"
   - Re-ejecuta la celda 6

**Listo! Tu script corre en la nube gratis.**

---

## 🏆 OPCIÓN 2: Google Cloud VM (MÁS PROFESIONAL)

### ✅ Ventajas:
- **$300 crédito gratis** (3 meses)
- **Siempre activo** (no se desconecta)
- **Acceso SSH desde móvil**
- **Más potente**

### 💳 Requisito:
- Tarjeta de crédito (no se cobra, solo verificación)

### 📋 Instrucciones:

#### 1. Crear Cuenta GCP:
```
1. Ve a: https://cloud.google.com/free
2. Haz clic en "Get started for free"
3. Inicia sesión con Google
4. Acepta $300 de crédito gratuito
5. Agrega tarjeta (NO SE COBRARÁ sin tu autorización)
```

#### 2. Crear VM (Máquina Virtual):
```
1. Ve a: Compute Engine → VM Instances
2. Haz clic en "CREATE INSTANCE"
3. Configuración:
   - Name: leadpier-bot
   - Region: us-central1 (más barato)
   - Machine type: e2-micro (gratis en free tier)
   - Boot disk: Ubuntu 20.04 LTS
   - Firewall: Allow HTTP/HTTPS
4. Haz clic en "CREATE"
```

#### 3. Configurar VM:
```bash
# Conectar por SSH (desde navegador o móvil)
# En GCP Console, haz clic en "SSH" junto a tu VM

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y dependencias
sudo apt install -y python3-pip chromium-browser chromium-chromedriver
pip3 install undetected-chromedriver selenium requests python-dotenv schedule pandas

# Subir archivos (opción A: desde local)
gcloud compute scp --recurse "C:\Users\mauro\Desktop\Freelance\MetaOnOff\Mainteinance and Scaling" leadpier-bot:~/

# O subir archivos (opción B: desde GitHub)
git clone <tu-repo-privado>
cd <repo>

# Configurar credenciales
nano enviorement.env
# (Pega tus credenciales, Ctrl+X para salir)

# Ejecutar script
nohup python3 leadpiertest1.py > leadpier.log 2>&1 &

# Ver logs en tiempo real
tail -f leadpier.log
```

#### 4. Mantener Activo:
```bash
# Instalar tmux (para mantener sesión)
sudo apt install -y tmux

# Crear sesión persistente
tmux new -s leadpier

# Dentro de tmux, ejecutar:
python3 leadpiertest1.py

# Desconectar (presionar): Ctrl+B, luego D

# Reconectar después:
tmux attach -t leadpier
```

#### 5. Acceder desde Móvil:
```
1. Instala "Termius" app (SSH client para móvil)
2. Agrega tu VM:
   - Host: <IP de tu VM en GCP>
   - User: <tu-usuario-gcp>
   - Authentication: SSH Key (descarga de GCP)
3. Conectar y ver logs:
   tmux attach -t leadpier
```

**Costo:** $0 (con $300 de crédito, dura meses)

---

## 💎 OPCIÓN 3: AWS EC2 (MÁS POTENTE)

### ✅ Ventajas:
- **Gratis 12 meses** (t2.micro)
- **Muy confiable**
- **Infraestructura profesional**

### 📋 Instrucciones Rápidas:

```
1. Crear cuenta AWS: https://aws.amazon.com/free
2. EC2 → Launch Instance
3. Configuración:
   - AMI: Ubuntu Server 20.04 LTS
   - Instance Type: t2.micro (free tier)
   - Storage: 8GB
   - Security Group: SSH (port 22)
4. Descargar .pem key
5. Conectar:
   ssh -i "tu-key.pem" ubuntu@<ip-publica>
6. Instalar y ejecutar (igual que GCP arriba)
```

**Costo:** $0 (primer año gratis)

---

## 🚀 OPCIÓN 4: DigitalOcean (MÁS SIMPLE)

### ✅ Ventajas:
- **$200 crédito gratis** (con referral)
- **Más simple** que AWS/GCP
- **Interfaz amigable**

### 📋 Instrucciones:

```
1. Crear cuenta: https://m.do.co/c/XXXXXX (usa referral para $200)
2. Create → Droplets
3. Configuración:
   - Image: Ubuntu 20.04
   - Plan: Basic ($4/mes)
   - Datacenter: New York
4. Crear y conectar por SSH
5. Instalar y ejecutar (igual que arriba)
```

**Costo:** $0 (con crédito, dura 50 meses)

---

## 📊 COMPARACIÓN FINAL

### Para tu caso (viaje con móvil):

| Necesidad | Mejor Opción |
|-----------|--------------|
| **Más fácil** | Google Colab ⭐⭐⭐⭐⭐ |
| **100% gratis sin tarjeta** | Google Colab |
| **No desconectar nunca** | Google Cloud VM / AWS |
| **Acceso desde móvil** | Todas (Colab más fácil) |
| **Duración del viaje** | |
| → 1-3 días | Google Colab (reconectar 2-6 veces) |
| → 1-2 semanas | Google Cloud VM |
| → Permanente | AWS / DigitalOcean |

---

## 🎯 MI RECOMENDACIÓN

### **Para empezar HOY (tu viaje):**

1. **Usa Google Colab** (10 minutos setup):
   - Sube el notebook `LEADPIER_COLAB.ipynb`
   - Ejecuta las celdas
   - Deja corriendo en pestaña del móvil
   - Reconecta 2 veces al día (5 segundos)

2. **Después del viaje, migra a Google Cloud VM** (30 minutos):
   - Setup una sola vez
   - Nunca más te preocupes
   - $300 gratis dura 4-6 meses
   - Gratis permanente si usas e2-micro

---

## 📱 SCRIPTS PARA MÓVIL

Te preparo también scripts optimizados para verificar el estado desde móvil:

### Status rápido (agregar a Google Colab):
```python
# Ejecuta esta celda para ver estado
from detection_monitor import get_detection_monitor
monitor = get_detection_monitor()
stats = monitor.get_stats()

print(f"✅ Éxito: {stats['success_rate']}%")
print(f"📊 Total: {stats['total_requests']} peticiones")
print(f"⏰ Último: {stats['last_success']}")
```

---

## 🆘 SOPORTE

### Problemas con Colab:
- "Se desconecta muy rápido" → Normal cada 12h, solo reconecta
- "No encuentra archivos" → Re-ejecuta celda de Google Drive mount
- "Chrome no funciona" → Re-ejecuta celda de instalación

### Problemas con VMs:
- "No puedo conectar por SSH" → Verifica reglas de firewall (port 22)
- "Script no corre en background" → Usa `tmux` o `screen`
- "Consume mucha RAM" → Reduce TTL de caché a 1 minuto

---

## ✅ SIGUIENTE PASO

**Para tu viaje AHORA:**

1. Abre el archivo `LEADPIER_COLAB.ipynb` que creé
2. Súbelo a Google Colab
3. Sigue las instrucciones del notebook (10 min)
4. **Listo para viajar con script corriendo en la nube**

**Para permanente (después):**

1. Crea cuenta en Google Cloud (usa tu Gmail)
2. Activa $300 de crédito
3. Crea VM e2-micro (5 min)
4. Copia los archivos (5 min)
5. Ejecuta con tmux (5 min)
6. **Nunca más te preocupes**

---

¿Quieres que te ayude con alguna opción específica?

