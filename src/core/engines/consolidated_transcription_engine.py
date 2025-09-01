#!/usr/bin/env python3
"""
Refactored consolidated transcription engine using existing services
Follows SOLID principles with dependency injection and no code duplication
"""

import logging
import os
import tempfile
import time
from typing import List, Dict, Any
from src.core.engines.utilities.model_manager import ModelManager
from src.core.engines.utilities.cleanup_manager import CleanupManager
from src.core.interfaces.transcription_engine_interface import ITranscriptionEngine
from src.core.engines.base_interface import TranscriptionEngine
from src.core.engines.strategies.transcription_strategy_factory import TranscriptionStrategyFactory
from src.models import (
    TranscriptionResult, 
    TranscriptionSegment, 
    TranscriptionMetadata,
    TranscriptionError
)

logger = logging.getLogger(__name__)


class ConsolidatedTranscriptionEngine(ITranscriptionEngine, TranscriptionEngine):
    """
    Refactored consolidated transcription engine that coordinates existing services.
    
    This engine follows SOLID principles by:
    - Single Responsibility: Coordinates transcription workflow
    - Open/Closed: Extensible through strategy pattern
    - Liskov Substitution: Implements interfaces correctly
    - Interface Segregation: Uses focused interfaces
    - Dependency Inversion: Depends on abstractions, not concretions
    """
    
    def __init__(self, config_manager, model_manager=None, text_processor=None):
        """
        Initialize the consolidated transcription engine with injected dependencies.
        
        Args:
            config_manager: Configuration manager for settings
            model_manager: Manager for model loading and caching
            text_processor: Service for text post-processing
        """
        if not config_manager:
            raise ValueError("ConfigManager is required - no fallback to direct config")
        
        self.config_manager = config_manager
        
        # Inject dependencies
        self.model_manager = model_manager or ModelManager(config_manager=config_manager)
        self.text_processor = text_processor
        
        if not self.text_processor:
            raise ValueError("Text processor is required - must be injected during initialization")
        
        # Initialize existing services using dependency injection
        self._initialize_services()
        
        # Initialize transcription strategies using existing factory
        self._init_transcription_strategies()
        
        # Initialize cleanup manager
        self._cleanup_manager = CleanupManager(config_manager=config_manager)
        
        logger.info("🚀 Refactored Consolidated Transcription Engine initialized")
        logger.info("✅ Using existing services without code duplication")
    
    def _initialize_services(self) -> None:
        """Initialize existing services using dependency injection"""
        try:
            # Use existing speaker labeling service
            from src.core.models.speaker_labeling_service import SpeakerLabelingService, DefaultSpeakerLabelingConfig
            
            config_dict = self.config_manager.config.dict() if hasattr(self.config_manager.config, 'dict') else self.config_manager.config
            config_provider = DefaultSpeakerLabelingConfig(config_dict)
            self.speaker_labeling_service = SpeakerLabelingService(config_provider)
            
            # Check if speaker diarization is enabled using existing service
            self._speaker_diarization_enabled = self.speaker_labeling_service.should_label_speakers(config_dict)
            
            logger.info(f"ℹ️ Speaker diarization enabled: {self._speaker_diarization_enabled}")
            
        except Exception as e:
            logger.error(f"❌ Speaker service initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize speaker services: {e}")
    
    def _init_transcription_strategies(self) -> None:
        """Initialize transcription strategies using existing factory"""
        try:
            self._strategy_factory = TranscriptionStrategyFactory(self.config_manager)
            logger.info("🔧 Transcription strategies initialized using existing factory")
        except Exception as e:
            logger.error(f"❌ Error initializing transcription strategies: {e}")
            raise
    
    def transcribe(self, audio_file_path: str, model_name: str) -> TranscriptionResult:
        """
        Main transcription entry point using existing services.
        
        Args:
            audio_file_path: Path to the audio file
            model_name: Name of the model to use
            
        Returns:
            TranscriptionResult: The transcription result
        """
        try:
            if not self._validate_audio_file(audio_file_path):
                return self._create_error_result(audio_file_path, model_name, "Audio file not found")
            
            # Use existing transcription strategy factory
            strategy = self._strategy_factory.create_strategy(audio_file_path)
            transcription_result = strategy.execute(audio_file_path, model_name, self)
            
            # Apply speaker diarization if enabled using existing service
            if (self._speaker_diarization_enabled and 
                transcription_result.success and 
                hasattr(transcription_result, 'speakers')):
                
                try:
                    logger.info("🎯 Applying speaker diarization using existing service")
                    enhanced_result = self._apply_speaker_diarization(audio_file_path, transcription_result)
                    if enhanced_result:
                        return enhanced_result
                    else:
                        logger.warning("⚠️ Speaker diarization failed, returning original result")
                        return transcription_result
                        
                except Exception as e:
                    logger.error(f"❌ Error applying speaker diarization: {e}")
                    return transcription_result
            
            return transcription_result
            
        except Exception as e:
            error_msg = f"❌ TRANSCRIPTION FAILED: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _apply_speaker_diarization(self, audio_file_path: str, transcription_result) -> 'TranscriptionResult':
        """Apply speaker diarization using existing services"""
        # For now, use basic enhancement since the orchestrator requires a speaker service
        logger.info("🎯 Using basic speaker enhancement")
        return self._basic_speaker_enhancement(transcription_result)
    
    def _basic_speaker_enhancement(self, transcription_result) -> TranscriptionResult:
        """Basic speaker enhancement when advanced service is not available"""
        try:
            # Simple enhancement: preserve existing speaker structure
            if hasattr(transcription_result, 'speakers') and transcription_result.speakers:
                logger.info("✅ Preserving existing speaker structure")
                return transcription_result
            else:
                # Create basic speaker structure
                from src.models import TranscriptionSegment
                
                if hasattr(transcription_result, 'full_text') and transcription_result.full_text:
                    segment = TranscriptionSegment(
                        start=0.0,
                        end=0.0,
                        text=transcription_result.full_text,
                        speaker="speaker_1"
                    )
                    
                    enhanced_result = TranscriptionResult(
                        success=True,
                        text=transcription_result.full_text,
                        segments=[segment],
                        metadata=TranscriptionMetadata(
                            model_name=transcription_result.model_name,
                            engine="consolidated",
                            language="he",
                            processing_time=transcription_result.transcription_time
                        ),
                        speakers={"speaker_1": [segment]},
                        speaker_count=1
                    )
                    
                    logger.info("✅ Basic speaker enhancement applied")
                    return enhanced_result
                
                return transcription_result
                
        except Exception as e:
            logger.error(f"❌ Error in basic speaker enhancement: {e}")
            return transcription_result
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> TranscriptionResult:
        """Transcribe a single audio chunk using existing model manager"""
        logger.info(f"🔍 Transcribing chunk {chunk_count}")
        
        try:
            # Use existing model manager
            processor, model = self.model_manager.get_or_load_model(model_name)
            language = self._get_language_config()
            
            # Execute transcription
            raw_text = self._execute_transcription(audio_chunk, processor, model, language)
            
            # Post-process using injected text processor
            if self.text_processor:
                processed_text = self.text_processor.filter_language_only(raw_text, language)
            else:
                processed_text = raw_text
            
            logger.info(f"✅ Chunk {chunk_count} transcribed successfully")
            
            # Create and return TranscriptionResult object
            from src.models import TranscriptionResult, TranscriptionSegment, TranscriptionMetadata
            
            # Create segment for this chunk
            segment = TranscriptionSegment(
                start=chunk_start,
                end=chunk_end,
                text=processed_text,
                speaker="speaker_1"
            )
            
            # Create result object
            result = TranscriptionResult(
                success=True,
                text=processed_text,
                segments=[segment],
                metadata=TranscriptionMetadata(
                    model_name=model_name,
                    engine="ctranslate2-whisper",
                    language=language,
                    processing_time=chunk_end - chunk_start
                ),
                speakers={"speaker_1": [segment]},
                speaker_count=1
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Chunk {chunk_count} transcription failed: {e}")
            
            # Return error result
            from src.models import TranscriptionResult, TranscriptionMetadata
            
            return TranscriptionResult(
                success=False,
                text="",
                segments=[],
                metadata=TranscriptionMetadata(
                    model_name=model_name,
                    engine="ctranslate2-whisper",
                    language="he",
                    processing_time=0.0
                ),
                error_message=str(e),
                speakers={},
                speaker_count=0
            )
    
    def _execute_transcription(self, audio_chunk, processor, model, language: str) -> str:
        """Execute transcription based on model type"""
        logger.info(f"🔍 Model type detection: {type(model)}")
        logger.info(f"🔍 Model attributes: {[attr for attr in dir(model) if not attr.startswith('_')]}")
        
        if self._is_ct2_model(model):
            logger.info(f"🎯 Using CTranslate2 transcription for model: {type(model)}")
            return self._transcribe_with_ct2(audio_chunk, processor, model, language)
        else:
            logger.info(f"🎯 Using Transformers transcription for model: {type(model)}")
            return self._transcribe_with_transformers(audio_chunk, processor, model, language)
    
    def _is_ct2_model(self, model) -> bool:
        """Check if model is CTranslate2 type"""
        # CTranslate2 models have a different structure than transformers models
        # Check for CTranslate2-specific attributes
        try:
            # More robust detection for CTranslate2 models
            return (hasattr(model, 'generate') and 
                    'ctranslate2' in str(type(model)).lower())
        except Exception:
            return False
    
    def _transcribe_with_ct2(self, audio_chunk, processor, model, language: str) -> str:
        """Transcribe using CTranslate2 model"""
        import ctranslate2
        
        logger.info(f"🔍 CTranslate2 transcription - Model type: {type(model)}")
        logger.info(f"🔍 CTranslate2 transcription - Model class: {model.__class__.__name__}")
        
        # Prepare features
        features = self._prepare_ct2_features(processor, audio_chunk)
        logger.info(f"🔍 CTranslate2 features prepared: {type(features)}")
        
        # Get configuration from config manager
        config = self._get_ct2_config()
        logger.info(f"🔍 CTranslate2 config: {config}")
        
        # Force Hebrew language for the generation
        hebrew_prompts = self._get_hebrew_ct2_prompts(processor, language)
        logger.info(f"🔍 Hebrew prompts: {hebrew_prompts}")
        
        # Generate transcription using CTranslate2 Whisper API
        # Based on the error message, the correct signature is:
        # generate(features, prompts, *, suppress_tokens, beam_size, max_length, etc.)
        logger.info(f"🔍 Calling CTranslate2 generate with: features={type(features)}, prompts={hebrew_prompts}")
        
        generation_result = model.generate(
            features,
            prompts=hebrew_prompts,
            suppress_tokens=self.text_processor.get_language_suppression_tokens(language) if self.text_processor else [],
            beam_size=config['beam_size'],
            max_length=config['max_length']
        )
        
        # Log the complete generation result for debugging
        logger.info(f"🔍 Generation result type: {type(generation_result)}")
        logger.info(f"🔍 Generation result attributes: {dir(generation_result)}")
        logger.info(f"🔍 Generation result: {generation_result}")
        
        # Try to access different attributes to understand the structure
        if hasattr(generation_result, '__dict__'):
            logger.info(f"🔍 Generation result __dict__: {generation_result.__dict__}")
        
        # Check if it's a list or has a specific structure
        if isinstance(generation_result, list):
            logger.info(f"🔍 Generation result is a list with {len(generation_result)} items")
            for i, item in enumerate(generation_result):
                logger.info(f"🔍 Item {i} type: {type(item)}")
                logger.info(f"🔍 Item {i} attributes: {dir(item)}")
                if hasattr(item, '__dict__'):
                    logger.info(f"🔍 Item {i} __dict__: {item.__dict__}")
        
        logger.info(f"🔍 CTranslate2 generation result: {type(generation_result)}")
        return self._decode_ct2_result(generation_result, processor)
    
    def _transcribe_with_transformers(self, audio_chunk, processor, model, language: str) -> str:
        """Transcribe using transformers model"""
        import torch
        
        features = self._prepare_transformers_features(processor, audio_chunk)
        
        config = self._get_transformers_config()
        
        with torch.no_grad():
            predicted_ids = model.generate(
                features,
                forced_decoder_ids=processor.get_decoder_prompt_ids(language=language, task="transcribe"),
                suppress_tokens=self.text_processor.get_language_suppression_tokens(language) if self.text_processor else [],
                num_beams=config['beam_size'],
                temperature=config['temperature'],
                do_sample=config['do_sample'],
                max_new_tokens=config['max_new_tokens']
            )
        
        return processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    
    def _prepare_ct2_features(self, processor, audio_chunk):
        """Prepare audio features for CTranslate2"""
        import ctranslate2
        features = processor(audio_chunk, sampling_rate=16000, return_tensors="np").input_features
        features = features.astype("float32")
        return ctranslate2.StorageView.from_array(features)
    
    def _prepare_transformers_features(self, processor, audio_chunk):
        """Prepare audio features for transformers"""
        features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
        return features.float()
    
    def _get_ct2_prompts(self, processor, language: str):
        """Get prompts for CTranslate2 generation"""
        try:
            decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
            if decoder_ids:
                prompt_token_ids = [token_id for _, token_id in decoder_ids]
                start_token = processor.tokenizer.encode("<|startoftranscript|>", add_special_tokens=False)
                if start_token and start_token[0] not in prompt_token_ids:
                    prompt_token_ids = start_token + prompt_token_ids
                return [prompt_token_ids]
        except Exception:
            pass
        return []
    
    def _get_hebrew_ct2_prompts(self, processor, language: str):
        """Get Hebrew-specific prompts for CTranslate2 generation"""
        try:
            # Force Hebrew language tokens
            if language == "he":
                # Hebrew language token: 50360
                # Transcribe task token: 50359
                # Start of transcript token: 50258
                hebrew_prompts = [
                    [50258, 50359, 50360]  # <|startoftranscript|><|transcribe|><|he|>
                ]
                logger.info(f"🔍 Using Hebrew-specific prompts: {hebrew_prompts}")
                return hebrew_prompts
            else:
                # Fallback to regular prompts
                return self._get_ct2_prompts(processor, language)
        except Exception as e:
            logger.error(f"🔍 Error creating Hebrew prompts: {e}")
            # Fallback to regular prompts
            return self._get_ct2_prompts(processor, language)
    
    def _decode_ct2_result(self, generation_result, processor) -> str:
        """
        Decode CTranslate2 generation result using raw token IDs for proper Hebrew text
        
        RULE: Use only sequences_ids (raw token IDs) - no fallbacks
        - sequences_ids contains the actual token IDs that decode to Hebrew text
        - sequences contains corrupted text tokens that should be ignored
        - This approach ensures proper Hebrew Unicode handling
        """
        try:
            logger.info(f"🔍 Decoding CTranslate2 result: {type(generation_result)}")
            
            # CTranslate2 Whisper returns a list of WhisperGenerationResult objects
            if isinstance(generation_result, list) and len(generation_result) > 0:
                first_result = generation_result[0]
                logger.info(f"🔍 First result type: {type(first_result)}")
                
                # RULE: Use only sequences_ids (raw token IDs) - no fallbacks
                if hasattr(first_result, 'sequences_ids') and first_result.sequences_ids:
                    logger.info(f"🔍 Found sequences_ids: {type(first_result.sequences_ids)}")
                    
                    if isinstance(first_result.sequences_ids, list) and len(first_result.sequences_ids) > 0:
                        token_ids = first_result.sequences_ids[0]
                        logger.info(f"🔍 Using token IDs: {token_ids[:10]}...")
                        
                        if token_ids and isinstance(token_ids[0], int):
                            # Decode using the processor - this should give us proper Hebrew text
                            decoded = processor.batch_decode([token_ids], skip_special_tokens=True)
                            if decoded and len(decoded) > 0:
                                result = decoded[0]
                                logger.info(f"🔍 ✅ Successfully decoded Hebrew text: {result}")
                                return result
                            else:
                                raise ValueError("Empty decode result from processor.batch_decode")
                        else:
                            raise ValueError(f"Invalid token IDs format: {type(token_ids[0]) if token_ids else 'empty'}")
                    else:
                        raise ValueError("sequences_ids is empty or not a list")
                else:
                    raise ValueError("No sequences_ids found in generation result")
            else:
                raise ValueError(f"Invalid generation result format: {type(generation_result)}")
                
        except Exception as e:
            logger.error(f"❌ Error decoding CTranslate2 result: {e}")
            raise
    
    def _get_language_config(self) -> str:
        """Get language configuration from config manager"""
        return getattr(self.config_manager.config.transcription, 'language', 'he')
    
    def _get_ct2_config(self) -> Dict[str, Any]:
        """Get CTranslate2 configuration from config manager"""
        # Try ctranslate2_optimization first, fallback to ctranslate2_specific
        ct2_config = self.config_manager.config.transcription.ctranslate2_optimization
        if ct2_config is None:
            # Use ctranslate2_specific as fallback
            ct2_config = self.config_manager.config.ctranslate2_specific
        
        # Get beam_size from transcription config or use default
        beam_size = getattr(self.config_manager.config.transcription, 'beam_size', 5)
        
        return {
            'beam_size': beam_size,
            'max_length': 10000 + 1000,  # Default max_new_tokens + buffer
            'temperature': 0.0,  # Default temperature
            'cpu_threads': getattr(ct2_config, 'cpu_threads', 8),
            'compute_type': getattr(ct2_config, 'compute_type', 'float32')
        }
    
    def _get_transformers_config(self) -> Dict[str, Any]:
        """Get transformers configuration from config manager"""
        # Get beam_size from transcription config or use default
        beam_size = getattr(self.config_manager.config.transcription, 'beam_size', 5)
        
        return {
            'beam_size': beam_size,
            'temperature': 0.0,  # Default temperature
            'do_sample': False,  # Default do_sample
            'max_new_tokens': 10000  # Default max_new_tokens
        }
    
    def _validate_audio_file(self, audio_file_path: str) -> bool:
        """Validate audio file exists and is accessible"""
        from pathlib import Path
        return Path(audio_file_path).exists()
    
    def _create_error_result(self, audio_file_path: str, model_name: str, error_message: str) -> TranscriptionResult:
        """Create error result with consistent structure"""
        from src.models import TranscriptionResult
        
        return TranscriptionResult(
            success=False,
            text="",
            segments=[],
            metadata=TranscriptionMetadata(
                model_name=model_name,
                engine="consolidated",
                language="he",
                processing_time=0.0
            ),
            error_message=error_message,
            speakers={},
            speaker_count=0
        )
    
    def is_available(self) -> bool:
        """Check if the engine is available"""
        try:
            import ctranslate2
            import transformers
            return True
        except ImportError:
            return False
    
    def cleanup_models(self) -> None:
        """Clean up loaded models and free memory"""
        self.model_manager.cleanup_models()
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the engine"""
        cache_info = self.model_manager.get_cache_info()
        return {
            "engine_type": "RefactoredConsolidatedTranscriptionEngine",
            "config": str(self.config_manager.config),
            "loaded_models_count": cache_info["loaded_models_count"],
            "processor_cache_size": cache_info["processor_cache_size"],
            "cached_models": cache_info["cached_models"],
            "speaker_diarization_enabled": self._speaker_diarization_enabled,
            "refactored": True,
            "no_duplication": True
        }
    

