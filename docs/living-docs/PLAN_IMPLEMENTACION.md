# Plan de Implementación - Audio2Text v0.10.0

> **Fecha:** 2026-03-13
> **Versión objetivo:** 0.10.0
> **Estado:** Planificación
> **Estimación:** Q2 2026 (8-12 semanas)

---

## 📋 RESUMEN EJECUTIVO

Este plan detalla la implementación de las mejoras críticas propuestas por Pablo para Audio2Text, enfocándose en:

1. **Post-procesamiento de transcripciones** - Calidad de transcripción tipo ChatGPT
2. **Migración a Flet** - UI moderna basada en Flutter
3. **Corrección UTF-8** - Solución definitiva a tildes y ñ
4. **Reactivación de overlay** - UI de grabación visible
5. **Arreglo de actualizaciones** - Sistema de updates funcional
6. **Gestión de archivos** - Límites y limpieza automática

---

## 🎯 ESTRATEGIA DE IMPLEMENTACIÓN

### Enfoque: "Feature Branches + Commits Pequeños"

```
main (producción)
  ├─ feature/v0.10.0-integration (rama de integración)
      ├─ feature/post-procesamiento
      ├─ feature/flet-migration
      ├─ feature/utf8-fix
      ├─ feature/overlay-fix
      ├─ feature/updater-fix
      └─ feature/file-management
```

### Principios

1. **Commits pequeños y frecuentes** - Cada 10-15 minutos
2. **Commits con CONTEXT** - Trazabilidad completa
3. **Branching por feature** - Aislamiento de cambios
4. **Code review** - Pull requests obligatorias
5. **Testing continuo** - Tests en cada commit
6. **Documentación viva** - Actualizar 10 docs vivientes

---

## 📅 FASES DE IMPLEMENTACIÓN

### FASE 0: Preparación (Semana 0)

#### Objetivos
- [ ] Configurar entorno de desarrollo
- [ ] Configurar sistema de CI/CD
- [ ] Crear ramas de feature
- [ ] Configurar Engram (memoria persistente)
- [ ] Documentar estado actual

#### Tareas

```bash
# 1. Crear rama de integración
git checkout main
git pull origin main
git checkout -b feature/v0.10.0-integration

# 2. Crear ramas de feature
git checkout -b feature/post-procesamiento
git checkout -b feature/flet-migration
git checkout -b feature/utf8-fix
git checkout -b feature/overlay-fix
git checkout -b feature/updater-fix
git checkout -b feature/file-management

# 3. Configurar CI/CD (GitHub Actions)
# Crear .github/workflows/ci.yml
# Crear .github/workflows/cd.yml

# 4. Configurar Engram
engram save "audio2text/v0.10.0/setup" "Setup inicial v0.10.0"
```

#### Commit Inicial

```bash
git add .
git commit -m "feat(v0.10.0): Initialize v0.10.0 development

CONTEXT:
- ESTADO: Setup inicial v0.10.0
- ARCHIVOS: Creación de ramas de feature
- NEXT: Comenzar con feature/post-procesamiento

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"
```

---

### FASE 1: Post-Procesamiento (Semana 1-2)

#### Objetivos
- [ ] Implementar sistema de post-procesamiento
- [ ] Añadir vocabulario técnico pre-cargado
- [ ] Optimizar tiempo de transcripción (60-90s max)
- [ ] Testing y validación

#### Archivos a Crear

```
backend/
  └── post_processor.py          # Módulo de post-procesamiento
  └── vocabulary/                # Vocabulario técnico
      ├── ia_tech.json          # Vocabulario de IA
      ├── general.json          # Vocabulario general
      └── custom.json           # Vocabulario personalizado
```

#### Archivos a Modificar

```
backend/
  └── transcriber.py            # Integrar post-procesamiento
ui/
  └── app.py                    # Añadir config de post-procesamiento
lang/
  ├── es.json                   # Strings en español
  └── en.json                   # Strings en inglés
```

#### Implementación Detallada

** Paso 1: Crear módulo de post-procesamiento**

`backend/post_processor.py`:

