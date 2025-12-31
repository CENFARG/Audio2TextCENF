# Política de Seguridad

## Versiones Soportadas

Actualmente damos soporte de seguridad a las siguientes versiones de Audio2Text:

| Versión | Soportada          |
| ------- | ------------------ |
| 0.9.2   | :white_check_mark: |
| 0.9.0   | :x:                |
| < 0.9.0 | :x:                |

## Reportar una Vulnerabilidad

La seguridad de Audio2Text es una prioridad. Si descubres una vulnerabilidad de seguridad, por favor ayúdanos siguiendo estos pasos:

### 🔒 Proceso de Reporte Confidencial

**NO** crees un issue público en GitHub para vulnerabilidades de seguridad.

En su lugar, por favor reporta las vulnerabilidades de seguridad a:

**Email:** seguridad@cenfarg.com.ar

### 📋 Información a Incluir

Para ayudarnos a entender y resolver el problema rápidamente, por favor incluye:

1. **Descripción del problema:**
   - Tipo de vulnerabilidad (ej: XSS, SQL injection, etc.)
   - Ubicación del código afectado (archivo y línea si es posible)
   - Configuración especial requerida para reproducir

2. **Pasos para reproducir:**
   - Instrucciones paso a paso
   - Código de prueba de concepto (PoC) si es aplicable
   - Capturas de pantalla o videos si ayudan

3. **Impacto potencial:**
   - ¿Qué puede hacer un atacante?
   - ¿Qué datos están en riesgo?
   - ¿Cuántos usuarios están afectados?

4. **Información del sistema:**
   - Versión de Audio2Text
   - Sistema operativo
   - Versión de Python
   - Cualquier otra información relevante

### ⏱️ Tiempo de Respuesta

- **Confirmación inicial:** Dentro de 48 horas
- **Evaluación preliminar:** Dentro de 5 días hábiles
- **Actualizaciones regulares:** Cada 7 días hasta la resolución

### 🛡️ Proceso de Divulgación

Seguimos el principio de **divulgación responsable**:

1. **Investigación:** Evaluamos y verificamos el reporte (1-5 días)
2. **Desarrollo:** Creamos y probamos un fix (variable según severidad)
3. **Notificación:** Informamos a usuarios afectados si es necesario
4. **Release:** Publicamos la versión corregida
5. **Divulgación:** Publicamos detalles después de que usuarios tengan tiempo de actualizar (típicamente 30 días)

### 🏆 Reconocimiento

Agradecemos a los investigadores de seguridad que reportan vulnerabilidades responsablemente:

- Incluiremos tu nombre en nuestro [Hall of Fame de Seguridad](docs/SECURITY_HALL_OF_FAME.md) (si lo deseas)
- Te daremos crédito en las notas de la versión (con tu permiso)

## 🔐 Mejores Prácticas de Seguridad para Usuarios

### Configuración Segura

1. **API Keys:**
   - Nunca compartas tu Groq API key
   - Usa variables de entorno o `config.json` (no versionado)
   - Rota tus keys regularmente

2. **Actualizaciones:**
   - Mantén Audio2Text actualizado
   - Suscríbete a notificaciones de releases en GitHub

3. **Permisos:**
   - Ejecuta con permisos mínimos necesarios
   - No ejecutes como administrador a menos que sea necesario

### Datos Sensibles

- Audio2Text **NO** envía datos de transcripción a servidores de CENF
- Las transcripciones se envían solo a Groq API (según su [política de privacidad](https://groq.com/privacy-policy/))
- Los archivos de audio se guardan localmente
- No se recopila telemetría ni analytics

### Verificación de Ejecutables

Antes de ejecutar el `.exe` descargado:

1. Verifica el hash SHA256:
   ```powershell
   Get-FileHash Audio2Text_CENF_0.9.2_GENERAL.exe -Algorithm SHA256
   ```

2. Compara con el hash publicado en el [Release](https://github.com/CENFARG/Audio2Text/releases)

3. Descarga solo de fuentes oficiales:
   - GitHub Releases: https://github.com/CENFARG/Audio2Text/releases
   - Sitio oficial: https://cenf.com.ar

## 🚨 Vulnerabilidades Conocidas

Actualmente no hay vulnerabilidades conocidas en la versión 0.9.2.

Historial de vulnerabilidades corregidas:
- Ninguna hasta la fecha

## 📞 Contacto

Para consultas de seguridad:

- **Email de Seguridad:** seguridad@cenf.com.ar
- **Email General:** soporte@cenf.com.ar
- **GitHub:** [@CENFARG](https://github.com/CENFARG)

## 📚 Recursos Adicionales

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [CVE - Common Vulnerabilities and Exposures](https://cve.mitre.org/)

---

**Última actualización:** 2025-12-23  
**Versión de la política:** 1.0
