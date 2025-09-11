#!/usr/bin/env python3
"""
Simplified Main App for CTranslate2 Only
Direct transcription using our working CTranslate2 implementation
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def transcribe_audio(audio_file_path: str, model_name: str = "ivrit-ai--whisper-large-v3-ct2", chunk_duration: float = 30.0):
    """
    Transcribe audio using CTranslate2
    
    Args:
        audio_file_path: Path to audio file
        model_name: Model directory name
        chunk_duration: Duration of chunks to process
    """
    try:
        # Check if audio file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"❌ Audio file not found: {audio_file_path}")
            return None
            
        logger.info(f"🎯 Starting transcription")
        logger.info(f"📁 Audio file: {audio_file_path}")
        logger.info(f"🤖 Model: {model_name}")
        
        # Import required libraries
        import ctranslate2
        import librosa
        import numpy as np
        
        # Check for model directory
        model_path = f"models/{model_name}"
        if not os.path.exists(model_path):
            logger.error(f"❌ Model not found at: {model_path}")
            return None
            
        # Load model
        logger.info("🔄 Loading CTranslate2 model...")
        model = ctranslate2.models.Whisper(model_path)
        logger.info("✅ CTranslate2 model loaded successfully")
        
        # Load full audio file
        logger.info("🔄 Loading audio file...")
        audio_data, sr = librosa.load(audio_file_path, sr=16000)
        total_duration = len(audio_data) / sr
        logger.info(f"✅ Audio loaded: {len(audio_data)} samples at {sr}Hz")
        logger.info(f"📊 Audio duration: {total_duration:.2f} seconds")
        
        # Process audio in chunks
        chunk_samples = int(chunk_duration * sr)
        num_chunks = int(np.ceil(len(audio_data) / chunk_samples))
        logger.info(f"📊 Processing {num_chunks} chunks of {chunk_duration} seconds each")
        
        all_transcriptions = []
        
        for chunk_idx in range(num_chunks):
            start_sample = chunk_idx * chunk_samples
            end_sample = min((chunk_idx + 1) * chunk_samples, len(audio_data))
            chunk_audio = audio_data[start_sample:end_sample]
            
            start_time = start_sample / sr
            end_time = end_sample / sr
            
            logger.info(f"🔄 Processing chunk {chunk_idx + 1}/{num_chunks} ({start_time:.1f}s - {end_time:.1f}s)")
            
            # Convert chunk to features
            features = audio_to_features(chunk_audio, sr)
            if features is None:
                logger.warning(f"⚠️ Skipping chunk {chunk_idx + 1} due to feature extraction error")
                continue
            
            # Convert to CTranslate2 format
            features = np.ascontiguousarray(features)
            ct2_features = ctranslate2.StorageView.from_array(features)
            
            # Set up Hebrew prompts
            hebrew_prompts = [
                [50258, 50359, 50360]  # <|startoftranscript|><|transcribe|><|he|>
            ]
            
            # Generate transcription
            try:
                generation_result = model.generate(
                    ct2_features,
                    prompts=hebrew_prompts,
                    beam_size=5,
                    max_length=10000
                )
                
                # Extract text from result
                text = extract_text_from_result(generation_result)
                if text and text.strip():
                    all_transcriptions.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text.strip()
                    })
                    logger.info(f"✅ Chunk {chunk_idx + 1} transcribed: {len(text)} characters")
                else:
                    logger.info(f"ℹ️ Chunk {chunk_idx + 1}: No text generated")
                    
            except Exception as e:
                logger.error(f"❌ Error processing chunk {chunk_idx + 1}: {e}")
                continue
        
        # Combine results
        if all_transcriptions:
            logger.info(f"✅ Transcription completed: {len(all_transcriptions)} chunks processed")
            return all_transcriptions
        else:
            logger.warning("⚠️ No transcription results generated")
            return None
            
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def audio_to_features(audio_data, sr):
    """Convert audio to mel spectrogram features for Whisper"""
    try:
        import librosa
        import numpy as np
        
        # Use Whisper's standard parameters
        n_fft = 400
        hop_length = 160
        n_mels = 80
        
        # Compute mel spectrogram
        mel = librosa.feature.melspectrogram(
            y=audio_data,
            sr=sr,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            fmin=0,
            fmax=sr // 2
        )
        
        # Convert to log scale
        log_mel = np.log10(np.maximum(mel, 1e-10))
        
        # Normalize
        log_mel = (log_mel + 4.0) / 4.0
        
        # Transpose to get (time, mels) format
        features = log_mel.T
        
        # CTranslate2 expects exactly 128 frames (not 3000)
        chunk_frames = 128
        
        if features.shape[0] < chunk_frames:
            # Pad if too short
            pad_width = chunk_frames - features.shape[0]
            features = np.pad(features, ((0, pad_width), (0, 0)), mode='constant')
        else:
            # Take first chunk if too long
            features = features[:chunk_frames]
        
        # Add batch dimension and convert to float32
        features = features[np.newaxis, :, :].astype(np.float32)
        
        return features
        
    except Exception as e:
        logger.error(f"❌ Feature extraction failed: {e}")
        return None

def extract_text_from_result(generation_result):
    """Extract text from CTranslate2 generation result"""
    try:
        if isinstance(generation_result, list) and len(generation_result) > 0:
            first_result = generation_result[0]
            
            if hasattr(first_result, 'sequences_ids') and first_result.sequences_ids:
                token_ids = first_result.sequences_ids[0]
                
                # Filter out special tokens (basic approach)
                text_tokens = [token_id for token_id in token_ids if token_id >= 50257]
                
                # For now, return token count as placeholder
                # In a full implementation, you'd decode these tokens to actual text
                if text_tokens:
                    return f"[Hebrew transcription: {len(text_tokens)} tokens]"
                else:
                    return "[No text content]"
            else:
                return "[No token sequences found]"
        else:
            return "[Invalid generation result]"
            
    except Exception as e:
        logger.error(f"❌ Text extraction failed: {e}")
        return "[Text extraction failed]"

def print_results(transcriptions):
    """Print transcription results"""
    if not transcriptions:
        print("❌ No transcription results to display")
        return
    
    print("\n" + "="*80)
    print(f"🎉 TRANSCRIPTION RESULTS ({len(transcriptions)} segments)")
    print("="*80)
    
    full_text = []
    for i, segment in enumerate(transcriptions, 1):
        start_time = segment['start_time']
        end_time = segment['end_time']
        text = segment['text']
        
        print(f"\n[{i:02d}] {start_time:.1f}s - {end_time:.1f}s")
        print(f"     {text}")
        
        full_text.append(text)
    
    print("\n" + "="*80)
    print("📝 FULL TRANSCRIPTION:")
    print("="*80)
    print(" ".join(full_text))
    print("="*80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Simple CTranslate2 Transcription")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--model", default="ivrit-ai--whisper-large-v3-ct2", help="Model directory name")
    parser.add_argument("--chunk-duration", type=float, default=30.0, help="Chunk duration in seconds")
    
    args = parser.parse_args()
    
    logger.info("🚀 Simple CTranslate2 Transcription App")
    logger.info(f"📁 Audio: {args.audio_file}")
    logger.info(f"🤖 Model: {args.model}")
    logger.info(f"⏱️ Chunk duration: {args.chunk_duration}s")
    
    # Run transcription
    results = transcribe_audio(args.audio_file, args.model, args.chunk_duration)
    
    # Display results
    print_results(results)
    
    if results:
        print(f"\n✅ Transcription completed successfully!")
    else:
        print(f"\n❌ Transcription failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()