```python
"""
Módulo de post-procesamiento de transcripciones.

Transforma habla espontánea en texto escrito natural.
"""

import re
from typing import List, Dict
from groq import Groq

class PostProcessor:
    """Post-procesa transcripciones de audio a texto."""

    def __init__(self, api_key: str, language: str = "es"):
        """
        Inicializar post-procesador.

        Args:
            api_key: API key de Groq
            language: Idioma de la transcripción
        """
        self.client = Groq(api_key=api_key)
        self.language = language
        self.vocabulary = self._load_vocabulary()

    def _load_vocabulary(self) -> Dict[str, List[str]]:
        """Cargar vocabulario técnico."""
        # TODO: Implementar carga de vocabulario
        return {
            "ia": ["prompt", "prompts", "ChatGPT", "OpenAI", "Gemini", "LLM", "Whisper"],
            "tech": ["API", "CLI", "GPU", "Python", "token", "tokens"]
        }

    def process(self, text: str) -> str:
        """
        Post-procesar transcripción.

        Args:
            text: Texto crudo de la transcripción

        Returns:
            Texto post-procesado
        """
        # TODO: Implementar post-procesamiento completo
        # 1. Corregir puntuación
        # 2. Corregir capitalización
        # 3. Eliminar muletillas
        # 4. Normalizar vocabulario técnico

        # Por ahora, retornar texto original
        return text

    def _correct_punctuation(self, text: str) -> str:
        """Corregir puntuación."""
        # TODO: Implementar
        pass

    def _correct_capitalization(self, text: str) -> str:
        """Corregir mayúsculas."""
        # TODO: Implementar
        pass

    def _remove_fillers(self, text: str) -> str:
        """Eliminar muletillas."""
        # TODO: Implementar
        pass

    def _normalize_vocabulary(self, text: str) -> str:
        """Normalizar vocabulario técnico."""
        # TODO: Implementar
        pass
```

**Paso 2: Integrar en transcriber**

`backend/transcriber.py`:

```python
# Añadir al inicio
from .post_processor import PostProcessor

# En __init__ de Transcriber:
self.post_processor = PostProcessor(
    api_key=self.api_key,
    language=self.language
)

# En método de transcripción, después de obtener resultado:
transcription = self.post_processor.process(transcription)
```

#### Commits Sugeridos

```bash
# Commit 1: Estructura base
git add backend/post_processor.py
git commit -m "feat(post-process): Create post-processor module structure

CONTEXT:
- ESTADO: Estructura base de post-procesador creada
- ARCHIVOS: backend/post_processor.py
- NEXT: Implementar métodos de post-procesamiento

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"

# Commit 2: Vocabulario técnico
git add backend/vocabulary/
git commit -m "feat(post-process): Add technical vocabulary dictionaries

CONTEXT:
- ESTADO: Vocabulario técnico añadido (IA, general, custom)
- ARCHIVOS: backend/vocabulary/*.json
- NEXT: Implementar corrección de puntuación

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"

# Commit 3: Integración con transcriber
git add backend/transcriber.py
git commit -m "feat(post-process): Integrate post-processor with transcriber

CONTEXT:
- ESTADO: Post-procesador integrado en flujo de transcripción
- ARCHIVOS: backend/transcriber.py
- NEXT: Testing y validación

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"

# Commit 4: UI y strings
git add ui/app.py lang/es.json lang/en.json
git commit -m "feat(post-process): Add UI for post-processing configuration

CONTEXT:
- ESTADO: UI de configuración de post-procesamiento añadida
- ARCHIVOS: ui/app.py, lang/*.json
- NEXT: Testing completo

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"
```

#### Testing

```python
# tests/test_post_processor.py
import pytest
from backend.post_processor import PostProcessor

def test_post_processor_init():
    """Test inicialización de post-procesador."""
    processor = PostProcessor(api_key="test")
    assert processor is not None

def test_process_basic():
    """Test procesamiento básico."""
    processor = PostProcessor(api_key="test")
    result = processor.process("hola mundo")
    assert isinstance(result, str)

def test_vocabulary_normalization():
    """Test normalización de vocabulario."""
    processor = PostProcessor(api_key="test")
    result = processor.process("uso mucho promp")
    assert "prompt" in result.lower() or "promp" in result.lower()
```

#### Criterios de Aceptación

- [ ] Post-procesador transforma habla a texto escrito
- [ ] Vocabulario técnico se normaliza correctamente
- [ ] Puntuación y capitalización corregidas
- [ ] Muletillas eliminadas (eh, mmm, bueno)
- [ ] Precisión de transcripción ≥ 95%
- [ ] Tiempo de transcripción < 10 segundos

---

### FASE 2: Migración a Flet (Semana 3-6)

