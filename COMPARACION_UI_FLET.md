# Comparación Sistemática: CustomTkinter vs Flet
**Fecha:** 2026-03-19
**Objetivo:** Asegurar que Flet sea idéntico a CustomTkinter en diseño y funcionalidad

---

## 1. TAMAÑO DE VENTANA

### CustomTkinter (ui/app.py líneas 56-57)
```python
self.geometry("500x400")  # Reducido de 550 a 400
self.minsize(400, 350)  # Reducido de 450x450 a 400x350
```

### Flet Actual (ui_flet/main.py líneas 1353-1358)
```python
page.window_width = 500
page.window_height = 400
page.window_max_width = 500  # ❌ PROBLEMA: Esto previene expansión
page.window_max_height = 400  # ❌ PROBLEMA: Esto previene expansión
page.window_min_width = 400
page.window_min_height = 350
```

**Problema:** El usuario quiere ventana más pequeña (~300x300)
**Estado:** ❌ INCORRECTO - Ventana demasiado grande

---

## 2. LAYOUT PRINCIPAL

### CustomTkinter (create_widgets líneas 108-132)
```python
# Tabview principal con padx=10, pady=(10, 5)
self.main_frame = ctk.CTkTabview(self)
self.main_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")

# 5 tabs:
- "Principal" (tab_main)
- "Configuración" (tab_settings)
- "Info" (tab_info)
- "Historial" (tab_history)
- "Actualizaciones" (tab_updates)

# Bottom frame con link CENF
self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
self.bottom_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
```

### Flet Actual
```python
# Tabs manuales con botones
# ❌ PROBLEMA: Botones son muy pequeños (width=100)
# ❌ PROBLEMA: Texto se corta en botones
# ❌ PROBLEMA: No hay padding correcto
```

**Problemas:**
- Botones de tabs muy pequeños (width=100)
- Texto "Configuración" se corta
- No se parece a CTkTabview visualmente
**Estado:** ❌ INCORRECTO - Tabs no funcionales visualmente

---

## 3. TAB PRINCIPAL - STATUS FRAME

### CustomTkinter (create_main_tab líneas 160-167)
```python
status_frame = ctk.CTkFrame(tab, fg_color="transparent")
status_frame.grid(row=0, column=0, pady=(10, 5), padx=15, sticky="ew")

# Status label - heading_large (20, bold)
self.status_label = ctk.CTkLabel(
    status_frame,
    text=self.localization_manager.get_string("status_ready"),
    font=DesignSystem.TYPOGRAPHY["heading_large"]  # ("Segoe UI", 20, "bold")
)

# Hotkey display - body_small (12, normal)
self.hotkey_display_label = ctk.CTkLabel(
    status_frame,
    text=self.localization_manager.get_string("hotkey_display", hotkey="F9"),
    font=DesignSystem.TYPOGRAPHY["body_small"]  # ("Segoe UI", 12, "normal")
)
```

### Flet Actual (create_main_tab)
```python
# ❌ PROBLEMA: No verificar qué tamaño de fuente usa
# ❌ PROBLEMA: Espaciado incorrecto
```

**Estado:** ⚠️ NECESITA VERIFICACIÓN

---

## 4. TAB PRINCIPAL - INFO FRAME

### CustomTkinter (líneas 187-193)
```python
info_frame = ctk.CTkFrame(tab, fg_color="transparent")
info_frame.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="ew")

# Audio size label
self.audio_size_label = ctk.CTkLabel(
    info_frame,
    text=self.localization_manager.get_string("audio_info", size="...", count="...")
)

# Log size label
self.log_size_label = ctk.CTkLabel(
    info_frame,
    text=self.localization_manager.get_string("transcriptions_info", size="...")
)
```

### Flet Actual
```python
# ❌ PROBLEMA: No verificar si existe o cómo se muestra
```

**Estado:** ⚠️ NECESITA VERIFICACIÓN

---

## 5. TAB PRINCIPAL - BUTTON FRAME

### CustomTkinter (líneas 196-200)
```python
button_frame = ctk.CTkFrame(tab, fg_color="transparent")
button_frame.grid(row=2, column=0, padx=15, pady=(0, 5), sticky="ew")
button_frame.grid_columnconfigure((0, 1, 2), weight=1)

# Botones con padx=5
ctk.CTkButton(
    button_frame,
    text=self.localization_manager.get_string("clear_audio_button"),
    command=self.clear_audio_with_feedback
).grid(row=0, column=0, padx=5, sticky="ew")

ctk.CTkButton(
    button_frame,
    text=self.localization_manager.get_string("clear_transcriptions_button"),
    command=self.clear_logs_with_feedback
).grid(row=0, column=1, padx=5, sticky="ew")
```

### Flet Actual
```python
# ❌ PROBLEMA: Botones pueden estar mal dimensionados
# ❌ PROBLEMA: Espaciado incorrecto
```

**Estado:** ⚠️ NECESITA VERIFICACIÓN

---

## 6. TAB PRINCIPAL - TRANSCRIPTION PANEL

### CustomTkinter (líneas 204-212)
```python
# Panel de Transcripción (row 3)
if self.config_manager.get("show_transcription_panel"):
    self.transcription_frame = ctk.CTkFrame(tab, fg_color="transparent")
    self.transcription_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")

    # Textbox con wrap="word", font=body_medium (14, normal)
    self.transcription_textbox = ctk.CTkTextbox(
        self.transcription_frame,
        wrap="word",
        font=DesignSystem.TYPOGRAPHY["body_medium"]  # ("Segoe UI", 14, "normal")
    )
    self.transcription_textbox.pack(expand=True, fill="both")
```

