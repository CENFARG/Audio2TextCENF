# 🔑 Guía: Cómo Obtener tu API Key de Groq

Audio2Text utiliza la API de Groq para transcripción de audio con el modelo Whisper Large v3. Esta guía te mostrará cómo obtener tu API key **gratuita**.

---

## 📋 Requisitos Previos

- Cuenta de email válida
- Navegador web
- 5 minutos de tiempo

---

## 🚀 Paso a Paso

### 1. Ir al Sitio de Groq

Abre tu navegador y ve a:

**🔗 https://console.groq.com**

### 2. Crear Cuenta

Si no tienes cuenta:

1. Haz clic en **"Sign Up"** (Registrarse)
2. Opciones disponibles:
   - **Google:** Usar cuenta de Google (más rápido)
   - **GitHub:** Usar cuenta de GitHub
   - **Email:** Registrarse con email

**Recomendación:** Usar Google o GitHub es más rápido.

### 3. Verificar Email (si usaste email)

1. Revisa tu bandeja de entrada
2. Busca email de Groq
3. Haz clic en el link de verificación
4. Completa el perfil si es necesario

### 4. Acceder a la Consola

Una vez logueado:

1. Verás el **Dashboard de Groq**
2. En el menú lateral izquierdo, busca **"API Keys"**
3. Haz clic en **"API Keys"**

### 5. Crear API Key

1. Haz clic en **"Create API Key"** (Crear API Key)
2. Dale un nombre descriptivo:
   - Ejemplo: `Audio2Text - Mi PC`
   - Ejemplo: `Audio2Text - Trabajo`
3. Haz clic en **"Create"** o **"Generate"**

### 6. Copiar la API Key

⚠️ **MUY IMPORTANTE:**

1. **Copia la API key INMEDIATAMENTE**
2. La key se muestra **UNA SOLA VEZ**
3. Si no la copias, tendrás que crear una nueva
4. Guárdala en un lugar seguro (temporalmente)

**Formato de la key:**
```
gsk_TU_API_KEY_AQUI
```

### 7. Configurar en Audio2Text

#### Opción A: Desde la Interfaz (Recomendado)

1. Abre **Audio2Text**
2. Ve a la pestaña **"Configuración"**
3. En el campo **"Groq API Key"**, pega tu key
4. Haz clic en **"Guardar Configuración"**
5. ✅ ¡Listo!

#### Opción B: Editar config.json Manualmente

1. Cierra Audio2Text si está abierto
2. Abre el archivo `config/config.json` con un editor de texto
3. Busca la línea:
   ```json
   "groq_api_key": "",
   ```
4. Pega tu key entre las comillas:
   ```json
   "groq_api_key": "TU_API_KEY_AQUI",
   ```
5. Guarda el archivo
6. Abre Audio2Text

---

## ✅ Verificar que Funciona

### Prueba Rápida:

1. Abre **Audio2Text**
2. Presiona el **hotkey** (por defecto F2)
3. Di algo en voz alta (ej: "Hola, esta es una prueba")
4. Presiona el hotkey nuevamente para detener
5. **Debe aparecer la transcripción**

Si aparece la transcripción: ✅ **¡Funciona!**

Si aparece un error: ⚠️ Ver sección de problemas abajo

---

## 🐛 Problemas Comunes

### Error: "Invalid API Key"

**Causa:** La API key es incorrecta o no se copió bien

**Solución:**
1. Verifica que copiaste la key completa
2. No debe tener espacios al inicio o final
3. Debe empezar con `gsk_`
4. Si no funciona, crea una nueva key

### Error: "Rate limit exceeded"

**Causa:** Excediste el límite gratuito

**Solución:**
1. Espera unos minutos
2. Revisa tu uso en: https://console.groq.com/usage
3. El plan gratuito tiene límites generosos pero no ilimitados

### Error: "Network error" o "Connection failed"

**Causa:** Problema de conexión a internet

**Solución:**
1. Verifica tu conexión a internet
2. Verifica que no haya firewall bloqueando
3. Intenta de nuevo en unos segundos

### La key no se guarda

**Causa:** Permisos de archivo o carpeta

**Solución:**
1. Ejecuta Audio2Text como administrador (una vez)
2. Verifica que la carpeta `config/` exista
3. Verifica permisos de escritura en la carpeta

---

## 💰 Límites del Plan Gratuito

Groq ofrece un plan gratuito muy generoso:

- **Requests por minuto:** ~30 (puede variar)
- **Requests por día:** ~14,400 (puede variar)
- **Tamaño de audio:** Hasta 25 MB por archivo
- **Duración:** Sin límite de tiempo de uso

**Para la mayoría de usuarios, el plan gratuito es más que suficiente.**

### ¿Necesitas más?

Si necesitas más capacidad:
1. Ve a https://console.groq.com/settings/billing
2. Revisa los planes de pago
3. Groq ofrece precios muy competitivos

---

## 🔒 Seguridad de tu API Key

### ✅ Buenas Prácticas:

1. **Nunca compartas tu API key** con nadie
2. **No la subas a GitHub** o repositorios públicos
3. **No la incluyas en capturas de pantalla**
4. **Rótala regularmente** (cada 3-6 meses)
5. **Usa keys diferentes** para diferentes proyectos/dispositivos

### ⚠️ Si tu key se compromete:

1. Ve a https://console.groq.com/keys
2. **Revoca** la key comprometida inmediatamente
3. **Crea una nueva** key
4. **Actualiza** Audio2Text con la nueva key

---

## 📊 Monitorear Uso

Para ver cuánto has usado:

1. Ve a https://console.groq.com/usage
2. Verás:
   - Requests realizados
   - Tokens consumidos
   - Gráficos de uso
   - Límites restantes

---

## 🎓 Recursos Adicionales

- **Documentación de Groq:** https://console.groq.com/docs
- **Modelos disponibles:** https://console.groq.com/docs/models
- **Pricing:** https://groq.com/pricing
- **Soporte de Groq:** https://console.groq.com/support

---

## ❓ Preguntas Frecuentes

### ¿Es realmente gratis?

Sí, Groq ofrece un plan gratuito generoso. No necesitas tarjeta de crédito para empezar.

### ¿Cuánto tiempo dura la key?

Las API keys no expiran, pero es buena práctica rotarlas cada cierto tiempo.

### ¿Puedo tener múltiples keys?

Sí, puedes crear varias keys para diferentes dispositivos o proyectos.

### ¿Groq guarda mis audios?

Según su política de privacidad, Groq procesa el audio pero no lo almacena permanentemente. Revisa: https://groq.com/privacy-policy/

### ¿Funciona sin internet?

No, Audio2Text necesita conexión a internet para enviar el audio a la API de Groq.

---

## 📞 Soporte

### Problemas con Groq:
- **Soporte de Groq:** https://console.groq.com/support
- **Documentación:** https://console.groq.com/docs

### Problemas con Audio2Text:
- **GitHub Issues:** https://github.com/CENFARG/Audio2Text/issues
- **Email:** soporte@cenf.com.ar

---

## 🎉 ¡Listo!

Ahora tienes tu API key de Groq configurada y puedes usar Audio2Text para transcribir audio en tiempo real.

**¡Disfruta transcribiendo!** 🎤✨

---

**Última actualización:** 2025-12-23  
**Versión de la guía:** 1.0  
**Compatible con:** Audio2Text v0.9.2+
