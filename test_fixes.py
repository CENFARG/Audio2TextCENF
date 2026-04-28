#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script para verificar bugs fixes v0.14.0"""

import sys
import os

print("="*60)
print("VERIFICANDO BUGS FIXES v0.14.0")
print("="*60)

# Test 1: Verificar versión en config.json
print("\n1. Verificando version en config.json...")
try:
    import json
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        version = config.get("app_version", "NOT FOUND")
        print(f"   [OK] Version: {version}")
        assert version == "0.14.0", f"Expected 0.14.0, got {version}"
        print("   [PASS] Version correcta en config.json")
except Exception as e:
    print(f"   [FAIL] {e}")
    sys.exit(1)

# Test 2: Verificar bloques desactivados
print("\n2. Verificando bloques desactivados...")
try:
    use_post = config.get("use_post_processing", True)
    use_llm = config.get("use_llm_post_processing", True)
    task_extractor = config.get("blocks", {}).get("task_extractor_enabled", True)

    assert use_post == False, "use_post_processing should be False"
    assert use_llm == False, "use_llm_post_processing should be False"
    assert task_extractor == False, "task_extractor_enabled should be False"

    print(f"   [OK] use_post_processing: {use_post}")
    print(f"   [OK] use_llm_post_processing: {use_llm}")
    print(f"   [OK] task_extractor_enabled: {task_extractor}")
    print("   [PASS] Bloques desactivados")
except Exception as e:
    print(f"   [FAIL] {e}")
    sys.exit(1)

# Test 3: Verificar que hotkey selector NO tenga los fixes problemáticos
print("\n3. Verificando hotkey selector (sin -topmost, focus_force)...")
try:
    with open("ui/hotkey_selector.py", "r", encoding="utf-8") as f:
        content = f.read()

        # Verificar que NO tenga los fixes problemáticos
        has_topmost = "attributes('-topmost', True)" in content
        has_focus_force = "focus_force()" in content
        has_lift = "self.lift()" in content

        print(f"   ¿Tiene -topmost? {has_topmost}")
        print(f"   ¿Tiene focus_force? {has_focus_force}")
        print(f"   ¿Tiene lift? {has_lift}")

        # Debería tener transient() y grab_set() pero NO los otros
        has_transient = "self.transient(parent)" in content
        has_grab_set = "self.grab_set()" in content

        assert has_transient, "Debe tener transient()"
        assert has_grab_set, "Debe tener grab_set()"
        assert not has_topmost, "NO debe tener -topmost"
        assert not has_focus_force, "NO debe tener focus_force()"
        assert not has_lift, "NO debe tener lift()"

        print("   [PASS] Hotkey selector limpio (sin fixes problemáticos)")
except Exception as e:
    print(f"   [FAIL] {e}")
    sys.exit(1)

# Test 4: Verificar que create_info_tab usa fallback
print("\n4. Verificando que info tab usa fallback CustomTkinter...")
try:
    with open("ui/app.py", "r", encoding="utf-8") as f:
        content = f.read()

        # Verificar que create_info_tab llama directamente a _create_info_tab_fallback
        # y NO usa tkhtmlview
        uses_fallback_directly = "self._create_info_tab_fallback(tab)" in content
        has_try_tkhtmlview = "from tkhtmlview import HTMLScrolledText" in content

        print(f"   ¿Usa fallback directamente? {uses_fallback_directly}")
        print(f"   ¿Tiene import tkhtmlview? {has_try_tkhtmlview}")

        # IMPORTANTE: Después del fix, NO debería importar ni usar tkhtmlview
        assert uses_fallback_directly, "Debe usar fallback directamente"
        assert not has_try_tkhtmlview, "NO debe importar tkhtmlview en create_info_tab"

        print("   [PASS] Info tab usa CustomTkinter nativo (no tkhtmlview)")
except Exception as e:
    print(f"   [FAIL] {e}")
    sys.exit(1)

print("\n" + "="*60)
print("[SUCCESS] TODOS LOS TESTS PASARON - v0.14.0 CORRECTA")
print("="*60)
print("\nResumen:")
print("  1. [OK] Version 0.14.0 en config.json")
print("  2. [OK] Bloques desactivados")
print("  3. [OK] Hotkey selector limpio")
print("  4. [OK] Info tab usa CustomTkinter nativo")
print("\nEl programa deberia:")
print("  - Mostrar 'Audio2Text CENF v0.14.0' en el titulo")
print("  - Abrir hotkey selector con contenido visible")
print("  - Mostrar pestaña Informacion con texto bonito (no CSS crudo)")
print("  - NO ejecutar bloques POST-processing")
