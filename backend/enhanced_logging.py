"""
Enhanced Logging System - Sistema de logging configurable con export

Permite configurar niveles de logging, guardar logs en archivo,
y exportar logs para soporte técnico.

Author: Audio2Text Development Team
Version: 0.15.0
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class EnhancedLoggingSystem:
    """
    Sistema de logging mejorado con configuración flexible.

    Features:
    - Configurar nivel de logging por módulo
    - Rotación de logs por tamaño
    - Exportar logs a archivo para soporte
    - Filtrar logs por nivel y fecha
    """

    def __init__(self, config_manager=None):
        """
        Inicializar sistema de logging mejorado.

        Args:
            config_manager: Gestor de configuración (opcional)
        """
        self.config_manager = config_manager
        self.log_file = None
        self.handlers = {}

        # Determinar directorio base
        if getattr(sys, 'frozen', False):
            # Ejecutándose como .exe compilado
            base_dir = os.getcwd()
        else:
            # Ejecutándose como script Python
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Directorio de logs
        self.logs_dir = Path(base_dir) / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Archivo de log principal
        timestamp = datetime.now().strftime("%Y%m%d")
        self.log_file = self.logs_dir / f"audio2text_{timestamp}.log"

        # Configurar logging
        self._setup_logging()

    def _setup_logging(self):
        """Configurar sistema de logging."""
        # Obtener nivel de logging desde config
        log_level_str = self._get_config("log_level", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)

        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Crear formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler para consola (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        self.handlers['console'] = console_handler

        # Handler para archivo (con rotación)
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            self.handlers['file'] = file_handler
        except Exception as e:
            print(f"Error creando file handler: {e}")

        logging.info(f"Sistema de logging inicializado - Nivel: {log_level_str}, Archivo: {self.log_file}")

    def _get_config(self, key: str, default=None):
        """Obtener valor de configuración."""
        if self.config_manager:
            return self.config_manager.get(key, default)
        return default

    def set_log_level(self, level: str):
        """
        Cambiar nivel de logging.

        Args:
            level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(numeric_level)

        # Guardar en config
        if self.config_manager:
            self.config_manager.config["log_level"] = level.upper()
            self.config_manager.save_config()

        logging.info(f"Nivel de logging cambiado a: {level.upper()}")

    def get_log_level(self) -> str:
        """Obtener nivel de logging actual."""
        level = logging.getLogger().level
        for name, value in logging._nameToLevel.items():
            if value == level:
                return name
        return "INFO"

    def export_logs_to_file(self, output_path: str = None) -> str:
        """
        Exportar logs actuales a un archivo para soporte.

        Args:
            output_path: Ruta donde guardar el archivo (opcional)

        Returns:
            Ruta del archivo exportado
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.logs_dir / f"logs_export_{timestamp}.txt"

        output_path = Path(output_path)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("Audio2Text - Log Export para Soporte Técnico\n")
                f.write("=" * 80 + "\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Archivo de log: {self.log_file}\n")
                f.write(f"Nivel de logging: {self.get_log_level()}\n")
                f.write("=" * 80 + "\n\n")

                # Contenido del log
                if self.log_file.exists():
                    with open(self.log_file, 'r', encoding='utf-8') as log_file:
                        f.write(log_file.read())
                else:
                    f.write("(No hay archivo de log disponible)\n")

                # Info del sistema
                f.write("\n" + "=" * 80 + "\n")
                f.write("Información del Sistema\n")
                f.write("=" * 80 + "\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"Plataforma: {sys.platform}\n")
                f.write(f"Executándose como: {'Compilado' if getattr(sys, 'frozen', False) else 'Script'}\n")

                # Config
                if self.config_manager:
                    f.write("\nConfiguración:\n")
                    config_safe = {k: v for k, v in self.config_manager.config.items()
                                   if not any(x in k.lower() for x in ['key', 'password', 'token'])}
                    f.write(json.dumps(config_safe, indent=2, ensure_ascii=False))

            logging.info(f"Logs exportados a: {output_path}")
            return str(output_path)

        except Exception as e:
            logging.error(f"Error exportando logs: {e}")
            return None

    def get_logs_by_level(self, level: str, last_n_lines: int = 100) -> list:
        """
        Obtener logs filtrados por nivel.

        Args:
            level: Nivel a filtrar ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            last_n_lines: Últimas N líneas a considerar

        Returns:
            Lista de líneas de log que coinciden con el nivel
        """
        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Tomar últimas N líneas
            lines = lines[-last_n_lines:] if len(lines) > last_n_lines else lines

            # Filtrar por nivel
            filtered = [line.strip() for line in lines if f"- {level.upper()} -" in line]

            return filtered

        except Exception as e:
            logging.error(f"Error leyendo logs: {e}")
            return []

    def get_error_logs(self, last_n_lines: int = 100) -> list:
        """Obtener últimos logs de ERROR y CRITICAL."""
        errors = self.get_logs_by_level("ERROR", last_n_lines)
        criticals = self.get_logs_by_level("CRITICAL", last_n_lines)
        return errors + criticals

    def clear_logs(self) -> bool:
        """
        Limpiar archivo de log actual.

        Returns:
            True si se limpió exitosamente
        """
        try:
            if self.log_file.exists():
                with open(self.log_file, 'w') as f:
                    f.write("")
                logging.info("Log limpiado")
                return True
            return False
        except Exception as e:
            logging.error(f"Error limpiando log: {e}")
            return False

    def get_log_file_path(self) -> str:
        """Obtener ruta del archivo de log actual."""
        return str(self.log_file)

    def get_logs_dir(self) -> str:
        """Obtener directorio de logs."""
        return str(self.logs_dir)
