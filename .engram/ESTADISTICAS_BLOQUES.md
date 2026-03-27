# 📊 Estadísticas de Bloques - Guía Completa

> **Versión:** v0.11.0
> **Fecha:** 2026-03-20
> **Para:** Usuario de Audio2Text

---

## 🎯 ¿QUÉ SON LAS ESTADÍSTICAS DE BLOQUES?

Las estadísticas de bloques muestran **información sobre el procesamiento** que realizan los bloques POST-transcripción (TaskExtractor, Summary, Keywords).

---

## 📋 ¿PARA QUÉ SIRVEN?

### 1. **VERIFICAR FUNCIONAMIENTO**
Permite confirmar que los bloques están funcionando correctamente:
- ✅ ¿Se ejecutaron los bloques?
- ✅ ¿Cuántas veces se usaron?
- ✅ ¿Falló algún bloque?

### 2. **OPTIMIZAR PROCESAMIENTO**
Ayuda a identificar cuellos de botella:
- ⚠️ ¿Un bloque se ejecuta muy lento?
- ⚠️ ¿Un bloque falla mucho?
- ⚠️ ¿Necesito activar/desactivar algún bloque?

### 3. **CONTROL DE CALIDAD**
Métricas de calidad del procesamiento:
- 📊 Total de transcripciones procesadas
- 📊 Tasa de éxito/fracaso
- 📊 Tiempo promedio de procesamiento

---

## 🎨 CÓMO VER LAS ESTADÍSTICAS

### Método 1: Desde la UI

1. **Abrir Audio2Text**
2. **Ir a "Configuración"**
3. **Click en "Ver Estadísticas de Bloques"**
4. **Se abre una ventana con:**

```
╔════════════════════════════════════════════════════════╗
║         Estadísticas de Bloques                          ║
║                                                           ║
║  TaskExtractor                                          ║
║    ✅ Activo                                              ║
║    Procesados: 0 | Fallos: 0                            ║
║                                                           ║
║  Summary                                                 ║
║    ✅ Activo                                              ║
║    Procesados: 0 | Fallos: 0                            ║
║                                                           ║
║  KeywordExtractor                                        ║
║    ✅ Activo                                              ║
║    Procesados: 0 | Fallos: 0                            ║
║                                                           ║
║                        [Cerrar]                            ║
╚════════════════════════════════════════════════════════╝
```

### Método 2: Desde el Código

```python
# En código Python:
stats = transcriber.get_block_stats()

print(json.dumps(stats, indent=2))
# {
#   "task_extractor": {
#     "enabled": true,
#     "block_type": "post",
#     "stats": {
#       "processed": 150,
#       "failed": 2,
#       "avg_processing_time": 0.15
#     }
#   },
#   ...
# }
```

---

## 📊 QUÉ SIGNIFICAN LAS MÉTRICAS

### TaskExtractorBlock (Extractor de Tareas)
- **Procesados:** Cantidad de transcripciones analizadas
- **Fallos:** Cantidad de veces que falló al extraer tareas
- **Promedio de procesamiento:** Tiempo promedio (segundos)

### SummaryBlock (Generador de Resúmenes)
- **Procesados:** Cantidad de resúmenes generados
- **Fallos:** Cantidad de errores al generar resúmenes
- **Promedio de procesamiento:** Tiempo promedio

### KeywordExtractorBlock (Extractor de Palabras Clave)
- **Procesados:** Cantidad de extracciones de keywords
- **Fallos:** Cantidad de errores al extraer
- **Promedio de procesamiento:** Tiempo promedio

---

## 🎯 USO PRÁCTICO

### Escenario 1: Verificar que los bloques funcionan

```
Usuario: "¿Cómo sé si los bloques están funcionando?"
Respuesta: "Ve a Estadísticas de Bloques, si 'Procesados' > 0 después de transcribir, están funcionando."
```

### Escenario 2: Optimizar rendimiento

```
Usuario: "Las transcripciones están lentas."
Respuesta: "Ve a Estadísticas de Bloques, si 'Promedio de procesamiento' es alto (> 1s), desactiva algún bloque."
```

### Escenario 3: Debugging

```
Usuario: "El extractor de tareas no funciona."
Respuesta: "Ve a Estadísticas de Bloques, si 'Fallos' > 0, hay un problema que investigar."
```

---

## ⚙️ CONFIGURACIÓN DE BLOQUES

### Activar/Desactivar Bloques

**En Configuración:**
1. Ir a "Configuración"
2. Buscar "Bloques de Procesamiento (v0.11.0)"
3. Activar/desactivar switches:
   - ☑️ Extractor de Tareas
   - ☑️ Generar Resúmenes
   - ☑️ Extractor de Palabras Clave

**Efecto:** Los bloques se activan/desactivan inmediatamente.

### Resetear Estadísticas

**Opción 1: Reiniciar aplicación**
```
La aplicación se reinicia y las estadísticas vuelven a 0.
```

**Opción 2: No disponible actualmente**
```
Puedes agregar un botón "Resetear Estadísticas" en versiones futuras.
```

---

## 🔧 EN EL CÓDIGO

### Acceder a estadísticas

```python
# Desde fuera de la App
from backend.transcriber import Transcriber

# Crear instancia (la App lo hace automáticamente)
transcriber = Transcriber(...)

# Obtener estadísticas
stats = transcriber.get_block_stats()

# Ver estadísticas de un bloque específico
task_stats = stats['task_extractor']
print(f"Procesados: {task_stats['stats']['processed']}")
print(f"Fallos: {task_stats['stats']['failed']}")
print(f"Tiempo promedio: {task_stats['stats']['avg_processing_time']}s")
```

### Obtener resultados de bloques

```python
# Obtener resultados de la última transcripción
results = transcriber.get_block_results()

for result in results:
    if result.success:
        print(f"Bloque: {result.data}")
        print(f"Metadatos: {result.metadata}")
```

---

## 📈 EJEMPLO DE USO

### Ejemplo 1: Verificar después de transcribir

1. **Presionar F9** y grabar algo
2. **Soltar F9** para transcribir
3. **Ir a Configuración → Ver Estadísticas de Bloques**
4. **Verificar que "Procesados" incrementó**

### Ejemplo 2: Analizar rendimiento

```
ANTES (sin bloques):
- Transcripción: 2 segundos
- Total: 2 segundos

DESPUÉS (con 3 bloques):
- Transcripción: 2 segundos
- TaskExtractor: 0.1 segundos
- Summary: 0.15 segundos
- Keywords: 0.05 segundos
- Total: 2.3 segundos

Conclusión: Los bloques agregan ~300ms pero mejoran mucho la salida.
```

---

## 🎯 CONCLUSIÓN

**Las estadísticas de bloques sirven para:**
- ✅ Verificar funcionamiento
- ✅ Optimizar rendimiento
- ✅ Debugging de problemas
- ✅ Control de calidad

**Es una herramienta de monitoreo esencial** para entender qué está pasando con el procesamiento de transcripciones.

---

## 💡 TIPS

1. **Revisar periódicamente:** Después de transcribir varias veces, mira las estadísticas
2. **Activar solo lo necesario:** Si no usas las tareas, desactiva TaskExtractor
3. **Monitorear fallos:** Si muchos fallos, puede haber un problema con el bloque
4. **Comparar rendimiento:** Si está lento, prueba desactivar bloques uno por uno

---

**Versión:** 0.11.0
**Fecha:** 2026-03-20
**Autor:** Audio2Text Development Team
