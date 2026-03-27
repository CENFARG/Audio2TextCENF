# 📋 Guía de Instalación - Audio2Text CENF v0.9.0

## ⚠️ Advertencia de Windows SmartScreen

**Cuando descargues e intentes ejecutar Audio2Text_CENF_0.9.0.exe, Windows SmartScreen puede mostrar una advertencia de seguridad.**

### ¿Por qué ocurre esto?

- Audio2Text es una aplicación legítima y segura
- La advertencia aparece porque el ejecutable **no tiene una firma digital** (los certificados de código cuestan ~$300-400 USD anuales)
- Es un comportamiento normal para aplicaciones independientes sin firma

### ✅ Cómo ejecutar la aplicación de forma segura

Sigue estos pasos:

#### **Paso 1: Aparece la advertencia inicial**
Cuando hagas doble clic en el ejecutable, verás:

```
Windows protegió su PC
SmartScreen de Microsoft Defender impidió el inicio de una aplicación desconocida...
```

#### **Paso 2: Hacer clic en "Más información"**
![Paso 1](docs/smartscreen_step1.png)

Haz clic en el enlace **"Más información"** en la ventana de advertencia.

#### **Paso 3: Hacer clic en "Ejecutar de todas formas"**
![Paso 2](docs/smartscreen_step2.png)

Aparecerá un nuevo botón: **"Ejecutar de todas formas"**. Haz clic en él.

#### **Paso 4: La aplicación se ejecutará normalmente**
Solo necesitas hacer esto **la primera vez**. Windows recordará tu elección.

---

## 🔧 Requisitos del Sistema

- **Sistema Operativo:** Windows 10/11 (64-bit)
- **RAM:** Mínimo 4 GB (recomendado 8 GB)
- **Espacio en disco:** 200 MB libres
- **Micrófono:** Cualquier micrófono compatible con Windows
- **Internet:** Conexión requerida para la transcripción (usa API de Groq)

---

## 🚀 Instalación

### Opción A: Ejecutable Portable (Recomendado)

1. **Descarga** `Audio2Text_CENF_0.9.0.exe`
2. **Coloca el ejecutable** en una carpeta de tu elección (ej: `C:\Aplicaciones\Audio2Text\`)
3. **Ejecuta** el archivo `.exe` siguiendo los pasos de SmartScreen arriba
4. **Configura tu API Key** de Groq en la primera ejecución:
   - Ve a la pestaña "Configuración"
   - Ingresa tu API Key (obtén una gratis en: https://console.groq.com/keys)
   - Haz clic en "Guardar Configuración"

### Opción B: Desde el Código Fuente (Para Desarrolladores)

```bash
# 1. Clonar o descargar el repositorio
git clone https://github.com/tu-usuario/audio2text.git
cd audio2text

# 2. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python main.py
```

---

## 🎯 Configuración Inicial

### 1. API Key de Groq (Obligatorio)

Audio2Text usa la API de Groq para la transcripción. Es **gratis** hasta 14,400 requests/día.

1. Regístrate en: https://console.groq.com/
2. Crea una API Key
3. Copia la clave
4. Pégala en Audio2Text → Configuración → "API Key de Groq"

### 2. Configurar Hotkey (Opcional)

- Por defecto: **F9**
- Puedes cambiarlo en: Configuración → "Hotkey de grabación"
- Opciones: F1-F12

### 3. Seleccionar Idioma (Opcional)

- Español (predeterminado)
- Inglés

---

## 🎤 Cómo Usar

### Grabación Rápida

1. **Presiona** la tecla de hotkey (ej: F9)
2. **Habla** normalmente
3. **Suelta** la tecla
4. La transcripción aparecerá automáticamente en el panel derecho

### Opciones Avanzadas

- **Auto-copiar al portapapeles:** Activa en Configuración
- **Guardar audio:** Los archivos se guardan en la carpeta configurada
- **Ver historial:** Pestaña "Archivos Guardados"

---

## 🛡️ Privacidad y Seguridad

- **Tus datos:** Los audios se procesan a través de la API de Groq (revisa su política de privacidad)
- **API Key:** Se guarda localmente en tu computadora en `config.json`
- **Sin telemetría:** Audio2Text no envía datos de uso ni analíticas

---

## ❓ Preguntas Frecuentes

### ¿Es gratis?
Sí, Audio2Text es gratis. Solo necesitas una API Key gratuita de Groq.

### ¿Necesito Internet?
Sí, la transcripción se realiza en la nube (Groq API).

### ¿Funciona con cualquier micrófono?
Sí, cualquier micrófono compatible con Windows.

### ¿Por qué Windows dice que es peligroso?
Es una advertencia estándar para aplicaciones sin firma digital. Sigue los pasos anteriores para ejecutarlo de forma segura.

### ¿Puedo usarlo offline?
No en esta versión. La transcripción requiere conexión a Internet.

---

## 🐛 Solución de Problemas

### El micrófono no funciona
1. Verifica que tu micrófono esté conectado y funcionando en Windows
2. Ve a Configuración de Windows → Privacidad → Micrófono
3. Asegúrate de que las aplicaciones puedan acceder al micrófono

### Error: "API Key inválida"
1. Verifica que copiaste la clave completa de Groq
2. Asegúrate de que la clave no haya expirado
3. Genera una nueva clave si es necesario

### La aplicación no abre
1. Asegúrate de tener Windows 10/11 (64-bit)
2. Ejecuta como administrador (clic derecho → "Ejecutar como administrador")
3. Verifica que no haya antivirus bloqueando la ejecución

---

## 📞 Soporte

- **Email:** soporte@cenf.com.ar
- **Documentación:** https://docs.audio2text-cenf.com
- **Issues:** https://github.com/tu-usuario/audio2text/issues

---

## 📄 Licencia

© 2024 CENF - Centro de Excelencia en Negocios del Futuro. Todos los derechos reservados.

---

**¿Primera vez usando Audio2Text?** 
Mira nuestro [video tutorial de 3 minutos](https://youtube.com/ejemplo) 🎥
