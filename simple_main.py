#!/usr/bin/env python3
"""
Simple Main App - Hebrew Voice-to-Text Transcription
Entry point for testing the basic flow
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_environment():
    """Verify that the environment is properly set up"""
    logger.info("🔍 Verifying environment setup...")
    
    # Check Python version
    python_version = sys.version_info
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check virtual environment
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    logger.info(f"Virtual environment active: {venv_active}")
    
    # Check key directories
    directories = {
        'models': 'models',
        'config': 'config', 
        'output': 'output',
        'examples': 'examples',
        'src': 'src'
    }
    
    for name, path in directories.items():
        full_path = project_root / path
        exists = full_path.exists()
        logger.info(f"Directory {name}: {'✅' if exists else '❌'} {full_path}")
    
    # Check model availability
    model_path = project_root / 'models' / 'ivrit-ai--whisper-large-v3-ct2'
    model_exists = model_path.exists()
    logger.info(f"Hebrew model: {'✅' if model_exists else '❌'} {model_path}")
    
    return venv_active and model_exists

def test_basic_imports():
    """Test basic imports to verify dependencies"""
    logger.info("🔍 Testing basic imports...")
    
    try:
        import ctranslate2
        logger.info("✅ ctranslate2 imported successfully")
    except ImportError as e:
        logger.error(f"❌ ctranslate2 import failed: {e}")
        return False
    
    try:
        import torch
        logger.info("✅ torch imported successfully")
    except ImportError as e:
        logger.error(f"❌ torch import failed: {e}")
        return False
        
    try:
        import librosa
        logger.info("✅ librosa imported successfully")
    except ImportError as e:
        logger.error(f"❌ librosa import failed: {e}")
        return False
    
    return True

def test_model_loading():
    """Test loading the Hebrew CTranslate2 model"""
    logger.info("🔍 Testing model loading...")
    
    try:
        import ctranslate2
        
        model_path = project_root / 'models' / 'ivrit-ai--whisper-large-v3-ct2'
        if not model_path.exists():
            logger.error(f"❌ Model path does not exist: {model_path}")
            return False
        
        # Try to load the model
        model = ctranslate2.models.Whisper(str(model_path))
        logger.info("✅ Hebrew CTranslate2 model loaded successfully")
        
        # Get model info
        logger.info(f"Model device: {model.device}")
        logger.info(f"Model compute type: {model.compute_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    logger.info("🔍 Testing configuration loading...")
    
    try:
        # Check if production config exists
        config_path = project_root / 'config' / 'environments' / 'production.json'
        if not config_path.exists():
            logger.error(f"❌ Production config does not exist: {config_path}")
            return False
        
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.info("✅ Production configuration loaded successfully")
        
        # Verify key configuration sections
        required_sections = ['transcription', 'output', 'processing']
        for section in required_sections:
            if section in config:
                logger.info(f"✅ Configuration section '{section}' found")
            else:
                logger.warning(f"⚠️ Configuration section '{section}' missing")
        
        # Check model configuration
        if 'transcription' in config and 'default_model' in config['transcription']:
            model = config['transcription']['default_model']
            logger.info(f"✅ Default model: {model}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration loading failed: {e}")
        return False

def verify_flow():
    """Verify the complete application flow"""
    logger.info("🚀 Starting Hebrew Voice-to-Text Application Flow Verification")
    logger.info("=" * 60)
    
    # Step 1: Environment verification
    logger.info("📋 Step 1: Environment Verification")
    env_ok = verify_environment()
    if not env_ok:
        logger.error("❌ Environment verification failed")
        return False
    logger.info("✅ Environment verification passed")
    
    # Step 2: Dependency imports
    logger.info("\n📋 Step 2: Dependency Verification") 
    imports_ok = test_basic_imports()
    if not imports_ok:
        logger.error("❌ Import verification failed")
        return False
    logger.info("✅ Import verification passed")
    
    # Step 3: Configuration loading
    logger.info("\n📋 Step 3: Configuration Verification")
    config_ok = test_configuration()
    if not config_ok:
        logger.error("❌ Configuration verification failed")  
        return False
    logger.info("✅ Configuration verification passed")
    
    # Step 4: Model loading
    logger.info("\n📋 Step 4: Model Loading Verification")
    model_ok = test_model_loading()
    if not model_ok:
        logger.error("❌ Model loading verification failed")
        return False
    logger.info("✅ Model loading verification passed")
    
    logger.info("\n🎉 SUCCESS: All verification steps passed!")
    logger.info("📝 System is ready for Hebrew voice-to-text transcription")
    
    return True

def main():
    """Main entry point"""
    try:
        success = verify_flow()
        if success:
            logger.info("\n✅ Application flow verification completed successfully")
            logger.info("🎯 Ready to process Hebrew audio files")
            return 0
        else:
            logger.error("\n❌ Application flow verification failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Unexpected error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)