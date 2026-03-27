# Guía de Contribución

¡Gracias por tu interés en contribuir a Audio2Text! 🎉

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Puedo Contribuir?](#cómo-puedo-contribuir)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Mejoras](#sugerir-mejoras)

## Código de Conducta

Este proyecto adhiere al [Código de Conducta](CODE_OF_CONDUCT.md). Al participar, se espera que mantengas este código.

## ¿Cómo Puedo Contribuir?

### Reportar Bugs

Los bugs se rastrean como [GitHub Issues](https://github.com/CENFARG/Audio2Text/issues). Antes de crear un issue:

1. **Verifica** que el bug no haya sido reportado previamente
2. **Usa** la plantilla de bug report
3. **Incluye** toda la información relevante:
   - Versión de Audio2Text
   - Sistema operativo y versión
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Capturas de pantalla si aplica
   - Logs relevantes

### Sugerir Mejoras

Las sugerencias de mejoras también se rastrean como [GitHub Issues](https://github.com/CENFARG/Audio2Text/issues):

1. **Usa** la plantilla de feature request
2. **Describe** el problema que la mejora resolvería
3. **Explica** la solución propuesta
4. **Considera** alternativas que hayas evaluado

### Tu Primera Contribución de Código

¿No estás seguro por dónde empezar? Busca issues etiquetados como:

- `good first issue` - Issues apropiados para principiantes
- `help wanted` - Issues donde necesitamos ayuda

## Proceso de Desarrollo

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/TU-USUARIO/Audio2Text.git
cd Audio2Text

# Agrega el repositorio original como upstream
git remote add upstream https://github.com/CENFARG/Audio2Text.git
```

### 2. Configura el Entorno

```bash
# Crea un entorno virtual
python -m venv .venv

# Activa el entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instala dependencias
pip install -r requirements.txt

# Instala dependencias de desarrollo (opcional)
pip install pytest pytest-cov black flake8 mypy
```

### 3. Crea una Rama

```bash
# Actualiza tu main
git checkout main
git pull upstream main

# Crea una rama para tu feature/fix
git checkout -b feature/nombre-descriptivo
# o
git checkout -b fix/nombre-del-bug
```

### 4. Desarrolla

- Escribe código limpio y documentado
- Sigue los [Estándares de Código](#estándares-de-código)
- Agrega tests si es posible
- Actualiza la documentación si es necesario

### 5. Prueba

```bash
# Ejecuta la aplicación
python main.py

# Ejecuta tests (si existen)
pytest

# Verifica el estilo de código
black --check .
flake8 .
```

### 6. Commit

Usa mensajes de commit descriptivos siguiendo [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: agrega soporte para nuevo idioma"
# o
git commit -m "fix: corrige error en transcripción de audio largo"
# o
git commit -m "docs: actualiza README con nuevas instrucciones"
```

Tipos de commit:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (no afectan el código)
- `refactor`: Refactorización de código
- `test`: Agregar o modificar tests
- `chore`: Cambios en build, dependencias, etc.

## Estándares de Código

### Python

- **Estilo:** Seguir [PEP 8](https://pep8.org/)
- **Formateo:** Usar `black` con line-length=100
- **Imports:** Organizar con `isort`
- **Type Hints:** Usar cuando sea posible (Python 3.8+)
- **Docstrings:** Usar formato Google/NumPy

Ejemplo:

```python
def transcribe_audio(audio_path: str, language: str = "es") -> dict:
    """
    Transcribe un archivo de audio usando Groq API.
    
    Args:
        audio_path: Ruta al archivo de audio
        language: Código de idioma (es/en)
        
    Returns:
        dict: Resultado de la transcripción con texto y metadatos
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        APIError: Si hay error en la API
    """
    # Implementación
    pass
```

### Estructura de Archivos

```
Audio2Text/
├── backend/           # Lógica de negocio
│   ├── __init__.py
│   ├── transcriber.py
│   └── ...
├── ui/                # Interfaz gráfica
│   ├── __init__.py
│   ├── app.py
│   └── ...
├── tests/             # Tests unitarios
│   ├── test_backend.py
│   └── test_ui.py
├── docs/              # Documentación
└── scripts/           # Scripts de build
```

### Nombres

- **Archivos:** `snake_case.py`
- **Clases:** `PascalCase`
- **Funciones/Variables:** `snake_case`
- **Constantes:** `UPPER_SNAKE_CASE`

## Proceso de Pull Request

1. **Actualiza tu rama** con los últimos cambios de main:
   ```bash
   git checkout main
   git pull upstream main
   git checkout tu-rama
   git rebase main
   ```

2. **Push a tu fork:**
   ```bash
   git push origin tu-rama
   ```

3. **Crea el Pull Request** en GitHub:
   - Usa un título descriptivo
   - Completa la plantilla de PR
   - Referencia issues relacionados (#123)
   - Agrega capturas si hay cambios visuales

4. **Espera la revisión:**
   - Responde a comentarios
   - Realiza cambios solicitados
   - Mantén la conversación profesional

5. **Merge:**
   - Un maintainer hará el merge cuando esté aprobado
   - Tu rama será eliminada automáticamente

## Reportar Vulnerabilidades de Seguridad

**NO** crees un issue público para vulnerabilidades de seguridad.

En su lugar, envía un email a: **cenf.arg@gmail.com**

Ver [SECURITY.md](SECURITY.md) para más detalles.

## Licencia

Al contribuir, aceptas que tus contribuciones serán licenciadas bajo la [Licencia Apache 2.0](LICENSE).

### Derechos de Autor

Al enviar una contribución, certificas que:

1. Tienes el derecho de someter el trabajo bajo la licencia Apache 2.0
2. Entiendes que tus contribuciones son públicas
3. Aceptas que CENF puede usar tu contribución bajo Apache 2.0
4. No estás violando ningún acuerdo de confidencialidad o propiedad intelectual

## Preguntas

¿Tienes preguntas? Puedes:

- Abrir un [GitHub Discussion](https://github.com/CENFARG/Audio2Text/discussions)
- Contactarnos en: cenf.arg@gmail.com

---

¡Gracias por contribuir a Audio2Text! 🎉