#### Objetivos
- [ ] Migrar UI de CustomTkinter a Flet
- [ ] Mantener separación frontend/backend
- [ ] Testing completo de UI
- [ ] Actualizar scripts de build

#### Estrategia de Migración

**Opción A: Big Bang (Recomendada)**
- Reescribir toda la UI en Flet de una vez
- Ventaja: Código limpio sin híbridos
- Desventaja: Más trabajo inicial

**Opción B: Gradual**
- Migrar componente por componente
- Ventaja: Menos riesgo
- Desventaja: Código híbrido temporal

#### Estructura Nueva

```
ui_flet/                          # Nueva UI en Flet
  ├── main.py                     # App principal
  ├── screens/                    # Pantallas
  │   ├── home.py                # Pantalla principal
  │   ├── history.py             # Historial
  │   ├── config.py              # Configuración
  │   └── blocks.py              # Gestión de bloques
  ├── components/                 # Componentes reutilizables
  │   ├── recording_overlay.py   # Overlay de grabación
  │   ├── transcription_card.py  # Tarjeta de transcripción
  │   └── vocabulary_selector.py # Selector de vocabulario
  └── theme.py                    # Tema de la app
```

#### Implementación Detallada

**Paso 1: Setup de Flet**

`requirements.txt`:

```
# Añadir
flet>=0.21.0
```

**Paso 2: App principal**

`ui_flet/main.py`:

```python
"""
App principal de Audio2Text en Flet.
"""

import flet as ft
from backend.transcriber import Transcriber
from backend.config_manager import ConfigManager
from ui_flet.screens.home import HomeScreen
from ui_flet.screens.history import HistoryScreen
from ui_flet.screens.config import ConfigScreen


class Audio2TextApp:
    """Aplicación principal de Audio2Text."""

    def __init__(self):
        """Inicializar app."""
        self.config = ConfigManager()
        self.transcriber = Transcriber(
            api_key=self.config.get_api_key()
        )
        self.current_screen = None

    def main(self, page: ft.Page):
        """
        Punto de entrada de la app.

        Args:
            page: Página de Flet
        """
        self.page = page
        self.page.title = "Audio2Text"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window.width = 1200
        self.page.window.height = 800

        # Navegación
        self.page.navigation_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.HOME_ROUNDED,
                    selected_icon=ft.icons.HOME,
                    label="Transcripción"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.HISTORY_ROUNDED,
                    selected_icon=ft.icons.HISTORY,
                    label="Historial"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_ROUNDED,
                    selected_icon=ft.icons.SETTINGS,
                    label="Configuración"
                ),
            ],
            on_change=self._navigate,
        )

        # Contenedor de pantallas
        self.screen_container = ft.Container()

        # Pantalla inicial
        self._show_home_screen()

        # Layout
        self.page.add(
            ft.Row(
                [
                    self.page.navigation_rail,
                    ft.VerticalDivider(width=1),
                    self.screen_container,
                ],
                expand=True,
            )
        )

    def _navigate(self, e):
        """Manejar navegación."""
        if self.page.navigation_rail.selected_index == 0:
            self._show_home_screen()
        elif self.page.navigation_rail.selected_index == 1:
            self._show_history_screen()
        elif self.page.navigation_rail.selected_index == 2:
            self._show_config_screen()
        self.page.update()

    def _show_home_screen(self):
        """Mostrar pantalla principal."""
        self.screen_container.content = HomeScreen(
            transcriber=self.transcriber,
            config=self.config
        )
        self.page.update()

    def _show_history_screen(self):
        """Mostrar pantalla de historial."""
        self.screen_container.content = HistoryScreen(
            config=self.config
        )
        self.page.update()

    def _show_config_screen(self):
        """Mostrar pantalla de configuración."""
        self.screen_container.content = ConfigScreen(
            config=self.config
        )
        self.page.update()


def main():
    """Punto de entrada."""
    app = Audio2TextApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()
```

#### Commits Sugeridos

```bash
# Commit 1: Estructura Flet
git add ui_flet/
git commit -m "feat(flet): Create Flet UI structure

CONTEXT:
- ESTADO: Estructura base de Flet creada
- ARCHIVOS: ui_flet/main.py, screens/, components/
- NEXT: Implementar pantallas

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"

# Commit 2: Pantalla principal
git add ui_flet/screens/home.py
git commit -m "feat(flet): Implement home screen

CONTEXT:
- ESTADO: Pantalla principal implementada
- ARCHIVOS: ui_flet/screens/home.py
- NEXT: Implementar historial y config

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"

# Commit 3: Integración backend
git add ui_flet/main.py
git commit -m "feat(flet): Integrate with backend

CONTEXT:
- ESTADO: UI de Flet integrada con backend
- ARCHIVOS: ui_flet/main.py
- NEXT: Testing completo

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"
```

