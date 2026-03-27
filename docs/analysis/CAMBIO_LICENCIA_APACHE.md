**[Español](CAMBIO_LICENCIA_APACHE.md) | [English](CAMBIO_LICENCIA_APACHE_EN.md)**

# 📝 Resumen de Cambios - Licencia Apache 2.0

## 🔄 Cambio de Licencia

**De:** MIT License  
**A:** Apache License 2.0  
**Fecha:** 2025-12-23  
**Razón:** Mejor protección para distribución B2B

---

## ✅ Archivos Actualizados

### 1. Licencia Principal
- ✅ `LICENSE` - Reemplazado con Apache 2.0 completo
- ✅ `NOTICE` - Creado (requerido por Apache 2.0)

### 2. Documentación
- ✅ `README.md` - Badge y sección de licencia actualizados
- ✅ `CONTRIBUTING.md` - Referencia a Apache 2.0 y derechos de autor

### 3. Configuración de Proyecto
- ✅ `setup.py` - Classifier cambiado a Apache Software License
- ✅ `pyproject.toml` - License text y classifier actualizados

### 4. Nuevas Guías
- ✅ `docs/GUIA_API_KEY_GROQ.md` - Guía completa para obtener API key
- ✅ `docs/GUIA_INSTALADOR_MSI.md` - Guía para crear instalador MSI
- ✅ `installer.wxs` - Configuración WiX para MSI
- ✅ `VERIFICACION_INSTALACION.md` - Checklist de instalación
- ✅ `ANALISIS_LICENCIAS.md` - Análisis de opciones de licencia

---

## 🎯 Beneficios de Apache 2.0

### Para CENF:
1. ✅ **Protección de Patentes:** Licencia explícita de patentes
2. ✅ **Protección de Marca:** "Audio2Text" y "CENF" protegidos
3. ✅ **Profesionalismo:** Estándar enterprise
4. ✅ **Defensa Legal:** Cláusulas de terminación por litigio

### Para Clientes:
1. ✅ **Uso Comercial:** Sin restricciones
2. ✅ **Modificaciones:** Permitidas con atribución
3. ✅ **Distribución:** Permitida
4. ✅ **Claridad:** Términos explícitos y profesionales

---

## 📋 Archivo NOTICE

Creado `NOTICE` con:
- Copyright de CENF
- Atribuciones de librerías de terceros
- Aviso de marca registrada
- Contacto legal

**Importante:** Este archivo DEBE distribuirse con el software.

---

## 🔍 Verificación

### Archivos que DEBEN incluirse en distribución:

1. ✅ `LICENSE` (Apache 2.0)
2. ✅ `NOTICE` (Atribuciones)
3. ✅ `README.md` (Con referencia a licencia)
4. ✅ Código fuente o ejecutable

### En Ejecutables Compilados:

El instalador MSI y NSIS deben incluir:
- LICENSE en la carpeta de instalación
- NOTICE en la carpeta de instalación
- Referencia a la licencia en el instalador

---

## 🚀 Próximos Pasos

### Inmediatos:
1. ✅ Commit de cambios de licencia
2. ✅ Push a GitHub
3. ⏳ Actualizar release v0.9.2 (si ya fue creada)

### Recomendados:
1. ⬜ Agregar headers de Apache 2.0 en archivos .py (opcional)
2. ⬜ Actualizar documentación de terceros si es necesario
3. ⬜ Notificar a usuarios existentes del cambio de licencia

---

## 📄 Header Opcional para Archivos Python

Si quieres agregar headers a los archivos .py:

```python
# Copyright 2024-2025 CENF - Centro de Excelencia en Negocios del Futuro
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

**Nota:** Esto es opcional pero recomendado para proyectos grandes.

---

## ⚖️ Compatibilidad

Apache 2.0 es compatible con:
- ✅ MIT
- ✅ BSD
- ✅ GPL v3 (con cuidado)
- ✅ Uso comercial
- ✅ Modificación y distribución

---

## 📞 Contacto Legal

Para consultas sobre licencia:
- **Email:** legal@cenfarg.com.ar
- **Sitio:** https://cenfarg.com.ar

---

**Cambio completado exitosamente** ✅
