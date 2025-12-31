import sys
import traceback

try:
    # Ejecutar main.py
    with open('main.py', 'r', encoding='utf-8') as f:
        code = f.read()
    exec(compile(code, 'main.py', 'exec'))
except Exception as e:
    print("\n" + "="*80)
    print("TRACEBACK COMPLETO:")
    print("="*80)
    traceback.print_exc()
    print("="*80)
    sys.exit(1)
