# 📦 Guía: Crear Instalador MSI para Windows

Esta guía te mostrará cómo crear un instalador MSI profesional para Audio2Text usando WiX Toolset.

---

## 📋 Requisitos Previos

### 1. WiX Toolset

**Descargar e Instalar:**

1. Ve a: https://wixtoolset.org/releases/
2. Descarga **WiX Toolset v3.11.2** (versión estable)
3. Ejecuta el instalador
4. Sigue las instrucciones

**Verificar instalación:**
```powershell
candle -?
```

Debe mostrar la ayuda de WiX.

### 2. Ejecutables Compilados

Antes de crear el MSI, debes tener los `.exe` compilados:

```bash
# Compilar la variante GENERAL
python scripts/build_GENERAL_v2.py

# Verificar que existe
dir dist\Audio2Text_CENF_0.9.2_GENERAL.exe
```

### 3. Licencia en formato RTF (Opcional)

Para mostrar la licencia en el instalador:

```bash
# Convertir LICENSE a RTF
# Puedes usar Word, LibreOffice, o un convertidor online
# Guardar como: docs\LICENSE.rtf
```

---

## 🚀 Crear el Instalador MSI

### Paso 1: Preparar el Proyecto

El archivo `installer.wxs` ya está creado en la raíz del proyecto.

**Estructura esperada:**
```
Audio2Text/
├── installer.wxs          # ← Configuración WiX
├── dist/
│   └── Audio2Text_CENF_0.9.2_GENERAL.exe
├── assets/
│   ├── icons/icono.ico
│   └── logos/logo.png
├── config/config.json
├── lang/
│   ├── es.json
│   └── en.json
├── templates/info_template.html
├── docs/
│   ├── INSTALACION.md
│   ├── GUIA_SMARTSCREEN.md
│   ├── GUIA_API_KEY_GROQ.md
│   └── LICENSE.rtf (opcional)
├── README.md
├── LICENSE
└── CHANGELOG.md
```

### Paso 2: Compilar el WiX Source

```powershell
# Navegar a la raíz del proyecto
cd C:\Dropbox\DOC.RECA\06-Software\Audio2Text

# Compilar el archivo .wxs a .wixobj
candle installer.wxs -out build\installer.wixobj
```

**Salida esperada:**
```
Windows Installer XML Toolset Compiler version 3.11.2.4516
Copyright (c) .NET Foundation and contributors. All rights reserved.

installer.wxs
```

### Paso 3: Enlazar y Crear el MSI

```powershell
# Crear el instalador MSI
light build\installer.wixobj -out Audio2Text_CENF_0.9.2_Setup.msi -ext WixUIExtension
```

**Salida esperada:**
```
Windows Installer XML Toolset Linker version 3.11.2.4516
Copyright (c) .NET Foundation and contributors. All rights reserved.
```

### Paso 4: Verificar el MSI

```powershell
# Verificar que se creó
dir Audio2Text_CENF_0.9.2_Setup.msi

# Ver propiedades
Get-Item Audio2Text_CENF_0.9.2_Setup.msi | Format-List
```

---

## 🎨 Personalizar el Instalador

### Cambiar el Logo

Edita `installer.wxs`:

```xml
<!-- Cambiar el icono -->
<Icon Id="icon.ico" SourceFile="assets\icons\TU_ICONO.ico"/>
```

### Cambiar Información del Producto

```xml
<Product 
  Name="Audio2Text CENF" 
  Manufacturer="TU EMPRESA" 
  Version="0.9.2.0">
```

### Agregar Más Archivos

```xml
<Component Id="NuevoComponente" Guid="*">
  <File Id="NuevoArchivo" Source="ruta\al\archivo.ext" KeyPath="yes" />
</Component>
```

### Cambiar Directorio de Instalación

```xml
<Directory Id="INSTALLFOLDER" Name="TU_NOMBRE_CARPETA" />
```

---

## 🧪 Probar el Instalador

### Instalación

1. **Doble clic** en `Audio2Text_CENF_0.9.2_Setup.msi`
2. Sigue el asistente:
   - Acepta la licencia
   - Elige la carpeta de instalación
   - Haz clic en "Install"
3. Verifica que se crearon:
   - ✅ Acceso directo en Inicio
   - ✅ Acceso directo en Escritorio
   - ✅ Archivos en `C:\Program Files\CENF\Audio2Text\`

### Ejecución

1. Abre Audio2Text desde el acceso directo
2. Verifica que funciona correctamente
3. Configura la API key de Groq

### Desinstalación

**Opción 1: Panel de Control**
1. Panel de Control → Programas → Desinstalar un programa
2. Busca "Audio2Text CENF"
3. Haz clic en "Desinstalar"

**Opción 2: Configuración de Windows**
1. Configuración → Aplicaciones
2. Busca "Audio2Text"
3. Haz clic en "Desinstalar"

**Verificar:**
- ✅ Archivos eliminados de Program Files
- ✅ Accesos directos eliminados
- ✅ Entradas de registro limpiadas

---

## 📦 Crear Variantes del Instalador

### Para CONTRERAS:

1. Edita `installer.wxs`:
   ```xml
   <Product Name="Audio2Text CONTRERAS" ...>
   <File Source="dist\Audio2Text_CENF_0.9.2_CONTRERAS.exe" ...>
   <File Source="assets\logos\logo_contreras.png" ...>
   ```

2. Compila:
   ```powershell
   candle installer.wxs -out build\installer_contreras.wixobj
   light build\installer_contreras.wixobj -out Audio2Text_CONTRERAS_0.9.2_Setup.msi -ext WixUIExtension
   ```

### Para CUTIGNOLA:

Similar al anterior, cambiando los nombres y rutas correspondientes.

---

## 🔧 Solución de Problemas

### Error: "candle: command not found"

**Causa:** WiX no está en el PATH

**Solución:**
```powershell
# Agregar WiX al PATH temporalmente
$env:Path += ";C:\Program Files (x86)\WiX Toolset v3.11\bin"