### Flet Actual
```python
# ❌ PROBLEMA: El usuario reporta que el área de transcripción cambia de tamaño
# ❌ PROBLEMA: No tiene dimensiones fijas
# ❌ PROBLEMA: La transcripción no se mostró (no funcionó)
```

**Estado:** ❌ INCORRECTO - No funciona, tamaño variable

---

## 7. TAB CONFIGURACIÓN

### CustomTkinter (create_config_tab líneas 217-249)
```python
# ScrollableFrame con fg_color="transparent"
scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
scroll_frame.pack(fill="both", expand=True)

# Main config frame
main_conf_frame = ctk.CTkFrame(scroll_frame)
main_conf_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

# Título con heading_medium (16, bold)
ctk.CTkLabel(
    main_conf_frame,
    text=self.localization_manager.get_string("settings_title_main"),
    font=DesignSystem.TYPOGRAPHY["heading_medium"]  # ("Segoe UI", 16, "bold")
)

# API Key status label (● grey/green/red, tamaño 20)
self.api_key_status_label = ctk.CTkLabel(
    main_conf_frame,
    text="●",
    font=("Segoe UI", 20),
    text_color="grey"
)

# API Key entry con show="*", placeholder_text
api_entry = ctk.CTkEntry(
    main_conf_frame,
    textvariable=self.api_key_var,
    show="*",
    placeholder_text=self.localization_manager.get_string("api_key_placeholder")
)

# Verify button width=70
verify_btn = ctk.CTkButton(
    main_conf_frame,
    text=self.localization_manager.get_string("verify_button"),
    width=70,
    command=self._check_api_key
)

# Hotkey combobox con state="readonly"
ctk.CTkComboBox(
    main_conf_frame,
    values=f_keys,
    variable=self.hotkey_var,
    state="readonly",
    command=lambda e: self.save_config()
)

# Record hotkey button width=70
record_hotkey_btn = ctk.CTkButton(
    main_conf_frame,
    text=self.localization_manager.get_string("record_hotkey_button"),
    width=70,
    command=self._start_hotkey_recording
)
```

### Flet Actual
```python
# ❌ PROBLEMA: No verificar si los campos están ocultos o mal mostrados
# ❌ PROBLEMA: El usuario dice "en configuración está todo configurado pero no se ve nada"
```

**Estado:** ❌ INCORRECTO - Campos no visibles

---

## 8. DISEÑO Y ESPACIADO

### CustomTkinter - Padding Summary:
```
Status frame:   pady=(10, 5), padx=15
Info frame:     padx=15, pady=(0, 5)
Button frame:   padx=15, pady=(0, 5)
Transcription:  padx=10, pady=(0, 10)

Config frames:  padx=10, pady=10
```

### Flet Actual - Padding:
```
# ❌ PROBLEMA: "todo está muy separado"
# ❌ PROBLEMA: No tiene diseño estético
```

**Estado:** ❌ INCORRECTO - Espaciado excesivo

---

## 9. COLORES

### CustomTkinter DesignSystem.COLORS:
```python
"primary": "#2563EB"
"primary_hover": "#1D4ED8"
"success": "#10B981"
"error": "#EF4444"
"warning": "#F59E0B"
"background": "#0F172A"
"surface": "#1E293B"
"text_primary": "#F8FAFC"
"text_secondary": "#CBD5E1"
```

### Flet Actual:
```python
# Usa ft.Colors.BLUE_GREY_900, BLUE_GREY_800, etc.
# ❌ PROBLEMA: No coincide exactamente con CustomTkinter
```

**Estado:** ⚠️ NECESITA VERIFICACIÓN

---

## 10. FUNCIONALIDAD - TRANSCRIPCIÓN

### CustomTkinter (funciona):
- ✅ Presionar F9 graba audio
- ✅ Transcripción se muestra en textbox
- ✅ Overlay muestra estado de grabación
- ✅ Auto-paste funciona (si está activado)

### Flet Actual (no funciona):
- ❌ "no funcionó la transcripción"
- ❌ "ahora no tradujo"

**Estado:** ❌ CRÍTICO - Funcionalidad rota

---

## LISTA DE PROBLEMAS IDENTIFICADOS

### CRÍTICOS (bloquean uso):
1. ❌ Transcripción no funciona
2. ❌ Traducción no funciona
3. ❌ Configuración no se ve ("todo configurado pero no se ve nada")

### ESTÉTICOS (afectan UX):
4. ❌ Ventana demasiado grande (usuario quiere ~300x300)
5. ❌ Tabs muy pequeños, texto se corta
6. ❌ Todo muy separado, sin estética
7. ❌ Layout vertical no compacto

### TÉCNICOS:
8. ❌ Área de transcripción cambia de tamaño
9. ❌ Padding/spacing incorrecto
10. ❌ Colores no coinciden exactamente

---

## PRÓXIMOS PASOS

1. **ANTES de hacer cambios:** Comparar cada componente uno a uno
2. **Lectura sistemática:**
   - Leer ui/app.py completo
   - Leer ui_flet/main.py completo
   - Comparar línea por línea
3. **Documentar diferencias**
4. **Corregir Flet para que coincida EXACTAMENTE**
5. **Probar funcionalidad**
6. **Recién después de probar, presentar al usuario**

---

## REQUERIMIENTOS DEL USUARIO

> " compara entre lo que hay en Sync y lo que hay en Flet y ver uno a uno si está igual,
> si tiene el mismo diseño, si tiene el mismo color, forma, contenido,
> si se vería exactamente igual. Y recién ahí después de que hagas toda esa comparación
> uno a uno entre Sync y Flet, lo desarrollemos y lo probemos"

**Acción requerida:** Hacer comparación exhaustiva ANTES de hacer cambios.
