import sys
import os

# Configurar para mostrar traceback completo
os.environ['PYTHONFAULTHANDLER'] = '1'

if __name__ == '__main__':
    try:
        import main
    except Exception as e:
        import traceback
        print("\n" + "="*100)
        print("ERROR COMPLETO:")
        print("="*100)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Imprimir cada frame del traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in tb_lines:
            print(line, end='')
        
        print("\n" + "="*100)
        print("ÚLTIMO FRAME (donde ocurrió el error):")
        print("="*100)
        
        # Obtener el último frame
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        
        frame = tb.tb_frame
        print(f"Archivo: {frame.f_code.co_filename}")
        print(f"Línea: {tb.tb_lineno}")
        print(f"Función: {frame.f_code.co_name}")
        print("="*100)
        
        sys.exit(1)
