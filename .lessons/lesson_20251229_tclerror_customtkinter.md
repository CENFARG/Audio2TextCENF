---
Project: Audio2Text
Date: 2025-12-29
Context_Tags: #Python #CustomTkinter #Tkinter #TclError #Windows #MonkeyPatch
User_Working_Style_Update: "Priorizar la creación de tutoriales interactivos de onboarding para mejorar la UX. Mantener ramas de desarrollo limpias y usar 'lessons learned' para evitar regresiones."
---

# Lección Aprendida: TclError con CustomTkinter y Floats en Windows

## Resumen Ejecutivo
Se resolvió un error crítico que impedía el inicio de la aplicación (`_tkinter.TclError: bad screen distance "300.0"`). El problema radicaba en la librería `CustomTkinter` pasando valores flotantes (ej. `300.0`) a `tkinter.Canvas`, lo cual es rechazado por el intérprete Tcl en el entorno actual de Windows/Python. La solución fue implementar un "monkeypatch" global en `tkinter.Canvas` para forzar la conversión de dimensiones a enteros.

## Directivas Algorítmicas (The Core Knowledge)

### Manejo de Geometría en Tkinter/CustomTkinter

*   **IF:** Estás desarrollando una interfaz gráfica con `CustomTkinter` (especialmente versiones ~5.2.2) sobre Python en Windows.
*   **WHEN:** `CustomTkinter` calcula dimensiones internas (width/height) para widgets compuestos (`CTkTabview`, `CTkScrollableFrame`) y las pasa a `tk.Canvas`.
*   **THEN:** **DEBES asegurar que los valores sean `int`**. Si la librería no lo hace, **DEBES aplicar un monkeypatch** en el punto de entrada (`main.py`) que intercepte `tkinter.Canvas.configure` e `__init__` para castear `float` a `int`.
*   **Reasoning:** Tcl puede ser estricto con los tipos de datos para dimensiones de pantalla ("screen distance"), rechazando cadenas que representan flotantes (ej: "300.0") donde espera enteros o unidades específicas.

### Depuración de Errores de Inicio en UI

*   **IF:** La aplicación crashea al inicio con un error de UI genérico o difícil de trazar.
*   **WHEN:** El traceback normal está truncado o es insuficiente.
*   **THEN:** **implementa un manejo de excepciones global** en el bloque `if __name__ == "__main__":` que capture el traceback completo y lo vuelque a un archivo de texto (`crash_log.txt`), o usa un script de debug dedicado con `debugpy` configurado para "Step Into" librerías externas (`justMyCode: false` en `launch.json`).

## Categorías Legacy

### Lecciones de Programación
- **Tipado Fuerte en Tcl:** Aunque Python es dinámico, el puente con Tcl/Tk puede ser estricto. Siempre pasar enteros para coordenadas de píxeles.
- **Monkeypatching:** Es una herramienta poderosa pero peligrosa. Debe hacerse lo antes posible en la ejecución (antes de instanciar la App) y debe mantener la firma original de los métodos.

### Lecciones Estratégicas
- **Aislamiento de Errores:** Comentar widgets sospechosos (`RecordingOverlay`) ayudó a descartar causas, pero el análisis del traceback real fue definitivo.
- **No confiar en `pip install --upgrade`:** A veces el bug está en la última versión estable de la librería y requiere un fix manual (patch) en lugar de un update.

## La Perspectiva "Anti-Gravedad"
**Asumir la responsabilidad del ecosistema:** Cuando una librería de terceros falla por incompatibilidades de entorno (como este caso de floats en Tcl), no debemos esperar un fix del mantenedor. Tenemos la capacidad de "reparar" el comportamiento en tiempo de ejecución mediante inyección de código (monkeypatching) para desbloquear el proyecto inmediatamente. La "gravedad" nos diría "espera el update o cambia de librería"; la "antigravedad" dice "reescribe la regla en memoria y sigue volando".

## Checklist Futuro
- [ ] Verificar si futuras actualizaciones de CustomTkinter resuelven este problema nativamente.
- [ ] Al agregar nuevos widgets complejos, probar inmediatamente en el entorno de producción (Windows build).
- [ ] Mantener el `launch.json` configurado para depuración profunda de librerías.
