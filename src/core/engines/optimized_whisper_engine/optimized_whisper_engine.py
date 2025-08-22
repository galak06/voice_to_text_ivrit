#!/usr/bin/env python3
"""
Optimized Whisper Engine for CTranslate2 models
"""

import logging
import os
import time
from typing import Any, Dict

from ..transcription_engine import TranscriptionEngine

logger = logging.getLogger(__name__)


class OptimizedWhisperEngine(TranscriptionEngine):
    """Engine for optimized Whisper models (higher accuracy and performance)"""
    
    def __init__(self, config, app_config=None):
        super().__init__(config, app_config)
        self.temp_chunks_dir = "output/temp_chunks"
        os.makedirs(self.temp_chunks_dir, exist_ok=True)
        # Add model caching to prevent reloading
        self._model_cache = {}
        self._processor_cache = {}
    
    def is_available(self) -> bool:
        """Check if CTranslate2 and transformers are available"""
        try:
            import ctranslate2
            import transformers
            return True
        except ImportError:
            return False
    
    def _get_or_load_model(self, model_name: str):
        """Get cached model or load it with CTranslate2 optimized settings.
        For ct2 models, use CTranslate2 loader and a compatible HF processor source.
        Avoid falling back to transformers for ct2 artifacts that lack pytorch weights."""
        if model_name not in self._model_cache:
            logger.info(f"Loading CTranslate2 optimized model: {model_name}")

            is_ct2_model = "-ct2" in model_name

            try:
                # Try to load with CTranslate2 first
                from ctranslate2.models import Whisper
                import transformers
                import os

                # Get the actual model path from Hugging Face cache
                cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                model_dir = model_name.replace("/", "--")
                model_path = os.path.join(cache_dir, f"models--{model_dir}")
                
                # Find the latest snapshot
                model = None
                if os.path.exists(model_path):
                    snapshots_dir = os.path.join(model_path, "snapshots")
                    if os.path.exists(snapshots_dir):
                        snapshots = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
                        if snapshots:
                            latest_snapshot = snapshots[0]  # Use first snapshot
                            full_model_path = os.path.join(snapshots_dir, latest_snapshot)
                            if os.path.exists(os.path.join(full_model_path, "model.bin")):
                                logger.info(f"📁 Using model path: {full_model_path}")
                                model = Whisper(full_model_path)
                            else:
                                logger.warning(f"model.bin not found in {full_model_path}, using model name")
                                model = Whisper(model_name)
                        else:
                            logger.warning("No snapshots found, using model name")
                            model = Whisper(model_name)
                    else:
                        logger.warning("No snapshots directory found, using model name")
                        model = Whisper(model_name)
                else:
                    logger.warning(f"Model cache not found at {model_path}, using model name")
                    model = Whisper(model_name)
                
                # Ensure model is loaded
                if model is None:
                    logger.warning("Fallback to using model name directly")
                    model = Whisper(model_name)

                # Select a processor source compatible with the tokenizer
                processor_source = model_name
                if is_ct2_model:
                    # Most ct2 repos do not include HF processor. Fallback to a compatible HF repo
                    if "ivrit-ai/whisper-large-v3-ct2" in model_name:
                        processor_source = "ivrit-ai/whisper-large-v3"
                    elif "large-v3-ct2" in model_name:
                        processor_source = "openai/whisper-large-v3"

                processor = transformers.WhisperProcessor.from_pretrained(
                    processor_source,
                    low_cpu_mem_usage=True
                )

                self._model_cache[model_name] = model
                self._processor_cache[model_name] = processor

                logger.info(f"✅ CTranslate2 optimized model loaded successfully: {model_name}")

            except Exception as e:
                logger.warning(f"CTranslate2 loading failed for {model_name}: {e}")

                if is_ct2_model:
                    # Do not attempt transformers fallback for ct2 models without pytorch weights
                    logger.error("❌ Transformers fallback disabled for ct2 models without pytorch weights")
                    raise

                logger.info("Falling back to transformers Whisper model...")

                from transformers import WhisperProcessor, WhisperForConditionalGeneration
                import torch

                # Load processor
                processor = transformers.WhisperProcessor.from_pretrained(
                    model_name,
                    low_cpu_mem_usage=True,
                )

                # Load model with optimized settings for accuracy
                model = transformers.WhisperForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    low_cpu_mem_usage=True,
                    attn_implementation="eager",
                )

                self._processor_cache[model_name] = processor
                self._model_cache[model_name] = model

                logger.info(f"✅ Transformers model loaded successfully: {model_name}")

        return self._processor_cache[model_name], self._model_cache[model_name]
    
    def cleanup_models(self):
        """Clean up loaded models to free memory"""
        for model_name in list(self._model_cache.keys()):
            logger.info(f"Cleaning up CTranslate2 model: {model_name}")
            model = self._model_cache[model_name]
            
            # Handle CTranslate2 models
            if hasattr(model, 'unload_model'):
                model.unload_model()
            
            del self._model_cache[model_name]
            del self._processor_cache[model_name]
        
        self._model_cache.clear()
        self._processor_cache.clear()
        logger.info("CTranslate2 model cleanup completed")
    
    def _cleanup_model_memory(self):
        """Enhanced memory cleanup for CTranslate2 engine"""
        import gc
        
        logger.info("🧹 CTranslate2 Engine memory cleanup...")
        
        # Force garbage collection
        gc.collect()
        logger.info("✅ CTranslate2 memory cleanup completed")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the OptimizedWhisperEngine"""
        return {
            "engine_type": "OptimizedWhisperEngine",
            "config": str(self.config),
            "temp_chunks_dir": self.temp_chunks_dir,
            "loaded_models_count": len(self._model_cache),
            "processor_cache_size": len(self._processor_cache)
        }
    
    def _get_language_suppression_tokens(self, language: str):
        """Get tokens to suppress for language-specific transcription"""
        # Try to get suppress_tokens from app_config first
        if (self.app_config and 
            hasattr(self.app_config, 'transcription') and 
            hasattr(self.app_config.transcription, 'suppress_tokens')):
            config_tokens = self.app_config.transcription.suppress_tokens
            if config_tokens and isinstance(config_tokens, list):
                logger.info(f"Using suppress_tokens from configuration: {len(config_tokens)} tokens")
                return config_tokens
        
        # Fallback to hardcoded tokens if no configuration
        base_tokens = [-1]  # Standard special token suppression
        
        if language == "he":
            # Add English language tokens that commonly appear in Hebrew transcriptions
            # These are common Whisper token IDs for English words/patterns
            english_tokens = [
                # Common English articles and prepositions
                262, 290, 264, 286, 257, 279, 281, 294, 302, 291, 278, 259, 267, 269, 
                # Common English words that might leak into Hebrew
                300, 301, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314,
                # Language switching tokens
                50259, 50260, 50261, 50262, 50263, 50264, 50265, 50266, 50267, 50268
            ]
            logger.info(f"Using hardcoded Hebrew suppress_tokens: {len(base_tokens + english_tokens)} tokens")
            return base_tokens + english_tokens
        else:
            # For other languages, just use base suppression
            logger.info(f"Using base suppress_tokens for language '{language}': {len(base_tokens)} tokens")
            return base_tokens
    
    def _filter_language_only(self, text: str, language: str) -> str:
        """Filter text to keep only specified language characters and basic punctuation"""
        import re
        
        if language == "he":
            # Keep Hebrew characters, numbers, and basic punctuation
            hebrew_pattern = r'[^\u0590-\u05FF\u2000-\u206F\u0020-\u007F\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0E00-\u0E7F\u1B00-\u1B7F\u1CD0-\u1CFF\uA880-\uA8DF\uA900-\uA92F\uAA00-\uAA5F\u0C80-\u0CFF\u0D00-\u0D7F\u0D80-\u0DFF\u0E80-\u0EFF\u0F00-\u0FFF\u1000-\u109F\u1100-\u11FF\u1200-\u137F\u1380-\u139F\u13A0-\u13FF\u1400-\u167F\u1680-\u169F\u16A0-\u16FF\u1700-\u171F\u1720-\u173F\u1740-\u175F\u1760-\u177F\u1780-\u17FF\u1800-\u18AF\u1900-\u194F\u1950-\u197F\u1980-\u19DF\u19E0-\u19FF\u1A00-\u1A1F\u1A20-\u1AAF\u1AB0-\u1AFF\u1B00-\u1B7F\u1B80-\u1BBF\u1BC0-\u1BFF\u1C00-\u1C4F\u1C50-\u1C7F\u1C80-\u1CDF\u1CD0-\u1CFF\u1D00-\u1D7F\u1D80-\u1DBF\u1DC0-\u1DFF\u1E00-\u1E7F\u1E80-\u1EFF\u1F00-\u1FFF\u2000-\u206F\u2070-\u209F\u20A0-\u20CF\u20D0-\u20FF\u2100-\u214F\u2150-\u218F\u2190-\u21FF\u2200-\u22FF\u2300-\u23FF\u2400-\u243F\u2440-\u245F\u2460-\u24FF\u2500-\u257F\u2580-\u259F\u25A0-\u25FF\u2600-\u26FF\u2700-\u27BF\u27C0-\u27EF\u27F0-\u27FF\u2800-\u28FF\u2900-\u297F\u2980-\u29FF\u2A00-\u2AFF\u2B00-\u2BFF\u2C00-\u2C5F\u2C60-\u2C7F\u2C80-\u2CFF\u2D00-\u2D2F\u2D30-\u2D7F\u2D80-\u2DDF\u2DE0-\u2DFF\u2E00-\u2E7F\u2E80-\u2EFF\u2F00-\u2FDF\u2FF0-\u2FFF\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u3100-\u312F\u3130-\u318F\u3190-\u319F\u31A0-\u31BF\u31C0-\u31EF\u31F0-\u31FF\u3200-\u32FF\u3300-\u33FF\u3400-\u4DBF\u4DC0-\u4DFF\u4E00-\u9FFF\uA000-\uA48F\uA490-\uA4CF\uA4D0-\uA4FF\uA500-\uA63F\uA640-\uA69F\uA6A0-\uA6FF\uA700-\uA71F\uA720-\uA7FF\uA800-\uA82F\uA830-\uA83F\uA840-\uA87F\uA880-\uA8DF\uA8E0-\uA8FF\uA900-\uA92F\uA930-\uA95F\uA960-\uA97F\uA980-\uA9DF\uA9E0-\uA9FF\uAA00-\uAA5F\uAA60-\uAA7F\uAA80-\uAADF\uAAE0-\uAAFF\uAB00-\uAB2F\uAB30-\uAB6F\uAB70-\uABBF\uABC0-\uABFF\uAC00-\uD7AF\uD7B0-\uD7FF\uD800-\uDB7F\uDB80-\uDBFF\uDC00-\uDFFF\uE000-\uF8FF\uF900-\uFAFF\uFB00-\uFB4F\uFB50-\uFDFF\uFE00-\uFE0F\uFE10-\uFE1F\uFE20-\uFE2F\uFE30-\uFE4F\uFE50-\uFE6F\uFE70-\uFEFF\uFF00-\uFFEF\uFFF0-\uFFFF\u20000-\u2A6DF\u2A700-\u2B73F\u2B740-\u2B81F\u2B820-\u2CEAF\u2CEB0-\u2EBEF\u2F800-\u2FA1F\u30000-\u3134F\u31350-\u323AF\uE0000-\uE007F\uE0100-\uE01EF\uF0000-\uFFFFF\u100000-\u10FFFF0-9\s\.,!?;:()\[\]{}"\'-]'
            filtered_text = re.sub(hebrew_pattern, '', text)
        else:
            # For other languages, keep alphanumeric and basic punctuation
            filtered_text = re.sub(r'[^\w\s\.,!?;:()\[\]{}"\'-]', '', text)
        
        # Clean up extra whitespace
        filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
        
        # Remove repetitions after language filtering to fix word repetition issues
        filtered_text = self._remove_repetitions(filtered_text)
        
        return filtered_text
    
    def _remove_repetitions(self, text: str) -> str:
        """Enhanced repetition removal for Whisper output with better pattern detection"""
        import re
        
        # Remove repeated words/phrases (common in Whisper output)
        words = text.split()
        if len(words) < 3:
            return text
        
        # Enhanced repetition detection
        cleaned_words = []
        i = 0
        while i < len(words):
            if i + 2 < len(words) and words[i] == words[i + 1] == words[i + 2]:
                # Found 3+ repeated words, keep only one
                cleaned_words.append(words[i])
                i += 3
                # Skip any additional repetitions
                while i < len(words) and words[i] == words[i - 1]:
                    i += 1
            else:
                cleaned_words.append(words[i])
                i += 1
        
        # Join words back to text for additional pattern cleanup
        cleaned_text = ' '.join(cleaned_words)
        
        # Remove comma-separated repetition patterns like "word, word, word, word"
        # This handles the specific case we see in chunk_012: "מלך, מלך, מלך, מלך..."
        pattern = r'(\b\w+\b)(?:\s*,\s*\1\s*)+'
        cleaned_text = re.sub(pattern, r'\1', cleaned_text)
        
        # Remove consecutive word repetition patterns like "word word word word"
        pattern = r'(\b\w+\b)(?:\s+\1\s*)+'
        cleaned_text = re.sub(pattern, r'\1', cleaned_text)
        
        # Remove trailing commas and clean up spacing
        cleaned_text = re.sub(r'\s*,\s*$', '', cleaned_text)  # Remove trailing comma
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # Clean up spacing
        
        return cleaned_text
    
    def _validate_transcription_quality(self, text: str) -> Dict[str, Any]:
        """Validate transcription quality and detect repetition issues"""
        import re
        
        words = text.split()
        
        # Check for excessive repetition
        word_counts = {}
        for word in words:
            # Clean word for counting (remove punctuation)
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word:
                word_counts[clean_word] = word_counts.get(clean_word, 0) + 1
        
        # Calculate repetition ratio
        total_words = len(words)
        unique_words = len(word_counts)
        repetition_ratio = unique_words / total_words if total_words > 0 else 1.0
        
        # Check for suspicious patterns
        suspicious_patterns = []
        for word, count in word_counts.items():
            if count > total_words * 0.3:  # Word appears in >30% of text
                suspicious_patterns.append(f"'{word}' appears {count} times ({count/total_words*100:.1f}%)")
        
        # Check for comma-separated repetition patterns
        comma_pattern = r'(\b\w+\b)(?:\s*,\s*\1\s*)+'
        if re.search(comma_pattern, text):
            suspicious_patterns.append("Comma-separated repetition detected")
        
        # Check for consecutive repetition patterns
        consecutive_pattern = r'(\b\w+\b)(?:\s+\1\s*)+'
        if re.search(consecutive_pattern, text):
            suspicious_patterns.append("Consecutive repetition detected")
        
        quality_score = repetition_ratio * 100
        
        # Log quality issues
        if suspicious_patterns:
            logger.warning(f"⚠️ Transcription quality issues detected:")
            for pattern in suspicious_patterns:
                logger.warning(f"   - {pattern}")
            logger.warning(f"   Quality score: {quality_score:.1f}/100")
        
        return {
            'quality_score': quality_score,
            'total_words': total_words,
            'unique_words': unique_words,
            'repetition_ratio': repetition_ratio,
            'suspicious_patterns': suspicious_patterns,
            'is_acceptable': quality_score > 50 and len(suspicious_patterns) == 0
        }
    
    def _transcribe_chunk(self, audio_chunk, chunk_count: int, chunk_start: float, chunk_end: float, model_name: str) -> str:
        """Transcribe a single audio chunk using optimized whisper engine"""
        chunk_start_time = time.time()
        logger.info(f"🎯 OptimizedWhisperEngine: Starting _transcribe_chunk for {model_name}")
        
        try:
            # Get cached model
            processor, model = self._get_or_load_model(model_name)
            logger.info(f"✅ OptimizedWhisperEngine: Model loaded successfully: {type(model)}")
            
        except Exception as e:
            logger.error(f"❌ OptimizedWhisperEngine: Error in _transcribe_chunk setup: {e}")
            raise
        
        # Determine if this is a CTranslate2 model
        is_ct2_model = hasattr(model, 'generate')
        
        if is_ct2_model:
            # This is a CTranslate2 model
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using CTranslate2 generation...")
            
            try:
                # Process audio features for CTranslate2
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Processing audio features...")
                features_start = time.time()
                
                # Get features as numpy array and convert to CTranslate2 StorageView
                import ctranslate2
                features = processor(audio_chunk, sampling_rate=16000, return_tensors="np").input_features
                features = features.astype("float32")  # Ensure correct data type
                
                # Convert to CTranslate2 StorageView
                features = ctranslate2.StorageView.from_array(features)
                
                features_time = time.time() - features_start
                logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Features processed in {features_time:.2f}s")
                
                # Generate token ids with CTranslate2
                logger.info(f"🎯 CHUNK {chunk_count} PROGRESS: Starting CTranslate2 generation...")
                generation_start = time.time()
                
                # Get language and configuration
                language = self.config.language if hasattr(self.config, 'language') else "he"
                prompts = None
                try:
                    # CTranslate2 expects prompts as list of token IDs
                    decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
                    if decoder_ids:
                        # Extract just the token IDs from the tuples
                        prompt_token_ids = [token_id for _, token_id in decoder_ids]
                        
                        # Add start token if not present (CTranslate2 requirement)
                        start_token = processor.tokenizer.encode("<|startoftranscript|>", add_special_tokens=False)
                        if start_token and start_token[0] not in prompt_token_ids:
                            prompt_token_ids = start_token + prompt_token_ids
                        
                        prompts = [prompt_token_ids]  # Wrap in list for CTranslate2
                    logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Decoder prompt IDs configured for language '{language}'")
                except Exception:
                    prompts = None
                    logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using default decoder prompt IDs")
                
                # Get suppression tokens
                suppress_tokens = self._get_language_suppression_tokens(language)
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using {len(suppress_tokens)} suppression tokens")
                
                # Generate with CTranslate2 - using correct parameter names
                generation_result = model.generate(
                    features,
                    prompts=prompts,
                    suppress_tokens=suppress_tokens,
                    beam_size=5,
                    max_length=448,  # CTranslate2 default max length
                    suppress_blank=True
                )
                
                generation_time = time.time() - generation_start
                logger.info(f"✅ CHUNK {chunk_count} PROGRESS: CTranslate2 generation completed in {generation_time:.2f}s")
                
                # Decode tokens from CTranslate2 result
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Decoding CTranslate2 tokens...")
                decode_start = time.time()
                

                # CTranslate2 can return different result types
                if hasattr(generation_result, 'sequences'):
                    # WhisperGenerationResult object
                    sequences = generation_result.sequences
                    if isinstance(sequences, list) and len(sequences) > 0:
                        chunk_transcription = processor.batch_decode(sequences, skip_special_tokens=True)[0]
                        logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Tokens decoded successfully (sequences)")
                    else:
                        raise ValueError("No sequences found in CTranslate2 result")
                elif isinstance(generation_result, list):
                    # Direct list of sequences
                    if len(generation_result) > 0 and generation_result[0] is not None:
                        # Check if the list contains WhisperGenerationResult objects
                        if hasattr(generation_result[0], 'sequences_ids') and generation_result[0].sequences_ids is not None:
                            # Use sequences_ids (integer token IDs) instead of sequences (string tokens)
                            sequences_ids = [item.sequences_ids for item in generation_result if item is not None and hasattr(item, 'sequences_ids') and item.sequences_ids is not None]
                            if sequences_ids:
                                chunk_transcription = processor.batch_decode(sequences_ids[0], skip_special_tokens=True)[0]
                            else:
                                raise ValueError("No valid sequences_ids found in CTranslate2 result")
                        else:
                            # Fallback to direct decoding
                            chunk_transcription = processor.batch_decode(generation_result, skip_special_tokens=True)[0]
                        
                        logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Tokens decoded successfully (direct list)")
                    else:
                        raise ValueError("Empty or invalid sequence list from CTranslate2")
                else:
                    # Fallback: try to handle as raw result
                    logger.warning(f"⚠️ Unexpected CTranslate2 result type: {type(generation_result)}")
                    raise ValueError(f"Unexpected result type: {type(generation_result)}")
                
                decode_time = time.time() - decode_start
                logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Tokens decoded in {decode_time:.2f}s")
                
            except Exception as fallback_error:
                logger.error(f"❌ CHUNK {chunk_count} PROGRESS: All CTranslate2 approaches failed: {fallback_error}")
                raise
            
            # Apply language-specific post-processing for CTranslate2 path
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Applying language filtering...")
            post_process_start = time.time()
            chunk_transcription = self._filter_language_only(chunk_transcription, language)
            post_process_time = time.time() - post_process_start
            logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Language filtering completed in {post_process_time:.2f}s")
            
            # Validate transcription quality and log any issues
            quality_info = self._validate_transcription_quality(chunk_transcription)
            if not quality_info['is_acceptable']:
                logger.warning(f"⚠️ CHUNK {chunk_count}: Low quality transcription detected (score: {quality_info['quality_score']:.1f})")
        
        else:
            # This is a transformers model (fallback)
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using transformers fallback generation...")
            
            import torch
            
            # Transcribe with transformers
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Processing audio features...")
            features_start = time.time()
            features = processor(audio_chunk, sampling_rate=16000, return_tensors="pt").input_features
            features = features.float()  # Ensure correct data type
            features_time = time.time() - features_start
            logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Features processed in {features_time:.2f}s")
            
            # Generate token ids with simplified parameters
            language = self.config.language if hasattr(self.config, 'language') else "he"
            forced_decoder_ids = None
            try:
                forced_decoder_ids = processor.get_decoder_prompt_ids(language=language, task="transcribe")
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Decoder prompt IDs configured for language '{language}'")
            except Exception:
                forced_decoder_ids = None
                logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using default decoder prompt IDs")
            
            # Get suppression tokens for language-specific transcription
            suppress_tokens = self._get_language_suppression_tokens(language)
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Using {len(suppress_tokens)} suppression tokens")
            
            logger.info(f"🎯 CHUNK {chunk_count} PROGRESS: Starting model generation...")
            generation_start = time.time()
            
            with torch.no_grad():  # Disable gradient computation to save memory
                predicted_ids = model.generate(
                    features, 
                    forced_decoder_ids=forced_decoder_ids,
                    suppress_tokens=suppress_tokens,
                    num_beams=5,                     # Reduced beam size for stability
                    temperature=0.0,                 # Deterministic output
                    do_sample=False,                 # Don't use sampling
                    max_new_tokens=400               # Token limit
                )
            
            generation_time = time.time() - generation_start
            logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Model generation completed in {generation_time:.2f}s")
            
            # Decode the token ids to text
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Decoding tokens to text...")
            decode_start = time.time()
            chunk_transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            decode_time = time.time() - decode_start
            logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Tokens decoded in {decode_time:.2f}s")
            
            # Apply language-specific post-processing for transformers fallback path
            logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Applying language filtering...")
            post_process_start = time.time()
            chunk_transcription = self._filter_language_only(chunk_transcription, language)
            post_process_time = time.time() - post_process_start
            logger.info(f"✅ CHUNK {chunk_count} PROGRESS: Language filtering completed in {post_process_time:.2f}s")
            
            # Validate transcription quality and log any issues
            quality_info = self._validate_transcription_quality(chunk_transcription)
            if not quality_info['is_acceptable']:
                logger.warning(f"⚠️ CHUNK {chunk_count}: Low quality transcription detected (score: {quality_info['quality_score']:.1f})")
        
        # Final processing and logging
        total_chunk_time = time.time() - chunk_start_time
        
        # Check if the transcription contains error messages
        if chunk_transcription and "ERROR:" in chunk_transcription:
            logger.error(f"❌ CHUNK {chunk_count} PROGRESS: Transcription contains error messages: {chunk_transcription}")
            raise ValueError(f"Transcription failed with error: {chunk_transcription}")
        
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Transcription completed!")
        logger.info(f"   📊 Total time: {total_chunk_time:.2f}s")
        logger.info(f"   📊 Text length: {len(chunk_transcription)} characters")
        logger.info(f"   📊 Words (estimated): {len(chunk_transcription.split())}")
        logger.info(f"   📊 Processing speed: {len(chunk_transcription) / total_chunk_time:.1f} chars/sec")
        
        # Get constants from configuration
        constants = self.app_config.system.constants if self.app_config and self.app_config.system else None
        preview_length = constants.chunk_preview_length if constants else 100
        
        logger.info(f"📊 CHUNK {chunk_count} PROGRESS: Transcription preview: {chunk_transcription[:preview_length]}...")
        
        return chunk_transcription
    
    def transcribe(self, audio_file_path: str, model_name: str):
        """Transcribe using the parent class logic to detect existing chunks first."""
        import os
        
        # Check if we have existing audio chunks first
        chunks_dir = "examples/audio/voice/audio_chunks/"
        if os.path.exists(chunks_dir):
            chunk_files = [f for f in os.listdir(chunks_dir) if f.startswith("audio_chunk_") and f.endswith(".wav")]
            if chunk_files:
                logger.info(f"🎯 Found {len(chunk_files)} existing audio chunks, processing them directly")
                return self._process_existing_audio_chunks(audio_file_path, model_name)
        
        # If no existing chunks, check file size and use appropriate method
        if os.path.exists(audio_file_path):
            file_size = os.path.getsize(audio_file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > 100:  # Files larger than 100MB
                logger.info(f"📁 Large file detected ({file_size_mb:.1f}MB), using audio chunk processing")
                return self._transcribe_with_audio_chunks(audio_file_path, model_name, 120)
            else:
                logger.info(f"📁 Small file detected ({file_size_mb:.1f}MB), processing directly")
                # For small files, we need to load the audio first
                try:
                    import librosa
                    audio_data, sample_rate = librosa.load(audio_file_path, sr=16000, mono=True)
                    return self._transcribe_directly(audio_file_path, model_name, audio_data, sample_rate)
                except Exception as e:
                    logger.error(f"❌ Error loading audio for direct processing: {e}")
                    # Fallback to chunk processing
                    return self._transcribe_with_audio_chunks(audio_file_path, model_name, 120)
        else:
            logger.error(f"❌ Audio file not found: {audio_file_path}")
            # Return a failed result instead of None
            from src.models.transcription_models import TranscriptionResult
            return TranscriptionResult(
                success=False,
                speakers={},
                full_text="",
                transcription_time=0.0,
                model_name=model_name,
                audio_file=audio_file_path,
                speaker_count=0,
                error_message="Audio file not found"
            )
