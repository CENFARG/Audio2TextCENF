"""visual_qa_capture.py — Visual QA capture harness (roadmap A5, level 1).

Captura la pantalla completa a pedido del operador para auditoría estética
del programa sin revisión manual compleja. El operador cambia la app al
estado deseado (pestaña, diálogo, cola con archivos, etc.) y presiona
Enter en este script; cada captura se guarda numerada en qa_screenshots/.

Uso:
    python scripts/visual_qa_capture.py [carpeta_destino]

    Enter       -> capturar pantalla completa
    e + Enter   -> capturar con etiqueta (ej: supervisor-bloques)
    q + Enter   -> terminar

Las capturas se guardan como PNG numeradas: 01_<etiqueta>.png, ...
El agente revisa la carpeta completa y produce el backlog estético.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PIL import ImageGrab

DEFAULT_OUTPUT_DIR = Path("qa_screenshots")


def capture_screen(output_path: Path) -> bool:
    """Capture the full primary screen and save it as PNG.

    Args:
        output_path: Destination PNG path (parent dirs created as needed).

    Returns:
        True when the capture was saved successfully.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shot = ImageGrab.grab()
        shot.save(output_path, format="png")
        return True
    except Exception as exc:  # pragma: no cover - depende del entorno gráfico
        print(f"  [ERR] No se pudo capturar: {exc}")
        return False


def main() -> None:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== VISUAL QA CAPTURE — Audio2Text ===")
    print("1) Abrí la app y posicioná la ventana")
    print("2) Cambiá la app al estado que quieras auditar (pestaña, diálogo, cola...)")
    print("3) Acá: Enter = capturar · e = capturar con etiqueta · q = terminar")
    print(f"Destino: {output_dir.resolve()}\n")

    index = 1
    while True:
        raw = input(f"[{index}] Enter=capturar · e=etiquetada · q=salir > ").strip().lower()
        if raw == "q":
            break
        label = ""
        if raw == "e":
            label = input("  Etiqueta breve (ej: supervisor-bloques) > ").strip()
            label = "_" + label.replace(" ", "_") if label else ""
        filename = output_dir / f"{index:02d}{label}.png"
        if capture_screen(filename):
            print(f"  Guardada: {filename}")
            index += 1

    print(f"\nListo: {index - 1} captura(s) en {output_dir.resolve()}/")
    print("Pasale la carpeta al agente para la auditoría estética.")


if __name__ == "__main__":
    main()
