# 🚀 Inicio Rápido: Crear Instalador MSI

## ¿Qué es installer.wxs?

`installer.wxs` es un archivo de configuración para **WiX Toolset** que define cómo crear un instalador MSI profesional para Windows.

---

## 📋 Requisitos Previos

### 1. Instalar WiX Toolset

**Descargar:**
- Ve a: https://wixtoolset.org/releases/
- Descarga: **WiX Toolset v3.11.2** (versión estable)
- Ejecuta el instalador
- Sigue las instrucciones

**Verificar instalación:**
```powershell
candle -?
```

Si muestra la ayuda, está instalado correctamente.

### 2. Compilar el Ejecutable

Antes de crear el MSI, necesitas el `.exe`:

```bash
# Compilar la variante que quieras
python scripts/build_GENERAL_v2.py

# Verificar que existe
dir dist\Audio2Text_CENF_0.9.2_GENERAL.exe
```

---

## 🎯 Uso Rápido (3 Pasos)

### Paso 1: Compilar el WiX Source

```powershell
# Desde la raíz del proyecto
cd C:\Dropbox\DOC.RECA\06-Software\Audio2Text

# Crear carpeta build si no existe
if (-not (Test-Path "build")) { New-Item -ItemType Directory -Path "build" }

# Compilar el .wxs a .wixobj
candle installer.wxs -out build\installer.wixobj
```

**Salida esperada:**
```
Windows Installer XML Toolset Compiler version 3.11.2.4516
installer.wxs
```

### Paso 2: Enlazar y Crear el MSI

```powershell
# Crear el instalador MSI
light build\installer.wixobj -out Audio2Text_CENF_0.9.2_Setup.msi -ext WixUIExtension
```

**Salida esperada:**
```
Windows Installer XML Toolset Linker version 3.11.2.4516
```

### Paso 3: Verificar el MSI

```powershell
# Ver el archivo creado
dir *.msi

# Debe mostrar: Audio2Text_CENF_0.9.2_Setup.msi (~80-120 MB)
```

---

## ✅ ¡Listo!

Ahora tienes `Audio2Text_CENF_0.9.2_Setup.msi` listo para distribuir.

### Probar el Instalador:

1. **Doble clic** en el `.msi`
2. Sigue el asistente de instalación
3. Verifica que se instale en `C:\Program Files\CENF\Audio2Text\`
4. Verifica accesos directos (Inicio + Escritorio)

---

## 🔧 Script Automatizado (Recomendado)

Crea `build_msi.ps1`:

```powershell
# Build MSI Script
Write-Host "🔨 Building MSI installer..." -ForegroundColor Cyan

# Verificar WiX
if (-not (Get-Command candle -ErrorAction SilentlyContinue)) {
    Write-Host "❌ WiX Toolset not found!" -ForegroundColor Red
    Write-Host "Download from: https://wixtoolset.org/releases/" -ForegroundColor Yellow
    exit 1
}

# Crear carpeta build
if (-not (Test-Path "build")) {
    New-Item -ItemType Directory -Path "build" | Out-Null
}

# Compilar
Write-Host "📋 Compiling WiX source..." -ForegroundColor Yellow
candle installer.wxs -out "build\installer.wixobj"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Compilation failed!" -ForegroundColor Red
    exit 1
}

# Enlazar
Write-Host "🔗 Linking MSI..." -ForegroundColor Yellow
light "build\installer.wixobj" -out "Audio2Text_CENF_0.9.2_Setup.msi" -ext WixUIExtension

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Linking failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ MSI created successfully!" -ForegroundColor Green
Write-Host "📦 File: Audio2Text_CENF_0.9.2_Setup.msi" -ForegroundColor Cyan
```

**Uso:**
```powershell
.\build_msi.ps1
```

---

## 🎨 Personalizar el Instalador

### Cambiar el Ejecutable (para otras variantes)

Edita `installer.wxs`, línea ~70:

```xml
<!-- Cambiar de GENERAL a CONTRERAS o CUTIGNOLA -->
<File Source="dist\Audio2Text_CENF_0.9.2_CONTRERAS.exe" ...>
```

### Cambiar el Nombre del Producto

Edita `installer.wxs`, línea ~14:

```xml
<Product Name="Audio2Text CONTRERAS" ...>
```

### Cambiar el Logo

Edita `installer.wxs`, línea ~100:

```xml
<File Source="assets\logos\logo_contreras.png" ...>
```

---

## 🐛 Problemas Comunes

### Error: "candle: command not found"

**Solución:**
```powershell
# Agregar WiX al PATH
$env:Path += ";C:\Program Files (x86)\WiX Toolset v3.11\bin"
```

### Error: "The system cannot find the file specified"

**Solución:**
1. Verifica que el `.exe` existe en `dist/`
2. Verifica que todos los archivos referenciados existen
3. Usa rutas relativas desde la raíz del proyecto

### Advertencias ICE

Son advertencias de validación de Windows Installer. Puedes ignorarlas si el MSI funciona.

Para suprimirlas:
```powershell
light ... -sice:ICE61 -sice:ICE69
```

---

## 📚 Guía Completa

Para más detalles, ver: **`docs/GUIA_INSTALADOR_MSI.md`**

Incluye:
- Explicación detallada de WiX
- Personalización avanzada
- Crear variantes (CONTRERAS, CUTIGNOLA)
- Troubleshooting completo
- Comparación MSI vs NSIS

---

## 📊 Comparación Rápida

| Característica | MSI (WiX) | NSIS |
|----------------|-----------|------|
| Estándar Windows | ✅ Nativo | ⚠️ Tercero |
| Desinstalación | ✅ Automática | ⚠️ Manual |
| Complejidad | ⚠️ Alta | ✅ Media |
| Tamaño | ⚠️ Mayor | ✅ Menor |

**Recomendación:**
- **MSI:** Para clientes empresariales (más profesional)
- **NSIS:** Para usuarios finales (más simple)

---

## ✅ Checklist

Antes de distribuir el MSI:

- [ ] ✅ WiX Toolset instalado
- [ ] ✅ Ejecutable compilado en `dist/`
- [ ] ✅ MSI compila sin errores
- [ ] ✅ Instalación probada en máquina limpia
- [ ] ✅ Aplicación funciona después de instalar
- [ ] ✅ Desinstalación limpia
- [ ] ✅ Accesos directos funcionan

---

**¡Listo para distribución profesional!** 🚀

---

**Última actualización:** 2025-12-23  
**Versión:** 1.0  
**Compatible con:** WiX Toolset v3.11+
