"""
HistoryViewMixin — extracted from ui/app.py for HC-02 god-class remediation.

Mueve: refresh_history_list, _process_history_batch, _format_duration,
       _create_history_item, _sync_history_after_clear, auto_refresh_history,
       _load_transcriptions_cache, _bind_tooltip, _change_emoji, _play helpers,
       y create_history_tab wiring helpers.

API preservada: App hereda este mixin y expone los mismos métodos sin breaking change.

TODO v0.16: extraer HistoryView a clase vista completa con inyección de dependencias
 (FileManager, MetadataManager, Transcriber) y tests dedicados sin Tk.
"""
import os
import json
import logging
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger(__name__)

# Lazy imports for DesignSystem / emoji_picker to avoid circular at import time


class HistoryViewMixin:
    """Mixin que provee toda la lógica de la pestaña Historial."""

    # ── Duration ──────────────────────────────────────────────────────
    def _format_duration(self, seconds: float) -> str:
        """Formatear duración en formato humano: 42s, 2m 35s, 1h 5m 20s"""
        try:
            s = int(round(seconds))
            if s < 60:
                return f"{s}s"
            m, sec = divmod(s, 60)
            if m < 60:
                return f"{m}m {sec:02d}s"
            h, m = divmod(m, 60)
            return f"{h}h {m}m {sec:02d}s"
        except Exception:
            return "—"

    # ── Transcriptions cache ──────────────────────────────────────────
    def _load_transcriptions_cache(self, force_reload=False):
        """
        Cargar cache de transcripciones desde el archivo JSONL.
        Args:
            force_reload: Si True, recarga el cache aunque el archivo no haya cambiado.
        """
        transcriptions_path = os.path.join("transcriptions", "transcriptions_log.jsonl")
        if not os.path.exists(transcriptions_path):
            return
        try:
            if not force_reload and hasattr(self, '_transcriptions_cache_mtime'):
                current_mtime = os.path.getmtime(transcriptions_path)
                if current_mtime == self._transcriptions_cache_mtime:
                    return
            cache = {}
            with open(transcriptions_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        audio_file = entry.get("audio_file", "")
                        transcription = entry.get("transcription", "")
                        if audio_file and transcription:
                            audio_filename = os.path.basename(audio_file)
                            cache[audio_filename] = transcription
                    except json.JSONDecodeError:
                        continue
            self.transcriptions_cache = cache
            self._transcriptions_cache_mtime = os.path.getmtime(transcriptions_path)
            self.logger.debug(f"Cache de transcripciones cargado: {len(self.transcriptions_cache)} entradas")
        except Exception as e:
            self.logger.error(f"Error cargando cache de transcripciones: {e}")

    # ── History list ──────────────────────────────────────────────────
    def auto_refresh_history(self):
        """Auto-refresh optimizado: solo actualiza si hubo cambios"""
        # late import to avoid circular at module load
        if self.main_frame.get() == self.localization_manager.get_string("tab_history"):
            audio_path = self.config_manager.get("audio_path")
            if os.path.exists(audio_path):
                try:
                    files = [f for f in os.listdir(audio_path) if f.endswith(".wav")]
                    current_count = len(files)
                    current_mtime = max([os.path.getmtime(os.path.join(audio_path, f)) for f in files]) if files else 0
                    if current_count != self.last_history_file_count or current_mtime != self.last_history_mtime:
                        self.refresh_history_list(full_reload=False)
                        self.last_history_file_count = current_count
                        self.last_history_mtime = current_mtime
                except Exception as e:
                    self.logger.error(f"Error verificando cambios en historial: {e}")
        self.after(15000, self.auto_refresh_history)
        self.logger.debug("Auto-optimizado: solo refresca si hay cambios (cada 15s)")

    def refresh_history_list(self, full_reload=False):
        """
        Actualizar lista de historial con estrategia inteligente.
        Args:
            full_reload: Si True, recarga toda la lista. Si False, solo agrega nuevos archivos.
        """
        import customtkinter as ctk  # local for tests without display
        if full_reload or not getattr(self, 'transcriptions_cache', None):
            self._load_transcriptions_cache(force_reload=full_reload)
        else:
            self._load_transcriptions_cache(force_reload=False)

        audio_path = self.config_manager.get("audio_path")
        if not os.path.exists(audio_path):
            if full_reload:
                for widget in self.history_scroll_frame.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(self.history_scroll_frame, text="Directorio no encontrado").pack(pady=20)
            return

        max_display_files = 200
        files_list = self.file_manager.get_audio_files_list(limit=max_display_files)

        if not files_list:
            if full_reload and not self.loaded_history_files:
                ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)
            return

        if full_reload:
            for widget in self.history_scroll_frame.winfo_children():
                widget.destroy()
            self.loaded_history_files.clear()

        current_files = {f["name"] for f in files_list}
        removed = self.loaded_history_files - current_files
        if removed:
            self.logger.debug(f"Detectados {len(removed)} archivos eliminados, haciendo full reload")
            for widget in self.history_scroll_frame.winfo_children():
                widget.destroy()
            self.loaded_history_files.clear()
            self._history_pending = []
            self._history_pending_pos = 0
            if not files_list:
                ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)
                self.loaded_history_files = set()
                return
            self._history_pending = files_list
            self._history_pending_pos = 0
            self._process_history_batch(batch_size=20)
            self.loaded_history_files = current_files
            return

        new_files = [f for f in files_list if f["name"] not in self.loaded_history_files]
        if new_files:
            self._history_pending = new_files
            self._history_pending_pos = 0
            self._process_history_batch(batch_size=20)
            self.logger.debug(f"Agregados {len(new_files)} archivos nuevos al historial (por lotes)")

        if not files_list and not self.history_scroll_frame.winfo_children():
            ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)

        self.loaded_history_files = current_files

    def _process_history_batch(self, batch_size=20):
        """
        FIX: crear items de historial en lotes para no congelar la UI.
        """
        pending = getattr(self, '_history_pending', [])
        pos = getattr(self, '_history_pending_pos', 0)
        end = min(pos + batch_size, len(pending))
        for file_info in pending[pos:end]:
            try:
                self._create_history_item(file_info["name"], file_info["path"], file_info.get("duration", 0))
                self.loaded_history_files.add(file_info["name"])
            except Exception as e:
                self.logger.error(f"Error creando item de historial: {e}")
        self._history_pending_pos = end
        if end < len(pending):
            self.after(15, self._process_history_batch, batch_size)
        else:
            self._history_pending = []
            self._history_pending_pos = 0

    def _create_history_item(self, filename, full_path, duration: float = 0):
        """Crear item de historial con emoji personalizable, play button y menú contextual"""
        import customtkinter as ctk
        # DesignSystem lazy to avoid circular
        try:
            from ui.app import DesignSystem
        except Exception:
            # Fallback minimal if circular not resolved yet
            class DesignSystem:  # type: ignore
                COLORS = {"primary": "#2563EB", "primary_hover": "#1D4ED8", "success": "#10B981", "error": "#EF4444"}
                TYPOGRAPHY = {"body_small": ("Segoe UI", 12, "normal"), "body_bold": ("Segoe UI", 13, "bold"), "heading_large": ("Segoe UI", 16, "bold")}

        item_frame = ctk.CTkFrame(self.history_scroll_frame)
        item_frame.pack(fill="x", pady=2, padx=5)

        custom_emoji = self.metadata_manager.get_emoji(filename, default="🎤")

        try:
            from datetime import datetime
            file_stat = os.stat(full_path)
            file_size = file_stat.st_size
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)

            if filename.startswith("audio_"):
                try:
                    parts = filename.replace(".wav", "").split("_")
                    if len(parts) >= 3:
                        date_part = parts[1]
                        time_part = parts[2]
                        formatted_date = f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]}"
                        formatted_time = f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}"
                        display_name = f"{custom_emoji} {formatted_date} {formatted_time}"
                    else:
                        display_name = f"{custom_emoji} {filename}"
                except Exception:
                    display_name = f"{custom_emoji} {filename}"
            else:
                display_name = f"{custom_emoji} {filename}"

            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"

            if not duration:
                try:
                    duration = self.file_manager._get_wav_duration(full_path)
                except Exception:
                    duration = 0
            duration_str = self._format_duration(duration) if duration else "—"

            tooltip_text = f"📁 {filename}\n📅 {file_mtime.strftime('%d/%m/%Y %H:%M:%S')}\n⏱️ {duration_str}\n💾 {size_str}\n📍 {full_path}"

            if filename in self.transcriptions_cache:
                transcription = self.transcriptions_cache[filename]
                if len(transcription) > 200:
                    transcription = transcription[:200] + "..."
                tooltip_text += f"\n\n💬 {transcription}"

            auto_metadata = self.metadata_manager.get_auto_metadata(filename)
            if auto_metadata:
                if auto_metadata.get("title"):
                    tooltip_text += f"\n\n🏷️ {auto_metadata['title']}"
                if auto_metadata.get("category"):
                    category_emoji = {
                        "trabajo": "💼",
                        "idea": "💡",
                        "personal": "👤",
                        "aprendizaje": "📚",
                        "técnico": "🔧"
                    }.get(auto_metadata['category'].lower(), "📁")
                    tooltip_text += f"\n{category_emoji} {auto_metadata['category'].title()}"
                if auto_metadata.get("tags"):
                    tags_str = ", ".join(auto_metadata['tags'][:5])
                    if tags_str:
                        tooltip_text += f"\n🏷️ {tags_str}"
                if auto_metadata.get("summary"):
                    summary = auto_metadata['summary']
                    if len(summary) > 150:
                        summary = summary[:150] + "..."
                    tooltip_text += f"\n\n📝 {summary}"
                if auto_metadata.get("sentiment"):
                    sentiment_emoji = {
                        "positivo": "😊",
                        "neutral": "😐",
                        "negativo": "😔"
                    }.get(auto_metadata['sentiment'].lower(), "😐")
                    tooltip_text += f"\n{sentiment_emoji} {auto_metadata['sentiment'].title()}"
                if auto_metadata.get("action_items") and len(auto_metadata['action_items']) > 0:
                    tasks = auto_metadata['action_items'][:3]
                    if tasks:
                        tooltip_text += f"\n\n✅ Tareas:"
                        for i, task in enumerate(tasks, 1):
                            tooltip_text += f"\n   {i}. {task}"
        except Exception as e:
            self.logger.error(f"Error obteniendo metadata de {filename}: {e}")
            display_name = f"🎤 {filename}"
            tooltip_text = f"📁 {filename}\n📍 {full_path}"
            duration = 0
            duration_str = "—"

        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)

        name_label = ctk.CTkLabel(info_frame, text=display_name, font=DesignSystem.TYPOGRAPHY["body_small"], anchor="w")
        name_label.pack(side="left", fill="x", expand=True)
        self._bind_tooltip(name_label, tooltip_text)

        action_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        action_frame.pack(side="right", padx=5)

        duration_label = ctk.CTkLabel(
            action_frame,
            text=f"⏱️ {duration_str}",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            width=62,
            anchor="e"
        )
        duration_label.pack(side="left", padx=(0, 4))
        self._bind_tooltip(duration_label, f"Duración: {duration_str}")

        emoji_btn = ctk.CTkButton(
            action_frame,
            text=custom_emoji,
            width=35,
            height=24,
            font=ctk.CTkFont(size=14),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=lambda f=filename, e=custom_emoji: self._change_emoji(f, e, emoji_btn, name_label)
        )
        emoji_btn.pack(side="left", padx=2)

        play_btn = ctk.CTkButton(action_frame, text="▶️", width=35, height=24, fg_color="#10B981", hover_color="#059669")
        play_btn.configure(command=lambda p=full_path, b=play_btn: self._play_audio_file(p, b))
        play_btn.pack(side="left", padx=2)

        ctk.CTkButton(action_frame, text=self.localization_manager.get_string("transcribe_button"), width=80, height=24,
                      command=lambda p=full_path: self._start_retranscription(p)).pack(side="left", padx=2)

        ctk.CTkButton(action_frame, text="🗑️", width=30, height=24, fg_color="#EF4444", hover_color="#DC2626",
                      command=lambda p=full_path: self._delete_audio_file(p)).pack(side="left", padx=2)

    def _bind_tooltip(self, widget, text):
        """Crear tooltip flotante con ventana emergente"""
        try:
            from ui.app import create_tooltip
            create_tooltip(widget, text)
        except Exception:
            # Fallback sin tooltip si circular
            pass

    def _sync_history_after_clear(self):
        """Sincronizar pestaña Historial después de limpiar audios: vaciar lista y mostrar estado vacío."""
        import customtkinter as ctk
        try:
            for widget in self.history_scroll_frame.winfo_children():
                widget.destroy()
            self.loaded_history_files = set()
            self.transcriptions_cache = {}
            self._transcriptions_cache_mtime = 0
            self._history_pending = []
            self._history_pending_pos = 0
            ctk.CTkLabel(self.history_scroll_frame, text=self.localization_manager.get_string("no_audio_files")).pack(pady=20)
            self.last_history_file_count = 0
            self.last_history_mtime = 0
        except Exception as e:
            self.logger.error(f"Error sincronizando historial tras clear: {e}")
