#!/usr/bin/env python3
"""
Configuration Manager for ivrit-ai voice transcription service
Simplified and focused on core configuration management
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

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
            print(f"⚠️  Warning: Could not load {filename}: {e}")
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
                config['transcription'].get('default_model', 'ivrit-ai/whisper-large-v3-turbo-ct2'))
            config['transcription']['fallback_model'] = os.getenv('FALLBACK_MODEL', 
                config['transcription'].get('fallback_model', 'ivrit-ai/whisper-large-v3-ct2'))
            config['transcription']['default_engine'] = os.getenv('DEFAULT_ENGINE', 
                config['transcription'].get('default_engine', 'faster-whisper'))
        
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
            print(f"❌ Error creating configuration: {e}")
            return AppConfig(environment=environment)


class ConfigValidator:
    """Handles configuration validation"""
    
    @staticmethod
    def validate(config: AppConfig) -> bool:
        """Validate configuration"""
        try:
            # Pydantic validation
            config.model_validate(config.model_dump())
            
            # Business logic validation
            missing_vars = []
            
            if config.runpod and not config.runpod.api_key:
                missing_vars.append('RUNPOD_API_KEY')
            if config.runpod and not config.runpod.endpoint_id:
                missing_vars.append('RUNPOD_ENDPOINT_ID')
            
            if missing_vars:
                print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False


class ConfigPrinter:
    """Handles configuration display"""
    
    @staticmethod
    def print_config(config: AppConfig, show_sensitive: bool = False):
        """Print configuration in a readable format"""
        print(f"🔧 Configuration ({config.environment.value}):")
        print("=" * 50)
        
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
                print(f"\n{title}:")
                for field_name, attr_name, *formatters in fields:
                    value = getattr(section, attr_name, None)
                    if len(formatters) > 0 and formatters[0]:
                        value = formatters[0](value)
                    print(f"   {field_name}: {value}")
                    
                    # Handle sensitive data
                    if show_sensitive and attr_name == 'api_key' and value == '✅ Set':
                        api_key = getattr(section, attr_name, '')
                        if api_key:
                            print(f"   API Key: {api_key[:10]}...")


class ConfigManager:
    """Simplified configuration manager"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Load environment variables
        self._load_env_file()
        
        # Determine environment
        self.environment = self._determine_environment()
        
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
            filename = f"config_{self.config.environment.value}.json"
        
        config_file = self.config_dir / filename
        
        try:
            config_dict = self.config.model_dump(exclude_none=True)
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            print(f"✅ Configuration saved to {config_file}")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    def get_speaker_config(self, preset: str = "default"):
        """Get speaker configuration for specific preset"""
        from src.core.speaker_config_factory import SpeakerConfigFactory
        return SpeakerConfigFactory.get_config(preset)


# Simple singleton pattern
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get current configuration"""
    return get_config_manager().config


# Backward compatibility
config_manager = get_config_manager()
config = get_config()


if __name__ == "__main__":
    config_manager.print_config()
    print()
    if config_manager.validate():
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration validation failed!") 