#### Criterios de Aceptación

- [ ] UI funciona correctamente en Flet
- [ ] Todas las features de CustomTkinter migradas
- [ ] Backend se mantiene sin cambios
- [ ] Performance igual o mejor
- [ ] Testing manual completo

---

### FASE 3: Corrección UTF-8 (Semana 7)

#### Objetivos
- [ ] Solucionar problemas con tildes y ñ
- [ ] Validar encoding en todo el flujo
- [ ] Testing con español rioplatense

#### Estrategia

1. **Investigar causa raíz**
   - ¿Es problema de Groq API?
   - ¿Es problema de Whisper model?
   - ¿Es problema de encoding Python?

2. **Implementar solución**
   - Opción A: Post-procesamiento con validación UTF-8
   - Opción B: Cambiar a Gemini API
   - Opción C: Usar OpenAI directamente

#### Implementación

`backend/utf8_validator.py`:

```python
"""
Validador y corrector de encoding UTF-8.
"""

import chardet


class UTF8Validator:
    """Valida y corrige encoding UTF-8."""

    @staticmethod
    def validate(text: str) -> bool:
        """
        Validar que el texto sea UTF-8 válido.

        Args:
            text: Texto a validar

        Returns:
            True si es UTF-8 válido
        """
        try:
            text.encode('utf-8')
            return True
        except UnicodeEncodeError:
            return False

    @staticmethod
    def correct(text: str) -> str:
        """
        Corregir encoding de texto.

        Args:
            text: Texto a corregir

        Returns:
            Texto corregido
        """
        if not UTF8Validator.validate(text):
            # Intentar detectar encoding
            detected = chardet.detect(text.encode('ascii', errors='ignore'))
            if detected['encoding']:
                try:
                    text = text.encode(detected['encoding']).decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    # Si falla, reemplazar caracteres inválidos
                    text = text.encode('ascii', errors='replace').decode('utf-8')
        return text

    @staticmethod
    def normalize_spanish(text: str) -> str:
        """
        Normalizar texto español (tildes, ñ).

        Args:
            text: Texto a normalizar

        Returns:
            Texto normalizado
        """
        # TODO: Implementar normalización específica
        return text
```

#### Criterios de Aceptación

- [ ] Tildes (á, é, í, ó, ú) funcionan correctamente
- [ ] ñ funciona correctamente
- [ ] Signos españoles (¿, ¡) funcionan
- [ ] No hay bloqueos por encoding
- [ ] Tests con 100+ palabras españoles

---

### FASE 4: Overlay Fix (Semana 7)

#### Objetivos
- [ ] Reactivar overlay de grabación
- [ ] Debuggear problema original
- [ ] Testing de overlay

#### Implementación

`ui/app.py` (o `ui_flet/components/recording_overlay.py`):

```python
# Descomentar y arreglar
# self.recording_overlay = RecordingOverlay(self)
```

#### Criterios de Aceptación

- [ ] Overlay aparece al grabar
- [ ] Overlay muestra timer correctamente
- [ ] Overlay es draggable
- [ ] Overlay se cierra al terminar

---

### FASE 5: Updater Fix (Semana 8)

#### Objetivos
- [ ] Arreglar botón de actualizar
- [ ] Debuggear updater.py
- [ ] Debuggear update_tab.py
- [ ] Testing de actualización

#### Implementación

Revisar `backend/updater.py` y `ui/update_tab.py` para:

1. Verificar conexión con GitHub
2. Verificar parseo de versiones
3. Verificar descarga de actualización
4. Verificar instalación silenciosa

#### Criterios de Aceptación

- [ ] Botón de actualizar funciona
- [ ] Actualización se descarga correctamente
- [ ] Actualización se instala correctamente
- [ ] App se reinicia después de actualizar

---

### FASE 6: File Management (Semana 8-9)

#### Objetivos
- [ ] Implementar límite de archivos
- [ ] Implementar limpieza automática
- [ ] Optimizar carga de historial
- [ ] Testing con muchos archivos

