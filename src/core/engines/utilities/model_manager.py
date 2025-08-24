#!/usr/bin/env python3
"""
Model Manager Utility
Handles model loading, caching, and cleanup for transcription engines
"""

import logging
import gc
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model loading, caching, and cleanup for transcription engines"""
    
    def __init__(self):
        """Initialize model manager"""
        self._model_cache = {}
        self._processor_cache = {}
    
    def get_or_load_model(self, model_name: str) -> Tuple[Any, Any]:
        """Get cached model or load it with optimized settings"""
        if model_name not in self._model_cache:
            logger.info(f"Loading model: {model_name}")
            processor, model = self._load_model_with_fallback(model_name)
            self._model_cache[model_name] = model
            self._processor_cache[model_name] = processor
        
        return self._processor_cache[model_name], self._model_cache[model_name]
    
    def _load_model_with_fallback(self, model_name: str) -> Tuple[Any, Any]:
        """Load model with CTranslate2 fallback to transformers"""
        is_ct2_model = "-ct2" in model_name
        
        try:
            return self._load_ct2_model(model_name, is_ct2_model)
        except Exception as e:
            if is_ct2_model:
                raise Exception(f"CTranslate2 model failed to load: {e}")
            return self._load_transformers_model(model_name)
    
    def _load_ct2_model(self, model_name: str, is_ct2_model: bool) -> Tuple[Any, Any]:
        """Load CTranslate2 model"""
        from ctranslate2.models import Whisper
        import transformers
        
        model = Whisper(model_name)
        processor_source = self._get_processor_source(model_name, is_ct2_model)
        processor = transformers.WhisperProcessor.from_pretrained(processor_source, low_cpu_mem_usage=True)
        
        logger.info(f"✅ CTranslate2 model loaded: {model_name}")
        return processor, model
    
    def _load_transformers_model(self, model_name: str) -> Tuple[Any, Any]:
        """Load transformers model"""
        logger.info("Falling back to transformers...")
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        import torch
        
        processor = WhisperProcessor.from_pretrained(model_name, low_cpu_mem_usage=True)
        model = WhisperForConditionalGeneration.from_pretrained(
            model_name, torch_dtype=torch.float32,
            low_cpu_mem_usage=True, attn_implementation="eager"
        )
        
        logger.info(f"✅ Transformers model loaded: {model_name}")
        return processor, model
    
    def _get_processor_source(self, model_name: str, is_ct2_model: bool) -> str:
        """Get appropriate processor source for model"""
        if is_ct2_model:
            if "ivrit-ai/whisper-large-v3-ct2" in model_name:
                return "ivrit-ai/whisper-large-v3"
            elif "large-v3-ct2" in model_name:
                return "openai/whisper-large-v3"
        return model_name
    
    def cleanup_models(self) -> None:
        """Clean up loaded models to free memory"""
        for model_name in list(self._model_cache.keys()):
            logger.info(f"Cleaning up model: {model_name}")
            model = self._model_cache[model_name]
            
            if hasattr(model, 'unload_model'):
                model.unload_model()
            
            del self._model_cache[model_name]
            del self._processor_cache[model_name]
        
        self._model_cache.clear()
        self._processor_cache.clear()
        gc.collect()
        logger.info("Model cleanup completed")
    
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
