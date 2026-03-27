# -*- coding: utf-8 -*-
"""
Startup Manager - Gestión del inicio automático con Windows
Maneja la creación/eliminación de accesos directos en la carpeta Startup del usuario.
No requiere permisos de administrador.
"""

import os
import sys
import logging
import win32com.client
from pathlib import Path


class StartupManager:
    """Gestiona el inicio automático de la aplicación con Windows"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_name = "Audio2Text_CENF"
        self.startup_folder = self._get_startup_folder()
        self.shortcut_path = os.path.join(self.startup_folder, f"{self.app_name}.lnk")
    
    def _get_startup_folder(self) -> str:
        """
        Obtiene la ruta de la carpeta Startup del usuario actual
        Returns:
            str: Ruta absoluta a la carpeta Startup
        """
        startup_path = os.path.join(
            os.environ['APPDATA'],
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        
        # Crear la carpeta si no existe (edge case)
        if not os.path.exists(startup_path):
            os.makedirs(startup_path)
            self.logger.info(f"Carpeta Startup creada en: {startup_path}")
        
        return startup_path
    
    def _get_executable_path(self) -> str:
        """
        Obtiene la ruta del ejecutable actual
        Returns:
            str: Ruta al ejecutable (.exe) o al script (.py) si se ejecuta desde fuente
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return sys.executable
        else:
            # Running from source - use python.exe with script path
            # NOTE: En producción siempre será .exe, pero esto permite testing
            return os.path.abspath(sys.argv[0])
    
    def is_enabled(self) -> bool:
        """
        Verifica si el inicio automático está habilitado
        Returns:
            bool: True si existe el acceso directo en Startup
        """
        exists = os.path.exists(self.shortcut_path)
        self.logger.debug(f"Inicio automático {'habilitado' if exists else 'deshabilitado'}: {self.shortcut_path}")
        return exists
    
    def enable(self) -> bool:
        """
        Habilita el inicio automático creando un acceso directo en Startup
        Returns:
            bool: True si se creó exitosamente, False en caso de error
        """
        try:
            # Si ya existe, no hacer nada
            if self.is_enabled():
                self.logger.info("El acceso directo ya existe en Startup")
                return True
            
            # Crear el acceso directo usando win32com
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(self.shortcut_path)
            shortcut.TargetPath = self._get_executable_path()
            shortcut.WorkingDirectory = os.path.dirname(self._get_executable_path())
            shortcut.IconLocation = self._get_executable_path()
            shortcut.Description = "Audio2Text CENF - Transcripción de audio en tiempo real"
            shortcut.save()
            
            self.logger.info(f"Acceso directo creado exitosamente en: {self.shortcut_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al crear acceso directo en Startup: {e}", exc_info=True)
            return False
    
    def disable(self) -> bool:
        """
        Deshabilita el inicio automático eliminando el acceso directo de Startup
        Returns:
            bool: True si se eliminó exitosamente o no existía, False en caso de error
        """
        try:
            # Si no existe, no hacer nada
            if not self.is_enabled():
                self.logger.info("El acceso directo no existe en Startup")
                return True
            
            # Eliminar el acceso directo
            os.remove(self.shortcut_path)
            self.logger.info(f"Acceso directo eliminado de: {self.shortcut_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al eliminar acceso directo de Startup: {e}", exc_info=True)
            return False
    
    def toggle(self, enable: bool) -> bool:
        """
        Habilita o deshabilita el inicio automático según el parámetro
        Args:
            enable (bool): True para habilitar, False para deshabilitar
        Returns:
            bool: True si la operación fue exitosa
        """
        if enable:
            return self.enable()
        else:
            return self.disable()
