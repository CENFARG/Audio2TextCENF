# Guía de Pruebas Manuales — Audio2Text v0.16.0-rc

> Para: GR · Última actualización: 2026-09-25
> Alcance: F1 Archivos · F2 Supervisor · F3 Hotkey · Grabación clásica · Configuración

## 0. Preparación (una vez)

```powershell
cd C:\Dropbox\DOC.RECA\06-Software\Audio2Text
.venv\Scripts\Activate.ps1
pip install -r requirements.txt        # incluye tkinterdnd2 (drag & drop)
python scripts/check_version.py        # debe decir: All version sources PASS
python main.py
```

Si falta la API key, la app lo avisa: cargala desde Configuración (sin tildes ni símbolos
raros — si pegás una key con caracteres inválidos, ahora la app te lo dice con un mensaje
claro en vez de fallar feo).

---

## 1. Pestaña Archivos (ahora dentro de Principal, abajo)

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1.1 | Sección "Archivos" al fondo de la pestaña Principal | Marco con título, cola visible (ya no hay pestaña separada) |
| 1.2 | Botón cargar → elegí 1 mp3/wav corto | El archivo entra a la cola como "pendiente" |
| 1.3 | Arrastrá un audio desde el Explorador sobre la ventana | Entra a la cola (si no funciona: `pip install tkinterdnd2` en el venv) |
| 1.4 | Copiá un archivo de audio en el Explorador (Ctrl+C) y en la app presioná pegar | Entra a la cola |
| 1.5 | Presioná transcribir | Estado por archivo: pendiente → transcribiendo → listo; texto en el área principal + entrada en Historial |
| 1.6 | Importá un OGG de WhatsApp | Rechazado AL IMPORTAR con razón clara ("unreadable") — no a mitad de transcripción |
| 1.7 | Si un archivo falla, mirá su fila | Debe mostrar el motivo del error (no solo "falló") |

## 2. Pestaña Supervisor

| Paso | Acción | Resultado esperado |
|---|---|---|
| 2.1 | Pestaña "Supervisor" → botón Nueva respuesta | Entrada numerada nueva (1, 2, 3...) |
| 2.2 | Pegá parte de una respuesta de tu IA entre comillas, después `:`, después tu corrección | El texto queda guardado automáticamente (mirá `supervisor_entries.json` en la raíz) |
| 2.3 | Selectbox de bloques → elegí uno (ej: supervision) → insertar | El cuerpo del bloque se inserta en la respuesta donde estaba el cursor |
| 2.4 | Botón grabar del fragmento → hablá → cortar | El texto transcrito se agrega a la respuesta de esa entrada |
| 2.5 | Botón "Copiar respuesta N" | Portapapeles = `N. "cita"` + `:` + tu corrección, listo para pegar en el TUI del agente |
| 2.6 | Botón "Copiar todo" | Portapapeles = TODAS las entradas numeradas en orden |
| 2.7 | Marcar "enviada" | Estado cambia a enviada; podés reabrirla |
| 2.8 | Borrar una entrada | Pide confirmación; los números restantes NO se renumeran |
| 2.9 | Cerrá la app a lo bruto (Alt+F4) y reabrí | TODAS las entradas siguen ahí (auto-save) |

## 3. Hotkey global (F3)

| Paso | Acción | Resultado esperado |
|---|---|---|
| 3.1 | Copiá cualquier texto (en cualquier app) → presioná `Ctrl+Alt+V` | Entrada nueva en el Supervisor con ese texto, mensaje de confirmación |
| 3.2 | Sin cambiar el portapapeles, presioná `Ctrl+Alt+V` de nuevo | NO crea entrada nueva: REEMPLAZA la última (anti-duplicado) |
| 3.3 | Cambiá el portapapeles y repetí | Entrada nueva |

## 4. Grabación clásica (regresión)

| Paso | Acción | Resultado esperado |
|---|---|---|
| 4.1 | Hotkey de grabación (F8/F9 según config) → hablá ~30s → hotkey | Transcripción normal, sin texto duplicado (fix de la transcripción doble) |
| 4.2 | Repetí con ~45s | Igual: las grabaciones cortas ya no streamean la cola |

## 5. Configuración

| Paso | Acción | Resultado esperado |
|---|---|---|
| 5.1 | Configuración → campo "Carpeta de bloques de contexto" | Visible y editable; apunta a `.amBotHs\contextBlocks` |
| 5.2 | Pegá una API key con una tilde a propósito y guardá | Mensaje amigable de caracteres inválidos (no crash ascii) |

## 6. Al terminar

Reportá cualquier desvío de esta tabla con el paso exacto. Todo verde = GO para
consolidación (merge a main + v0.16.0).
