# NVIDIA Riva ASR - Guía de Integración

## 📋 Resumen

Integración de **NVIDIA Riva** (modelo `parakeet-ctc-0.6b-es`) en Audio2Text como alternativa a Groq/Whisper.

**Ventajas:**
- ✅ Modelo especializado en español
- ✅ Soporta modo offline (local)
- ✅ Latencia baja con GPU NVIDIA
- ✅ Sin costes de API (modo local)

## 🚀 Opción 1: Modo Cloud (Requiere API Key)

### Requisitos
- API key de NVIDIA NGC (gratis)
- Conexión a internet
- Python 3.8+

### Instalación

1. **Generar API key:**
   - Ve a https://build.nvidia.com/
   - Regístrate y genera una API key gratuita

2. **Instalar dependencias:**
   ```bash
   pip install nvidia-riva-client grpcio grpcio-tools
   ```

3. **Configurar API key:**
   ```bash
   # Opción A: Variable de entorno
   export NVIDIA_API_KEY=tu_api_key_aqui

   # Opción B: Archivo .env
   echo "NVIDIA_API_KEY=tu_api_key_aqui" > .env
   ```

4. **Probar transcripción:**
   ```python
   from backend.nvidia_asr import NvidiaASRBuilder

   # Crear cliente cloud
   asr = NvidiaASRBuilder.cloud(api_key="tu_api_key")

   # Transcribir
   texto = asr.transcribe("audio.wav", language_code="es-US")
   print(texto)
   ```

## 🖥️ Opción 2: Modo Local (Docker + GPU NVIDIA)

### Requisitos
- **NVIDIA GPU** con soporte CUDA
- **NVIDIA Driver** instalado
- **Docker** con runtime nvidia
- **8GB+ RAM**
- **API key de NVIDIA NGC**

### Instalación en Windows

1. **Instalar WSL2 + NVIDIA GPU:**
   - Instala CUDA Toolkit para WSL2
   - Instala Docker Desktop con soporte WSL2
   - Habilita "Use the WSL 2 based engine"

2. **Generar API key:**
   - Ve a https://build.nvidia.com/
   - Regístrate y genera una API key

3. **Ejecutar script PowerShell:**
   ```powershell
   # Setear API key
   $env:NGC_API_KEY = "tu_api_key_aqui"

   # Ejecutar script
   powershell -ExecutionPolicy Bypass -File scripts/nvidia_local.ps1
   ```

4. **Esperar a que esté listo:**
   - El script descargará la imagen (30 min primera vez)
   - Monitorea con: `docker logs -f parakeet-ctc-0.6b-es`
   - Cuando vea "✓ ¡Servicio listo!" está listo

### Instalación en Linux/Mac

1. **Instalar Docker con NVIDIA runtime:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install docker.io nvidia-container-toolkit

   # CentOS/RHEL
   sudo yum install docker nvidia-container-toolkit
   ```

2. **Generar API key:**
   - Ve a https://build.nvidia.com/
   - Regístrate y genera una API key

3. **Ejecutar script bash:**
   ```bash
   # Setear API key
   export NGC_API_KEY="tu_api_key_aqui"

   # Ejecutar script
   bash scripts/nvidia_local.sh
   ```

4. **Verificar que funcionó:**
   ```bash
   curl http://localhost:9000/v1/health/ready
   # Debe devolver: {"ready":true}
   ```

## 🔧 Configuración en Audio2Text

### Agregar a config.json:

```json
{
  "transcription_engine": "nvidia",
  "nvidia": {
    "mode": "local",
    "server": "localhost:50051",
    "api_key": "",
    "language_code": "es-US"
  }
}
```

O para modo cloud:

```json
{
  "transcription_engine": "nvidia",
  "nvidia": {
    "mode": "cloud",
    "api_key": "tu_api_key_aqui",
    "language_code": "es-US"
  }
}
```

## 📊 Comparación de Modos

| Característica | Cloud | Local |
|----------------|-------|--------|
| Costo | Free tier | Gratis (local) |
| Latencia | 100-300ms | 50-150ms |
| Requiere GPU | No | **Sí** |
| Requiere Internet | **Sí** | No |
| Privacidad | Enviar audio a NVIDIA | 100% local |
| Setup | 5 minutos | 30 minutos |

## 🐛 Solución de Problemas

### Error: "nvidia-smi no encontrado"
**Solución:** Instala NVIDIA drivers para tu GPU

### Error: "Login falló"
**Solución:** Verifica que la API key sea correcta

### Error: "Contenedor no inicia"
**Solución:**
```bash
# Ver logs de Docker
docker logs parakeet-ctc-0.6b-es

# Verificar GPU
nvidia-smi
```

### Error: "Servicio no está listo"
**Solución:** Espera más tiempo (hasta 30 min primera vez)

## 📚 Referencias

- [NVIDIA Riva Documentation](https://docs.nvidia.com/deeplearning/riva/)
- [NVIDIA NIM Catalog](https://build.nvidia.com/)
- [parakeet-ctc-0.6b-es Model Card](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/riva/models/parakeet-ctc-0_6b-es)
