#!/usr/bin/env python3
"""
Configuration Manager for ivrit-ai voice transcription service
Simplified and focused on core configuration management
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

from src.models import (
    Environment,
    TranscriptionConfig,
    SpeakerConfig,
    BatchConfig,
    DockerConfig,
    RunPodConfig,
    OutputConfig,
    SystemConfig,
    InputConfig,
    AppConfig
)


class ConfigLoader:
    """Handles loading and merging configuration files"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
    
    def load_config(self, environment: Environment) -> AppConfig:
        """Load and merge configuration for given environment"""
        # Load base config
        base_config = self._load_json_file("environments/base.json")
        
        # Load environment-specific config
        env_config = self._load_json_file(f"environments/{environment.value}.json")
        
        # Merge configurations
        merged = self._merge_configs(base_config, env_config)
        
        # Apply environment variable overrides
        merged = self._apply_env_overrides(merged)
        
        # Convert to AppConfig
        return self._create_app_config(merged, environment)
    
    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load JSON file safely"""
        file_path = self.config_dir / filename
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {filename}: {e}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
        """Simple deep merge of configurations"""
        result = base.copy()
        
        for key, value in env.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Transcription overrides
        if 'transcription' in config:
            config['transcription']['default_model'] = os.getenv('DEFAULT_MODEL', 
                config['transcription'].get('default_model', 'ivrit-ai/whisper-large-v3'))
            config['transcription']['fallback_model'] = os.getenv('FALLBACK_MODEL', 
                config['transcription'].get('fallback_model', 'ivrit-ai/whisper-large-v3-turbo'))
            # Set default values for transcription
            config['transcription']['default_model'] = (
                config['transcription'].get('default_model', 'ivrit-ai/whisper-large-v3'))
            config['transcription']['default_engine'] = (
                config['transcription'].get('default_engine', 'custom-whisper'))
        
        # RunPod overrides
        if 'runpod' in config:
            config['runpod']['api_key'] = os.getenv('RUNPOD_API_KEY', config['runpod'].get('api_key'))
            config['runpod']['endpoint_id'] = os.getenv('RUNPOD_ENDPOINT_ID', config['runpod'].get('endpoint_id'))
        
        # System overrides
        if 'system' in config:
            debug_env = os.getenv('DEBUG')
            if debug_env is not None:
                config['system']['debug'] = debug_env.lower() in ('true', '1', 'yes', 'on')
            dev_mode_env = os.getenv('DEV_MODE')
            if dev_mode_env is not None:
                config['system']['dev_mode'] = dev_mode_env.lower() in ('true', '1', 'yes', 'on')
            config['system']['hugging_face_token'] = os.getenv('HUGGING_FACE_TOKEN', 
                config['system'].get('hugging_face_token'))
        
        return config
    
    def _create_app_config(self, config_dict: Dict[str, Any], environment: Environment) -> AppConfig:
        """Create AppConfig from dictionary"""
        try:
            return AppConfig(
                environment=environment,
                transcription=TranscriptionConfig(**config_dict.get('transcription', {})) if config_dict.get('transcription') else None,
                speaker=SpeakerConfig(**config_dict.get('speaker', {})) if config_dict.get('speaker') else None,
                batch=BatchConfig(**config_dict.get('batch', {})) if config_dict.get('batch') else None,
                docker=DockerConfig(**config_dict.get('docker', {})) if config_dict.get('docker') else None,
                runpod=RunPodConfig(**config_dict.get('runpod', {})) if config_dict.get('runpod') else None,
                output=OutputConfig(**config_dict.get('output', {})) if config_dict.get('output') else None,
                system=SystemConfig(**config_dict.get('system', {})) if config_dict.get('system') else None,
                input=InputConfig(**config_dict.get('input', {})) if config_dict.get('input') else None
            )
        except Exception as e:
            logger.error(f"Error creating configuration: {e}")
            return AppConfig(environment=environment)


class ConfigValidator:
    """Handles configuration validation"""
    
    @staticmethod
    def validate(config: AppConfig) -> bool:
        """Validate configuration with comprehensive checks"""
        try:
            # Pydantic validation
            config.model_validate(config.model_dump())
            
            # Business logic validation
            errors = []
            
            # Check required environment variables
            missing_vars = ConfigValidator._check_required_env_vars(config)
            if missing_vars:
                errors.extend(missing_vars)
            
            # Check file paths and directories
            path_errors = ConfigValidator._validate_paths(config)
            if path_errors:
                errors.extend(path_errors)
            
            # Check configuration consistency
            consistency_errors = ConfigValidator._check_consistency(config)
            if consistency_errors:
                errors.extend(consistency_errors)
            
            # Check model and engine compatibility
            compatibility_errors = ConfigValidator._check_model_engine_compatibility(config)
            if compatibility_errors:
                errors.extend(compatibility_errors)
            
            if errors:
                logger.error("Configuration validation failed:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    @staticmethod
    def _check_required_env_vars(config: AppConfig) -> List[str]:
        """Check for required environment variables"""
        errors = []
        
        if config.runpod and config.runpod.enabled:
            if not config.runpod.api_key:
                errors.append('RUNPOD_API_KEY is required when RunPod is enabled')
            if not config.runpod.endpoint_id:
                errors.append('RUNPOD_ENDPOINT_ID is required when RunPod is enabled')
        
        if config.system and config.system.hugging_face_token:
            # Validate HF token format (basic check)
            if len(config.system.hugging_face_token) < 10:
                errors.append('HUGGING_FACE_TOKEN appears to be invalid (too short)')
        
        return errors
    
    @staticmethod
    def _validate_paths(config: AppConfig) -> List[str]:
        """Validate file paths and directories"""
        errors = []
        
        # Check output directory
        if config.output and config.output.output_dir:
            output_path = Path(config.output.output_dir)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                # Test write permissions
                test_file = output_path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                errors.append(f'Output directory {config.output.output_dir} is not writable: {e}')
        
        # Check logs directory
        if config.output and config.output.logs_dir:
            logs_path = Path(config.output.logs_dir)
            try:
                logs_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f'Logs directory {config.output.logs_dir} cannot be created: {e}')
        
        # Check input directory if specified
        if config.input and config.input.directory:
            input_path = Path(config.input.directory)
            if not input_path.exists():
                errors.append(f'Input directory {config.input.directory} does not exist')
            elif not input_path.is_dir():
                errors.append(f'Input path {config.input.directory} is not a directory')
        
        return errors
    
    @staticmethod
    def _check_consistency(config: AppConfig) -> List[str]:
        """Check configuration consistency"""
        errors = []
        
        # Check speaker configuration
        if config.speaker:
            if config.speaker.min_speakers > config.speaker.max_speakers:
                errors.append('min_speakers cannot be greater than max_speakers')
            
            if config.speaker.min_speakers < 1:
                errors.append('min_speakers must be at least 1')
            
            if config.speaker.max_speakers > 10:
                errors.append('max_speakers should not exceed 10 for performance reasons')
        
        # Check batch configuration
        if config.batch and config.batch.enabled:
            if config.batch.max_workers < 1:
                errors.append('max_workers must be at least 1')
            elif config.batch.max_workers > 16:
                errors.append('max_workers should not exceed 16 for memory management')
            
            if config.batch.timeout_per_file < 30:
                errors.append('timeout_per_file should be at least 30 seconds')
        
        # Check system configuration
        if config.system:
            if config.system.timeout_seconds < 10:
                errors.append('timeout_seconds should be at least 10 seconds')
            
            if config.system.retry_attempts < 0:
                errors.append('retry_attempts cannot be negative')
            elif config.system.retry_attempts > 10:
                errors.append('retry_attempts should not exceed 10')
        
        return errors
    
    @staticmethod
    def _check_model_engine_compatibility(config: AppConfig) -> List[str]:
        """Check model and engine compatibility"""
        errors = []
        
        if config.transcription:
            # Define compatible model-engine combinations
            stable_whisper_models = {
                'tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small',
                'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large',
                'large-v3-turbo', 'turbo'
            }
            
            custom_whisper_models = {
                'ivrit-ai/whisper-large-v3', 'ivrit-ai/whisper-large-v3-turbo'
            }
            
            model = config.transcription.default_model
            engine = config.transcription.default_engine
            
            if engine == 'stable-whisper' and model in custom_whisper_models:
                errors.append(f'Model {model} requires custom-whisper engine, not stable-whisper')
            elif engine == 'custom-whisper' and model in stable_whisper_models:
                errors.append(f'Model {model} should use stable-whisper engine for better performance')
        
        return errors


class ConfigPrinter:
    """Handles configuration display"""
    
    @staticmethod
    def print_config(config: AppConfig, show_sensitive: bool = False):
        """Print configuration in a readable format"""
        logger.info(f"Configuration ({config.environment.value}):")
        logger.info("=" * 50)
        
        sections = [
            ('🎤 Transcription', config.transcription, [
                ('Default Model', 'default_model'),
                ('Fallback Model', 'fallback_model'),
                ('Default Engine', 'default_engine'),
                ('Beam Size', 'beam_size'),
                ('Language', 'language')
            ]),
            ('👥 Speaker Diarization', config.speaker, [
                ('Min Speakers', 'min_speakers'),
                ('Max Speakers', 'max_speakers'),
                ('Silence Threshold', 'silence_threshold', lambda x: f"{x}s"),
                ('Beam Size', 'beam_size')
            ]),
            ('☁️  RunPod', config.runpod, [
                ('API Key', 'api_key', lambda x: '✅ Set' if x else '❌ Not set'),
                ('Endpoint ID', 'endpoint_id', lambda x: '✅ Set' if x else '❌ Not set'),
                ('Enabled', 'enabled'),
                ('Serverless Mode', 'serverless_mode')
            ]),
            ('📁 Output', config.output, [
                ('Output Directory', 'output_dir'),
                ('Logs Directory', 'logs_dir'),
                ('Save JSON', 'save_json'),
                ('Save TXT', 'save_txt'),
                ('Save DOCX', 'save_docx')
            ]),
            ('⚙️  System', config.system, [
                ('Debug Mode', 'debug'),
                ('Dev Mode', 'dev_mode'),
                ('Timeout', 'timeout_seconds', lambda x: f"{x}s"),
                ('Retry Attempts', 'retry_attempts')
            ]),
            ('📂 Input', config.input, [
                ('Directory', 'directory'),
                ('Recursive Search', 'recursive_search'),
                ('Max File Size', 'max_file_size_mb', lambda x: f"{x}MB"),
                ('Supported Formats', 'supported_formats', lambda x: ', '.join(x) if x else 'None')
            ]),
            ('🔄 Batch Processing', config.batch, [
                ('Enabled', 'enabled'),
                ('Parallel Processing', 'parallel_processing'),
                ('Max Workers', 'max_workers'),
                ('Timeout Per File', 'timeout_per_file', lambda x: f"{x}s")
            ]),
            ('🐳 Docker', config.docker, [
                ('Enabled', 'enabled'),
                ('Image', 'image_name', lambda x: f"{x}:{config.docker.tag}" if config.docker else None),
                ('Memory Limit', 'memory_limit'),
                ('CPU Limit', 'cpu_limit')
            ])
        ]
        
        for title, section, fields in sections:
            if section:
                logger.info(f"\n{title}:")
                for field_name, attr_name, *formatters in fields:
                    value = getattr(section, attr_name, None)
                    if len(formatters) > 0 and formatters[0]:
                        value = formatters[0](value)
                    logger.info(f"   {field_name}: {value}")
                    
                    # Handle sensitive data
                    if show_sensitive and attr_name == 'api_key' and value == '✅ Set':
                        api_key = getattr(section, attr_name, '')
                        if api_key:
                            logger.info(f"   API Key: {api_key[:10]}...")


class ConfigManager:
    """Configuration manager supporting dependency injection"""
    
    def __init__(self, config_dir: str = "config", environment: Optional[Environment] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
            environment: Optional environment override (defaults to ENVIRONMENT env var)
        """
        self.config_dir = Path(config_dir)
        self.config_path = str(self.config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Load environment variables
        self._load_env_file()
        
        # Determine environment
        self.environment = environment or self._determine_environment()
        
        # Load configuration
        loader = ConfigLoader(self.config_dir)
        self.config = loader.load_config(self.environment)
    
    def _load_env_file(self):
        """Load .env file if it exists"""
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.split('#')[0].strip()
                        os.environ[key.strip()] = value
    
    def _determine_environment(self) -> Environment:
        """Determine current environment"""
        env_var = os.getenv('ENVIRONMENT', '').lower()
        if env_var == 'production':
            return Environment.PRODUCTION
        elif env_var == 'development':
            return Environment.DEVELOPMENT
        else:
            return Environment.BASE
    
    def validate(self) -> bool:
        """Validate configuration"""
        return ConfigValidator.validate(self.config)
    
    def print_config(self, show_sensitive: bool = False):
        """Print configuration"""
        ConfigPrinter.print_config(self.config, show_sensitive)
    
    def save_config(self, filename: Optional[str] = None):
        """Save configuration to file"""
        if filename is None:
            filename = f"config_{self.environment.value}.json"
        
        config_file = self.config_dir / filename
        
        try:
            config_dict = self.config.model_dump(exclude_none=True)
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_speaker_config(self, preset: str = "default"):
        """Get speaker configuration for specific preset"""
        from src.core.speaker_config_factory import SpeakerConfigFactory
        return SpeakerConfigFactory.get_config(preset) 