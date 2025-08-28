#!/usr/bin/env python3
"""
Factory for creating progress monitors based on configuration
"""

from src.utils.config_manager import ConfigManager
from src.core.interfaces.transcription_protocols import ProgressMonitorProtocol
from src.core.models.simple_progress_monitor import SimpleProgressMonitor
from src.core.models.advanced_progress_monitor import AdvancedProgressMonitor


class ProgressMonitorFactory:
    """Factory for creating progress monitors based on configuration"""

    @staticmethod
    def create_monitor(config_manager: ConfigManager) -> ProgressMonitorProtocol:
        """
        Create appropriate progress monitor based on config
        
        Args:
            config_manager: Configuration manager instance
            
        Returns:
            ProgressMonitorProtocol implementation
        """
        config = config_manager.config

        # Check if advanced progress monitoring is enabled
        if hasattr(config, 'system') and config.system and getattr(config.system, 'advanced_monitoring', False):
            return AdvancedProgressMonitor(config_manager)
        else:
            return SimpleProgressMonitor(config_manager)
