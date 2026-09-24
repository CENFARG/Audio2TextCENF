"""
VocabDialogMixin — extracted from ui/app.py for HC-02 god-class remediation.

Mueve: _show_vocab_corrections + bulk logic (Shift rango, seleccionar todos),
       _delete_vocab_correction, _edit_vocab_correction, _add_vocab_correction,
       _import_vocab_file, _export_vocab_file, _refresh_vocab_list.

API preservada: App hereda el mixin; todos los callers existentes siguen funcionando.

HC-03 Shift fallback incluido (ctypes -> keyboard -> log WARNING).

TODO v0.16: extraer VocabDialog a clase con inyección de CustomVocabulary y desacoplar de App.
"""
import os
import logging
import tkinter as tk
from tkinter import messagebox, filedialog

logger = logging.getLogger(__name__)


class VocabDialogMixin:
    """Mixin de gestión de vocabulario personalizado."""

    # ── CRUD básico ───────────────────────────────────────────────────
    def _add_vocab_correction(self):
        """Agregar corrección de vocabulario personalizado."""
        incorrect = self.vocab_incorrect_var.get().strip()
        correct = self.vocab_correct_var.get().strip()
        if not incorrect or not correct:
            self.update_status("Debe ingresar ambas palabras", "orange")
            return
        if hasattr(self.transcriber, 'custom_vocab'):
            success = self.transcriber.custom_vocab.add_correction(incorrect, correct)
            if success:
                self.update_status(f"Corrección agregada: {incorrect} → {correct}", "green")
                self.vocab_incorrect_var.set("")
                self.vocab_correct_var.set("")
                self._refresh_vocab_list()
            else:
                self.update_status("Error al agregar corrección", "red")
        else:
            self.update_status("CustomVocabulary no disponible", "red")

    def _import_vocab_file(self):
        """Importar correcciones de vocabulario desde un archivo (TXT/MD/JSON)."""
        try:
            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return
            file_path = filedialog.askopenfilename(
                title="Importar vocabulario",
                filetypes=[
                    ("Archivos de vocabulario", "*.txt;*.md;*.json"),
                    ("Texto", "*.txt;*.md"),
                    ("JSON", "*.json"),
                    ("Todos", "*.*")
                ]
            )
            if not file_path:
                return
            count = self.transcriber.custom_vocab.import_from_file(file_path)
            if count > 0:
                self.update_status(f"✅ {count} correcciones importadas de {os.path.basename(file_path)}", "green")
                self._refresh_vocab_list()
            else:
                self.update_status("No se importó ninguna corrección (revisá el formato: 'incorrecta=correcta' por línea o JSON)", "orange")
        except Exception as e:
            self.logger.error(f"Error importando vocabulario: {e}")
            self.update_status(f"Error importando vocabulario: {e}", "red")

    def _export_vocab_file(self):
        """Exportar el vocabulario actual a un archivo de texto."""
        try:
            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return
            file_path = filedialog.asksaveasfilename(
                title="Exportar vocabulario",
                defaultextension=".txt",
                filetypes=[("Texto", "*.txt"), ("Markdown", "*.md"), ("JSON", "*.json"), ("Todos", "*.*")]
            )
            if not file_path:
                return
            if self.transcriber.custom_vocab.export_to_file(file_path):
                self.update_status(f"✅ Vocabulario exportado a {os.path.basename(file_path)}", "green")
            else:
                self.update_status("Error exportando vocabulario", "red")
        except Exception as e:
            self.logger.error(f"Error exportando vocabulario: {e}")
            self.update_status(f"Error exportando vocabulario: {e}", "red")

    def _delete_vocab_correction(self, incorrect: str, on_deleted=None):
        """Eliminar corrección de vocabulario con refresh INMEDIATO de la lista."""
        try:
            if hasattr(self.transcriber, 'custom_vocab'):
                success = self.transcriber.custom_vocab.remove_correction(incorrect)
                if success:
                    self.update_status(f"Corrección eliminada: {incorrect}", "green")
                    self.logger.info(f"Corrección eliminada: {incorrect}")
                    if on_deleted:
                        on_deleted()
                    self._refresh_vocab_list()
                else:
                    self.update_status("Error al eliminar corrección", "red")
        except Exception as e:
            self.logger.error(f"Error eliminando corrección: {e}")
            self.update_status("Error al eliminar corrección", "red")

    def _edit_vocab_correction(self, incorrect: str, current_correct: str, on_edited=None):
        """Editar una corrección existente — permite cambiar TANTO la palabra incorrecta como la correcta."""
        try:
            import customtkinter as ctk
            try:
                from ui.app import DesignSystem
            except Exception:
                class DesignSystem:  # fallback
                    TYPOGRAPHY = {"body_small": ("Segoe UI", 12, "normal")}

            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return

            edit_window = ctk.CTkToplevel(self)
            edit_window.title("Editar Corrección")
            edit_window.geometry("460x220")
            edit_window.transient(self)
            edit_window.lift()
            edit_window.attributes('-topmost', True)
            edit_window.after(100, lambda: edit_window.attributes('-topmost', False))
            edit_window.grab_set()
            edit_window.resizable(False, False)

            ctk.CTkLabel(edit_window, text="Palabra incorrecta (lo que el modelo entiende mal):", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(padx=15, pady=(10, 2), anchor="w")
            new_incorrect_var = tk.StringVar(value=incorrect)
            incorrect_entry = ctk.CTkEntry(edit_window, textvariable=new_incorrect_var)
            incorrect_entry.pack(padx=15, pady=2, fill="x")

            ctk.CTkLabel(edit_window, text="Palabra correcta (como debe escribirse):", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(padx=15, pady=(8, 2), anchor="w")
            new_correct_var = tk.StringVar(value=current_correct)
            correct_entry = ctk.CTkEntry(edit_window, textvariable=new_correct_var)
            correct_entry.pack(padx=15, pady=2, fill="x")

            def save_edit():
                new_incorrect = new_incorrect_var.get().strip()
                new_correct = new_correct_var.get().strip()
                if not new_incorrect or not new_correct:
                    self.update_status("Ambas palabras deben tener contenido", "orange")
                    return
                if new_incorrect == incorrect and new_correct == current_correct:
                    edit_window.destroy()
                    return
                if new_incorrect != incorrect:
                    for key in list(self.transcriber.custom_vocab.corrections.keys()):
                        if key.lower() == incorrect.lower():
                            del self.transcriber.custom_vocab.corrections[key]
                            break
                self.transcriber.custom_vocab.corrections[new_incorrect] = new_correct
                self.transcriber.custom_vocab._save_vocab()
                self.update_status(f"Corrección actualizada: {new_incorrect}={new_correct}", "green")
                if on_edited:
                    on_edited()
                self._refresh_vocab_list()
                edit_window.destroy()

            btn_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
            btn_frame.pack(pady=12)
            ctk.CTkButton(btn_frame, text="Guardar", width=100, fg_color="#10B981", hover_color="#059669", command=save_edit).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Cancelar", width=100, command=edit_window.destroy).pack(side="left", padx=5)

            incorrect_entry.focus_set()
            incorrect_entry.select_range(0, 'end')

        except Exception as e:
            self.logger.error(f"Error editando corrección: {e}")
            self.update_status(f"Error editando corrección: {e}", "red")

    def _refresh_vocab_list(self):
        """Refrescar lista de correcciones en la pestaña de configuración."""
        try:
            import customtkinter as ctk
            try:
                from ui.app import DesignSystem
            except Exception:
                class DesignSystem:
                    TYPOGRAPHY = {"body_small": ("Segoe UI", 12, "normal")}
            for widget in self.vocab_list_frame.winfo_children():
                widget.destroy()
            if hasattr(self, 'transcriber') and hasattr(self.transcriber, 'custom_vocab'):
                corrections = self.transcriber.custom_vocab.get_corrections()
                if not corrections:
                    ctk.CTkLabel(self.vocab_list_frame, text="No hay correcciones configuradas", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(pady=5)
                else:
                    for incorrect, correct in corrections.items():
                        item = ctk.CTkLabel(self.vocab_list_frame, text=f"{incorrect}={correct}", font=DesignSystem.TYPOGRAPHY["body_small"])
                        item.pack(anchor="w", padx=10, pady=1)
        except Exception as e:
            self.logger.error(f"Error refrescando lista de vocabulario: {e}")

    # ── Dialog bulk ───────────────────────────────────────────────────
    def _show_vocab_corrections(self):
        """Mostrar ventana para ver/editar/eliminar correcciones — con selección múltiple bulk."""
        try:
            import customtkinter as ctk
            try:
                from ui.app import DesignSystem
            except Exception:
                class DesignSystem:
                    TYPOGRAPHY = {
                        "heading_medium": ("Segoe UI", 16, "bold"),
                        "body_small": ("Segoe UI", 12, "normal"),
                        "body_bold": ("Segoe UI", 13, "bold"),
                        "heading_large": ("Segoe UI", 16, "bold"),
                    }

            if not hasattr(self.transcriber, 'custom_vocab'):
                self.update_status("CustomVocabulary no disponible", "red")
                return

            vocab_window = ctk.CTkToplevel(self)
            vocab_window.title("Correcciones de Vocabulario")
            vocab_window.geometry("680x540")
            vocab_window.transient(self)
            vocab_window.lift()
            vocab_window.attributes('-topmost', True)
            vocab_window.after(100, lambda: vocab_window.attributes('-topmost', False))
            vocab_window.grab_set()

            main_frame = ctk.CTkScrollableFrame(vocab_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)

            ctk.CTkLabel(main_frame, text="Correcciones de Vocabulario Personalizado", font=DesignSystem.TYPOGRAPHY["heading_medium"]).pack(pady=10)
            ctk.CTkLabel(main_frame, text="Palabras que el modelo entiende mal y su corrección:", font=DesignSystem.TYPOGRAPHY["body_small"]).pack(pady=5)

            bulk_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            bulk_frame.pack(fill="x", padx=5, pady=(5, 8))

            select_all_var = tk.BooleanVar(value=False)
            bulk_state = {"order": [], "vars": {}, "last_idx": [-1], "select_all_var": select_all_var}

            def _is_shift_pressed() -> bool:
                # HC-03 fallback cross-platform
                try:
                    import ctypes
                    return (ctypes.windll.user32.GetKeyState(0x10) & 0x8000) != 0
                except Exception as e:
                    try:
                        import keyboard as _kb
                        if _kb.is_pressed('shift'):
                            return True
                        if not getattr(_is_shift_pressed, "_warned", False):
                            self.logger.warning(f"Shift fallback activo (ctypes no disponible: {e}) — keyboard usado")
                            _is_shift_pressed._warned = True
                        return False
                    except Exception:
                        pass
                    if not getattr(_is_shift_pressed, "_warned", False):
                        self.logger.warning(f"Shift ctypes fallback sin keyboard (Linux/macOS): {e}")
                        _is_shift_pressed._warned = True
                    return False

            def _update_bulk_button():
                cnt = sum(1 for v in bulk_state["vars"].values() if v.get())
                if cnt:
                    delete_bulk_btn.configure(state="normal", text=f"🗑️ Eliminar seleccionados ({cnt})")
                else:
                    delete_bulk_btn.configure(state="disabled", text="🗑️ Eliminar seleccionados")
                total = len(bulk_state["order"])
                if total and cnt == total:
                    select_all_var.set(True)
                elif cnt == 0:
                    select_all_var.set(False)

            def _on_select_all():
                val = select_all_var.get()
                for v in bulk_state["vars"].values():
                    v.set(val)
                bulk_state["last_idx"][0] = -1
                _update_bulk_button()

            def _on_checkbox(idx: int):
                if _is_shift_pressed() and bulk_state["last_idx"][0] != -1:
                    last = bulk_state["last_idx"][0]
                    lo, hi = (last, idx) if last < idx else (idx, last)
                    key_clicked = bulk_state["order"][idx]
                    new_val = bulk_state["vars"][key_clicked].get()
                    for j in range(lo, hi + 1):
                        k = bulk_state["order"][j]
                        bulk_state["vars"][k].set(new_val)
                bulk_state["last_idx"][0] = idx
                _update_bulk_button()

            select_all_cb = ctk.CTkCheckBox(bulk_frame, text="Seleccionar todos", variable=select_all_var, command=_on_select_all)
            select_all_cb.pack(side="left", padx=5)

            delete_bulk_btn = ctk.CTkButton(bulk_frame, text="🗑️ Eliminar seleccionados", width=200, fg_color="#EF4444", hover_color="#DC2626", state="disabled")
            delete_bulk_btn.pack(side="right", padx=5)

            def _delete_selected():
                selected = [k for k, v in bulk_state["vars"].items() if v.get()]
                if not selected:
                    return
                if not messagebox.askyesno("Confirmar eliminación", f"¿Eliminar {len(selected)} correcciones seleccionadas?\n\n" + ", ".join(selected[:10]) + (f"\n...y {len(selected)-10} más" if len(selected) > 10 else ""), parent=vocab_window):
                    return
                for key in selected:
                    self.transcriber.custom_vocab.remove_correction(key)
                self.update_status(f"🗑️ {len(selected)} correcciones eliminadas", "green")
                self._refresh_vocab_list()
                reload_list()

            delete_bulk_btn.configure(command=_delete_selected)

            hint = ctk.CTkLabel(bulk_frame, text="Tip: Shift+clic para rango", font=ctk.CTkFont(size=10), text_color="#94A3B8")
            hint.pack(side="left", padx=12)

            list_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            list_frame.pack(fill="both", expand=True, padx=5, pady=5)

            def reload_list():
                for widget in list_frame.winfo_children():
                    widget.destroy()
                bulk_state["order"] = []
                bulk_state["vars"] = {}
                bulk_state["last_idx"][0] = -1
                corrections = self.transcriber.custom_vocab.get_corrections()
                if not corrections:
                    ctk.CTkLabel(list_frame, text="No hay correcciones configuradas").pack(pady=20)
                    _update_bulk_button()
                else:
                    for idx, (incorrect, correct) in enumerate(corrections.items()):
                        row_frame = ctk.CTkFrame(list_frame)
                        row_frame.pack(fill="x", pady=2, padx=5)
                        var = tk.BooleanVar(value=False)
                        bulk_state["order"].append(incorrect)
                        bulk_state["vars"][incorrect] = var
                        cb = ctk.CTkCheckBox(row_frame, text="", variable=var, width=20, command=lambda i=idx: _on_checkbox(i))
                        cb.pack(side="left", padx=(8, 2))
                        ctk.CTkLabel(row_frame, text=incorrect, font=DesignSystem.TYPOGRAPHY["body_bold"]).pack(side="left", padx=6)
                        ctk.CTkLabel(row_frame, text="→", font=DesignSystem.TYPOGRAPHY["heading_large"]).pack(side="left", padx=6)
                        ctk.CTkLabel(row_frame, text=correct, font=DesignSystem.TYPOGRAPHY["body_bold"], text_color="#10B981").pack(side="left", padx=6)
                        edit_btn = ctk.CTkButton(row_frame, text="✏️ Editar", width=70, fg_color="#2563EB", hover_color="#1D4ED8",
                                                 command=lambda inc=incorrect, cor=correct: self._edit_vocab_correction(inc, cor, reload_list))
                        edit_btn.pack(side="right", padx=2)
                        delete_btn = ctk.CTkButton(row_frame, text="🗑️", width=30, fg_color="#EF4444", hover_color="#DC2626",
                                                command=lambda inc=incorrect: self._delete_vocab_correction(inc, reload_list))
                        delete_btn.pack(side="right", padx=5)
                    _update_bulk_button()

            reload_list()
            ctk.CTkButton(main_frame, text="Cerrar", command=vocab_window.destroy, width=100).pack(pady=10)
            self.logger.info("Ventana de correcciones mostrada")

        except Exception as e:
            self.logger.error(f"Error mostrando correcciones: {e}")
            self.update_status("Error al mostrar correcciones", "red")
