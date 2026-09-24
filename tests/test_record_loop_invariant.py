"""
Test estructural: invariante del hot-loop _record_loop.

Verifica que _record_loop no toque UI directamente (solo vía timer_queue).
"""
import inspect
from pathlib import Path


def _get_record_loop_source() -> str:
    from backend.transcriber import Transcriber
    return inspect.getsource(Transcriber._record_loop)


def test_record_loop_no_direct_ui_calls():
    src = _get_record_loop_source()
    # Excluir docstring del análisis — solo código ejecutable
    # Remover contenido entre triples comillas para no contar menciones explicativas
    import re
    code_only = re.sub(r'""".*?"""', '', src, flags=re.DOTALL)
    code_only = re.sub(r"'''.*?'''", '', code_only, flags=re.DOTALL)
    # No debe llamar update_status ni overlay_callback directamente (solo vía timer_queue)
    assert "update_status" not in code_only, "_record_loop no debe llamar update_status directo — usar timer_queue"
    assert "overlay_callback" not in code_only, "_record_loop no debe llamar overlay_callback directo — usar timer_queue"
    # Debe usar timer_queue
    assert "timer_queue" in src, "_record_loop debe usar timer_queue para comunicación no bloqueante"


def test_record_loop_uses_timer_queue_put_nowait():
    src = _get_record_loop_source()
    assert "put_nowait" in src, "_record_loop debe usar put_nowait (no bloqueante)"
