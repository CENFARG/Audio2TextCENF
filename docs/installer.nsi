; Audio2Text_CENF_0.9.2_Installer.nsi
; Script de instalación NSIS para Audio2Text CENF v0.9.2
; Este instalador reduce las advertencias de SmartScreen al proporcionar metadatos completos

;--------------------------------
; Includes

  !include "MUI2.nsh"
  !include "FileFunc.nsh"

;--------------------------------
; Configuración General

  ; Nombre del instalador
  Name "Audio2Text CENF 0.9.2"
  
  ; Archivo de salida
  OutFile "..\Audio2Text_CENF_0.9.2_Setup.exe"
  
  ; Carpeta de instalación por defecto
  InstallDir "$PROGRAMFILES64\CENF\Audio2Text"
  
  ; Obtener carpeta de instalación desde el registro si es posible
  InstallDirRegKey HKLM "Software\CENF\Audio2Text" "Install_Dir"
  
  ; Solicitar privilegios de administrador
  RequestExecutionLevel admin
  
  ; Información de versión
  VIProductVersion "0.9.2.0"
  VIAddVersionKey "ProductName" "Audio2Text CENF"
  VIAddVersionKey "ProductVersion" "0.9.2"
  VIAddVersionKey "CompanyName" "CENF - Centro de Excelencia en Negocios del Futuro"
  VIAddVersionKey "LegalCopyright" "© 2024 CENF. Todos los derechos reservados."
  VIAddVersionKey "FileDescription" "Instalador de Audio2Text CENF - Transcripción de Audio"
  VIAddVersionKey "FileVersion" "0.9.2.0"

;--------------------------------
; Interfaz

  !define MUI_ABORTWARNING
  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
  !define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
  
  ; Página de bienvenida
  !insertmacro MUI_PAGE_WELCOME
  
  ; Página de licencia (opcional)
  ; !insertmacro MUI_PAGE_LICENSE "license.txt"
  
  ; Página de directorio de instalación
  !insertmacro MUI_PAGE_DIRECTORY
  
  ; Página de instalación
  !insertmacro MUI_PAGE_INSTFILES
  
  ; Página de finalización
  !define MUI_FINISHPAGE_RUN "$INSTDIR\Audio2Text_CENF_0.9.2_GENERAL.exe"
  !define MUI_FINISHPAGE_RUN_TEXT "Ejecutar Audio2Text ahora"
  !insertmacro MUI_PAGE_FINISH
  
  ; Páginas del desinstalador
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Idiomas

  !insertmacro MUI_LANGUAGE "Spanish"

;--------------------------------
; Sección de Instalación

Section "Audio2Text CENF" SecMain

  SetOutPath "$INSTDIR"
  
  ; Copiar ejecutable desde dist/
  File "..\dist\Audio2Text_CENF_0.9.2_GENERAL.exe"
  
  ; Copiar assets
  File "..\assets\icons\icono.ico"
  File "..\assets\logos\logo.png"
  
  ; Copiar configuración
  File "..\config\config.json"
  
  ; Copiar template
  File "..\templates\info_template.html"
  
  ; Copiar carpeta de idiomas
  SetOutPath "$INSTDIR\lang"
  File "..\lang\*.json"
  
  ; Crear carpetas de datos del usuario
  CreateDirectory "$APPDATA\CENF\Audio2Text"
  CreateDirectory "$APPDATA\CENF\Audio2Text\audio"
  CreateDirectory "$APPDATA\CENF\Audio2Text\logs"
  
  ; Escribir información de des instalación en el registro
  WriteRegStr HKLM "Software\CENF\Audio2Text" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF" "DisplayName" "Audio2Text CENF 0.9.2"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF" "DisplayIcon" "$INSTDIR\icono.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF" "Publisher" "CENF"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF" "DisplayVersion" "0.9.2"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF" "NoRepair" 1
  
  ; Crear desinstalador
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Crear accesos directos en el menú inicio
  CreateDirectory "$SMPROGRAMS\CENF"
  CreateShortcut "$SMPROGRAMS\CENF\Audio2Text.lnk" "$INSTDIR\Audio2Text_CENF_0.9.2_GENERAL.exe" "" "$INSTDIR\icono.ico"
  CreateShortcut "$SMPROGRAMS\CENF\Desinstalar Audio2Text.lnk" "$INSTDIR\uninstall.exe"
  
  ; Crear acceso directo en el escritorio (opcional)
  CreateShortcut "$DESKTOP\Audio2Text CENF.lnk" "$INSTDIR\Audio2Text_CENF_0.9.2_GENERAL.exe" "" "$INSTDIR\icono.ico"

SectionEnd

;--------------------------------
; Sección de Desinstalación

Section "Uninstall"

  ; Eliminar archivos
  Delete "$INSTDIR\Audio2Text_CENF_0.9.2_GENERAL.exe"
  Delete "$INSTDIR\icono.ico"
  Delete "$INSTDIR\logo.png"
  Delete "$INSTDIR\config.json"
  Delete "$INSTDIR\info_template.html"
  Delete "$INSTDIR\lang\*.json"
  RMDir "$INSTDIR\lang"
  Delete "$INSTDIR\uninstall.exe"
  
  ; Eliminar directorio de instalación
  RMDir "$INSTDIR"
  
  ; Eliminar accesos directos
  Delete "$SMPROGRAMS\CENF\Audio2Text.lnk"
  Delete "$SMPROGRAMS\CENF\Desinstalar Audio2Text.lnk"
  RMDir "$SMPROGRAMS\CENF"
  Delete "$DESKTOP\Audio2Text CENF.lnk"
  
  ; Eliminar claves del registro
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Audio2Text_CENF"
  DeleteRegKey HKLM "Software\CENF\Audio2Text"
  
  ; Nota: No eliminamos los datos del usuario en $APPDATA por seguridad
  ; Si el usuario quiere eliminarlos, debe hacerlo manualmente

SectionEnd

;--------------------------------
; Descripciones de Secciones (opcional)

  LangString DESC_SecMain ${LANG_SPANISH} "Instala Audio2Text CENF 0.9.2 y sus componentes necesarios."

  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END
