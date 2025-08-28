#!/usr/bin/env python3
"""
Factory for creating output strategies with proper dependency injection
Follows SOLID principles and factory pattern
"""

import logging
from typing import TYPE_CHECKING

from src.core.engines.strategies.output_strategy import (
    OutputStrategy,
    MergedOutputStrategy,
    IntelligentDeduplicationStrategy,
    OverlappingTextDeduplicator
)

if TYPE_CHECKING:
    from src.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class OutputStrategyFactory:
    """Factory for creating output strategies with dependency injection"""
    
    @staticmethod
    def create_merged_output_strategy(config_manager: 'ConfigManager') -> MergedOutputStrategy:
        """Create a merged output strategy with intelligent deduplication"""
        try:
            # Create the deduplicator
            deduplicator = OverlappingTextDeduplicator(config_manager)
            
            # Create the output strategy with injected deduplicator
            strategy = MergedOutputStrategy(config_manager, deduplicator)
            
            logger.info("✅ MergedOutputStrategy created successfully with dependency injection")
            return strategy
            
        except Exception as e:
            logger.error(f"❌ Failed to create MergedOutputStrategy: {e}")
            raise RuntimeError(f"Failed to create MergedOutputStrategy: {e}")
    
    @staticmethod
    def create_deduplicator(config_manager: 'ConfigManager') -> IntelligentDeduplicationStrategy:
        """Create a deduplicator strategy"""
        try:
            deduplicator = OverlappingTextDeduplicator(config_manager)
            logger.info("✅ OverlappingTextDeduplicator created successfully")
            return deduplicator
            
        except Exception as e:
            logger.error(f"❌ Failed to create OverlappingTextDeduplicator: {e}")
            raise RuntimeError(f"Failed to create OverlappingTextDeduplicator: {e}")
    
    @staticmethod
    def create_custom_output_strategy(
        config_manager: 'ConfigManager',
        deduplicator: IntelligentDeduplicationStrategy
    ) -> MergedOutputStrategy:
        """Create a custom output strategy with a specific deduplicator"""
        try:
            strategy = MergedOutputStrategy(config_manager, deduplicator)
            logger.info("✅ Custom MergedOutputStrategy created successfully")
            return strategy
            
        except Exception as e:
            logger.error(f"❌ Failed to create custom MergedOutputStrategy: {e}")
            raise RuntimeError(f"Failed to create custom MergedOutputStrategy: {e}")

    @staticmethod
    def create_output_manager_with_strategy(config_manager: 'ConfigManager') -> 'OutputManager':
        """Create an OutputManager with injected output strategy for document generation"""
        try:
            # Import here to avoid circular imports
            from src.output_data.managers.output_manager import OutputManager
            
            # Create the output strategy
            output_strategy = OutputStrategyFactory.create_merged_output_strategy(config_manager)
            
            # Create the output manager with injected strategy
            output_manager = OutputManager(output_strategy=output_strategy)
            
            logger.info("✅ OutputManager created successfully with injected output strategy")
            return output_manager
            
        except Exception as e:
            logger.error(f"❌ Failed to create OutputManager with strategy: {e}")
            raise RuntimeError(f"Failed to create OutputManager with strategy: {e}")