#### Implementación

`backend/file_manager.py`:

```python
def clean_old_files(max_files: int = 100, max_days: int = 30):
    """
    Limpiar archivos viejos.

    Args:
        max_files: Máximo número de archivos a mantener
        max_days: Máximo número de días a mantener
    """
    # TODO: Implementar limpieza
    pass

def cleanup_size(max_size_gb: int = 10):
    """
    Limpiar si supera tamaño máximo.

    Args:
        max_size_gb: Tamaño máximo en GB
    """
    # TODO: Implementar limpieza por tamaño
    pass
```

#### Criterios de Aceptación

- [ ] Límite de archivos configurable
- [ ] Limpieza automática funciona
- [ ] Historial carga rápido (lazy loading)
- [ ] App no se cuelga con muchos archivos

---

### FASE 7: Integración y Testing (Semana 10-11)

#### Objetivos
- [ ] Merge de todas las features
- [ ] Testing completo de integración
- [ ] Corrección de bugs
- [ ] Preparación de release

#### Testing Checklist

- [ ] Unit tests (80%+ cobertura)
- [ ] Integration tests
- [ ] Manual testing de UI
- [ ] Performance testing
- [ ] Security testing
- [ ] User acceptance testing

---

### FASE 8: Release v0.10.0 (Semana 12)

#### Objetivos
- [ ] Tag de versión
- [ ] Release notes
- [ ] Build de ejecutables
- [ ] Despliegue

#### Release Checklist

```bash
# 1. Crear tag
git tag -a v0.10.0 -m "Release v0.10.0: Post-procesamiento, Flet, UTF-8 fix"
git push origin v0.10.0

# 2. Crear release en GitHub
# - Subir executables
# - Añadir release notes
# - Añadir changelog

# 3. Actualizar documentación
# - CLAUDE.md
# - README.md
# - CHANGELOG.md
# - 10 docs vivientes

# 4. Anunciar release
# - GitHub discussions
# - Comunidad
# - Usuarios
```

---

## 📊 ESTIMACIÓN DE TIEMPO

| Fase | Duración | Effort | Dependencias |
|------|----------|--------|--------------|
| FASE 0: Preparación | 1 semana | 8h | - |
| FASE 1: Post-procesamiento | 2 semanas | 80h | FASE 0 |
| FASE 2: Migración a Flet | 4 semanas | 160h | FASE 0 |
| FASE 3: UTF-8 Fix | 1 semana | 40h | FASE 1 |
| FASE 4: Overlay Fix | 1 semana | 8h | FASE 2 |
| FASE 5: Updater Fix | 1 semana | 16h | FASE 2 |
| FASE 6: File Management | 2 semanas | 40h | FASE 2 |
| FASE 7: Integración | 2 semanas | 80h | Todas |
| FASE 8: Release | 1 semana | 16h | Todas |
| **TOTAL** | **15 semanas** | **448h** | - |

**Estimación:** Q2 2026 (abril - julio)

---

## 🎯 RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Flet no esté listo | Media | Alto | CustomTkinter como fallback |
| UTF-8 no se resuelva | Alta | Medio | OpenAI API como backup |
| Migración toma más tiempo | Alta | Medio | Reducir scope |
| Bugs en integración | Media | Medio | Testing extensivo |
| Cambios en requirements | Baja | Bajo | Version locking |

---

## 🎯 ÉXITO DEL PROYECTO

### Criterios de Éxito

**Técnicos:**
- ✅ Post-procesamiento funciona
- ✅ UI en Flet funciona
- ✅ UTF-8 resuelto
- ✅ Overlay funciona
- ✅ Actualizaciones funcionan
- ✅ Gestión de archivos funciona

**De Producto:**
- ✅ Precisión ≥ 95%
- ✅ Performance < 10s
- ✅ Estabilidad < 1% crashes

**De Proceso:**
- ✅ Commits con CONTEXT
- ✅ Branching por feature
- ✅ Testing completo
- ✅ Documentación actualizada

---

## 🎯 PRÓXIMOS PASOS

1. **Aprobación del plan** por parte del equipo
2. **Configuración de entorno** (FASE 0)
3. **Comenzar FASE 1** (Post-procesamiento)
4. **Revisión semanal** de progreso
5. **Ajustes según** feedback

---

**Fin del Plan de Implementación.**

¿Aprobamos este plan y comenzamos con FASE 0?