# O permanentemente (como administrador)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files (x86)\WiX Toolset v3.11\bin", "Machine")
```

### Error: "The system cannot find the file specified"

**Causa:** Rutas incorrectas en installer.wxs

**Solución:**
1. Verifica que todos los archivos existen
2. Usa rutas relativas desde la raíz del proyecto
3. Verifica que el .exe está en `dist/`

### Error: "light.exe : error LGHT0001"

**Causa:** Problema al enlazar

**Solución:**
```powershell
# Limpiar y recompilar
Remove-Item build\*.wixobj -Force
candle installer.wxs -out build\installer.wixobj
light build\installer.wixobj -out Audio2Text_Setup.msi -ext WixUIExtension -sval
```

El flag `-sval` omite validaciones (solo para debugging).

### Advertencia: "ICE" warnings

**Causa:** Validaciones de Windows Installer

**Solución:**
- La mayoría son advertencias, no errores
- Puedes ignorarlas si el MSI funciona
- Para suprimirlas: `light ... -sice:ICEXX` (donde XX es el número)

---

## 🎯 Script Automatizado

Crea `build_msi.ps1`:

```powershell
# Build MSI Script for Audio2Text
param(
    [string]$Variant = "GENERAL"
)

Write-Host "🔨 Building MSI for variant: $Variant" -ForegroundColor Cyan

# Verificar WiX
if (-not (Get-Command candle -ErrorAction SilentlyContinue)) {
    Write-Host "❌ WiX Toolset not found!" -ForegroundColor Red
    exit 1
}

# Crear carpeta build
if (-not (Test-Path "build")) {
    New-Item -ItemType Directory -Path "build" | Out-Null
}

# Compilar
Write-Host "📋 Compiling WiX source..." -ForegroundColor Yellow
candle installer.wxs -out "build\installer_$Variant.wixobj"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Compilation failed!" -ForegroundColor Red
    exit 1
}

# Enlazar
Write-Host "🔗 Linking MSI..." -ForegroundColor Yellow
light "build\installer_$Variant.wixobj" `
    -out "Audio2Text_${Variant}_0.9.2_Setup.msi" `
    -ext WixUIExtension

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Linking failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ MSI created successfully!" -ForegroundColor Green
Write-Host "📦 File: Audio2Text_${Variant}_0.9.2_Setup.msi" -ForegroundColor Cyan
```

**Uso:**
```powershell
.\build_msi.ps1 -Variant GENERAL
.\build_msi.ps1 -Variant CONTRERAS
.\build_msi.ps1 -Variant CUTIGNOLA
```

---

## 📊 Comparación: MSI vs NSIS

| Característica | MSI (WiX) | NSIS |
|----------------|-----------|------|
| Estándar Windows | ✅ Nativo | ⚠️ Tercero |
| Desinstalación | ✅ Automática | ⚠️ Manual |
| Actualizaciones | ✅ Integradas | ❌ No |
| Group Policy | ✅ Soportado | ❌ No |
| Complejidad | ⚠️ Alta | ✅ Media |
| Tamaño | ⚠️ Mayor | ✅ Menor |
| Personalización | ⚠️ Limitada | ✅ Total |

**Recomendación:** 
- **MSI:** Para distribución enterprise/corporativa
- **NSIS:** Para distribución a usuarios finales

---

## 🎓 Recursos

- **WiX Tutorial:** https://www.firegiant.com/wix/tutorial/
- **WiX Documentation:** https://wixtoolset.org/documentation/
- **WiX on GitHub:** https://github.com/wixtoolset/wix3

---

## ✅ Checklist Final

Antes de distribuir el MSI:

- [ ] ✅ Ejecutable compilado y probado
- [ ] ✅ Todos los archivos necesarios presentes
- [ ] ✅ Licencia en formato RTF (opcional)
- [ ] ✅ MSI compila sin errores
- [ ] ✅ Instalación probada en máquina limpia
- [ ] ✅ Aplicación funciona después de instalar
- [ ] ✅ Desinstalación limpia
- [ ] ✅ Accesos directos funcionan
- [ ] ✅ Versión correcta en propiedades

---

**¡Listo para distribución profesional!** 🚀

---

**Última actualización:** 2025-12-23  
**Versión:** 1.0  
**Compatible con:** WiX Toolset v3.11+
