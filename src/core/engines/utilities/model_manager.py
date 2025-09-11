#!/usr/bin/env python3
"""
Model Manager Utility
Handles model loading, caching, and cleanup for transcription engines
"""

import logging
import gc
import os
import json
import time
from typing import Dict, Any, Tuple, Optional

# Model loading imports
from ctranslate2.models import Whisper
from transformers import WhisperProcessor

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model loading, caching, and cleanup for transcription engines"""
    
    def __init__(self, config_manager: Any):
        """Initialize model manager with ConfigManager for configuration
        
        Args:
            config_manager: ConfigManager instance for configuration and processor injection
            
        Raises:
            ValueError: If config_manager is not provided
            ValueError: If ConfigManager doesn't contain required configuration
            FileNotFoundError: If the models directory doesn't exist
        """
        self._model_cache = {}
        self._processor_cache = {}
        self._config_manager = config_manager
        
        # Models path must come from ConfigManager
        if config_manager is None:
            raise ValueError("ConfigManager must be provided")
            
        # Validate that all required configuration exists in ConfigManager
        try:
            logger.info(f"🔍 Validating ConfigManager configuration...")
            
            # Check if ConfigManager has config
            if not hasattr(config_manager, 'config'):
                raise ValueError("ConfigManager does not have 'config' attribute")
            
            # Get models path from ConfigManager's directory structure
            # The models directory must be configured in ConfigManager
            config_dir = getattr(config_manager, 'config_dir', None)
            if not config_dir:
                raise ValueError("ConfigManager must have config_dir attribute set")
            
            # Always use 'models' directory relative to project root
            # The config_dir might be config/environments, but models should be at project root
            if 'environments' in str(config_dir):
                # If config_dir is config/environments, go up two levels to project root
                project_root = config_dir.parent.parent
            else:
                # If config_dir is config, go up one level to project root
                project_root = config_dir.parent
            
            self._models_path = str(project_root / 'models')
            
            logger.info(f"✅ Using models_path: {self._models_path}")
            
            # Validate transcription section exists
            if not hasattr(config_manager.config, 'transcription'):
                raise ValueError("ConfigManager missing 'transcription' section")
            
            # Check if ctranslate2_optimization exists (this is what we actually need)
            if not hasattr(config_manager.config.transcription, 'ctranslate2_optimization'):
                logger.warning("⚠️ ConfigManager missing 'transcription.ctranslate2_optimization' section")
            
            logger.info(f"✅ All required configuration validated successfully")
            
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")
        
        # Validate that the models path exists and is a directory
        if not os.path.exists(self._models_path):
            raise FileNotFoundError(f"Models directory does not exist: {self._models_path}")
        
        if not os.path.isdir(self._models_path):
            raise ValueError(f"Models path is not a directory: {self._models_path}")
        
        # Check if directory is readable
        if not os.access(self._models_path, os.R_OK):
            raise PermissionError(f"Models directory is not readable: {self._models_path}")
        
        logger.info(f"✅ Models path validated: {self._models_path}")
        logger.info(f"📊 Models directory contents: {len(os.listdir(self._models_path))} items")
        

    

    
    def get_models_path(self) -> str:
        """Get the configured models path"""
        return self._models_path
    
    def validate_model_path(self, model_name: str) -> bool:
        """Validate if a specific model exists in the models directory
        
        Args:
            model_name: Name of the model to validate
            
        Returns:
            bool: True if model exists and is valid, False otherwise
        """
        if not self._models_path:
            return False
            
        model_path = os.path.join(self._models_path, model_name)
        model_bin_path = os.path.join(model_path, "model.bin")
        
        exists = os.path.exists(model_path) and os.path.exists(model_bin_path)
        if exists:
            logger.info(f"✅ Model validation passed: {model_name} at {model_path}")
        else:
            logger.warning(f"⚠️ Model validation failed: {model_name} not found at {model_path}")
            
        return exists
    
    def list_available_models(self) -> list:
        """List all available models in the models directory
        
        Returns:
            list: List of model names that have valid model.bin files
        """
        if not self._models_path:
            return []
            
        available_models = []
        try:
            for item in os.listdir(self._models_path):
                item_path = os.path.join(self._models_path, item)
                if os.path.isdir(item_path):
                    model_bin_path = os.path.join(item_path, "model.bin")
                    if os.path.exists(model_bin_path):
                        available_models.append(item)
                        logger.debug(f"📁 Found model: {item}")
        except Exception as e:
            logger.warning(f"⚠️ Error listing models: {e}")
            
        logger.info(f"📊 Available models: {len(available_models)} - {available_models}")
        return available_models
    

    
    def get_or_load_model(self, model_name: str) -> Tuple[Any, Any]:
        """Get cached model or load it with optimized settings"""
        if model_name not in self._model_cache:
            logger.info(f"Loading model: {model_name}")
            processor, model = self._load_model(model_name)
            self._model_cache[model_name] = model
            self._processor_cache[model_name] = processor
        
        return self._processor_cache[model_name], self._model_cache[model_name]
    
    def _load_model(self, model_name: str) -> Tuple[Any, Any]:
        """Load model - no fallbacks, must be configured in ConfigManager"""
        is_ct2_model = "-ct2" in model_name
        
        if is_ct2_model:
            return self._load_ct2_model(model_name, is_ct2_model)
        else:
            raise ValueError(f"Only CTranslate2 models are supported. Got: {model_name}")
    
    def _load_ct2_model(self, model_name: str, is_ct2_model: bool) -> Tuple[Any, Any]:
        """Load CTranslate2 model from local models directory"""
        start_time = time.time()
        logger.info(f"🚀 Starting CTranslate2 model load: {model_name}")
        
        # Try to load from local models directory first
        # For CTranslate2 models, check if the model-specific directory contains the required files
        model_path = None
        
        # Construct model path using ConfigManager models_path
        if self._models_path:
            model_path = os.path.join(self._models_path, model_name)
            logger.info(f"🔍 Checking for local model at: {model_path}")
            
            if os.path.exists(model_path) and os.path.exists(os.path.join(model_path, "model.bin")):
                logger.info(f"📁 Loading CTranslate2 model from local path: {model_path}")
                logger.info(f"📊 Model file size: {os.path.getsize(os.path.join(model_path, 'model.bin')) / (1024**3):.2f} GB")
                model = Whisper(model_path)
                logger.info(f"✅ CTranslate2 model loaded successfully from local path in {time.time() - start_time:.2f}s")
            else:
                raise FileNotFoundError(f"Local CTranslate2 model not found at {model_path}. Model must be available locally.")
        else:
            raise ValueError("No models path configured in ConfigManager. Cannot load CTranslate2 model.")
        
        # Load processor - prioritize local files when available
        processor_start = time.time()
        logger.info(f"🔧 Loading WhisperProcessor for: {model_name}")
        processor_source = self._get_processor_source(model_name, is_ct2_model, model_path)
        logger.info(f"📡 Processor source: {processor_source}")
        
        # Load WhisperProcessor for token decoding (required for both regular and CTranslate2 models)
        try:
            processor = WhisperProcessor.from_pretrained(processor_source)
            logger.info(f"✅ WhisperProcessor loaded successfully from: {processor_source}")
        except Exception as e:
            logger.error(f"❌ Failed to load WhisperProcessor from {processor_source}: {e}")
            # Try fallback to original model name
            try:
                processor = WhisperProcessor.from_pretrained(model_name)
                logger.info(f"✅ WhisperProcessor loaded from fallback: {model_name}")
            except Exception as fallback_error:
                logger.error(f"❌ Failed to load WhisperProcessor fallback: {fallback_error}")
                raise ValueError(f"Unable to load WhisperProcessor for {model_name}")
        
        logger.info(f"✅ WhisperProcessor loaded in {time.time() - processor_start:.2f}s")
        
        total_time = time.time() - start_time
        logger.info(f"🎯 Total model loading time: {total_time:.2f}s")
        logger.info(f"📈 Model cache status: {len(self._model_cache)} models cached")
        
        return processor, model
    

    
    def _get_processor_source(self, model_name: str, is_ct2_model: bool, model_path: Optional[str] = None) -> str:
        """Get appropriate processor source for model - must use ConfigManager configuration"""
        # Use ConfigManager for processor sources - NO FALLBACKS
        if is_ct2_model and self._config_manager:
            try:
                # Use the models path from ConfigManager
                if hasattr(self._config_manager, 'config') and hasattr(self._config_manager.config, 'transcription'):
                    
                    # Check if we have ctranslate2_optimization config
                    if hasattr(self._config_manager.config.transcription, 'ctranslate2_optimization'):
                        # Use the full model path for processor source
                        if model_path:
                            processor_source = model_path
                            logger.info(f"🔧 Using full model path for processor source: {processor_source}")
                            return processor_source
                        else:
                            raise ValueError(f"Model path not available for processor source")
                    
            except Exception as e:
                raise ValueError(f"Error reading processor source from ConfigManager: {e}. Please ensure ctranslate2_optimization section exists.")
        
        # If we reach here, no configuration was found - throw exception
        raise ValueError(f"Processor source configuration not found in ConfigManager for model: {model_name}. Please ensure ctranslate2_optimization section exists.")
    
    def cleanup_memory_only(self) -> None:
        """Clean up memory without unloading models - keeps models in cache"""
        try:
            # Only run garbage collection to free unused memory
            import gc
            gc.collect()
            
            # Log memory cleanup without unloading models
            logger.debug("🧹 Memory cleanup completed (models remain loaded)")
            
        except Exception as e:
            logger.warning(f"⚠️ Memory cleanup failed: {e}")

    def cleanup_models(self) -> None:
        """Clean up loaded models to free memory - use only when completely done"""
        for model_name in list(self._model_cache.keys()):
            logger.info(f"🔄 Unloading model: {model_name}")
            model = self._model_cache[model_name]
            
            if hasattr(model, 'unload_model'):
                model.unload_model()
            
            del self._model_cache[model_name]
            del self._processor_cache[model_name]
        
        self._model_cache.clear()
        self._processor_cache.clear()
        gc.collect()
        logger.info("✅ Model cleanup completed - all models unloaded")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about model cache"""
        return {
            "loaded_models_count": len(self._model_cache),
            "processor_cache_size": len(self._processor_cache),
            "cached_models": list(self._model_cache.keys())
        }
    
    def is_model_cached(self, model_name: str) -> bool:
        """Check if a model is currently cached"""
        return model_name in self._model_cache

    def _inject_processor_config(self, model_path: str) -> None:
        """Log processor configuration from local files"""
        try:
            # Check for any processor config files in the model path
            processor_files = [f for f in os.listdir(model_path) if f.endswith('.json') and 'config' in f.lower()]
            if processor_files:
                logger.info(f"🔧 Found processor config files: {processor_files}")
                
                # Log the first processor config file content for debugging
                processor_config_file = processor_files[0]
                processor_config_path = os.path.join(model_path, processor_config_file)
                with open(processor_config_path, 'r') as f:
                    preprocessor_config = json.load(f)
                
                logger.info(f"🔧 Processor config content: {list(preprocessor_config.keys())}")
            else:
                logger.warning("⚠️ No processor config files found in model path")
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to read processor config: {e}")
