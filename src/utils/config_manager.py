#!/usr/bin/env python3
"""
Comprehensive Configuration Manager for ivrit-ai voice transcription service
Supports base, development, and production configurations
"""

import os
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class Environment(Enum):
    """Environment types"""
    BASE = "base"
    DEVELOPMENT = "development"
    PRODUCTION = "production"

@dataclass
class TranscriptionConfig:
    """Transcription engine configuration"""
    default_model: str = "ivrit-ai/whisper-large-v3-turbo-ct2"
    fallback_model: str = "ivrit-ai/whisper-large-v3-ct2"
    default_engine: str = "faster-whisper"
    beam_size: int = 5
    language: str = "he"
    word_timestamps: bool = True
    vad_enabled: bool = True
    vad_min_silence_duration_ms: int = 500

@dataclass
class SpeakerConfig:
    """Speaker diarization configuration"""
    min_speakers: int = 2
    max_speakers: int = 4
    silence_threshold: float = 2.0
    vad_enabled: bool = True
    word_timestamps: bool = True
    language: str = "he"
    beam_size: int = 5
    vad_min_silence_duration_ms: int = 500

@dataclass
class RunPodConfig:
    """RunPod service configuration"""
    api_key: Optional[str] = None
    endpoint_id: Optional[str] = None
    max_payload_size: int = 200 * 1024 * 1024  # 200MB
    streaming_enabled: bool = True
    in_queue_timeout: int = 300
    max_stream_timeouts: int = 5
    max_payload_len: int = 10 * 1024 * 1024  # 10MB

@dataclass
class OutputConfig:
    """Output and logging configuration"""
    output_dir: str = "output"
    logs_dir: str = "output/logs"
    transcriptions_dir: str = "output/transcriptions"
    temp_dir: str = "output/temp"
    log_level: str = "INFO"
    log_file: str = "transcription.log"
    save_json: bool = True
    save_txt: bool = True
    save_docx: bool = True
    cleanup_temp_files: bool = True
    temp_file_retention_hours: int = 24

@dataclass
class SystemConfig:
    """System and performance configuration"""
    debug: bool = False
    dev_mode: bool = False
    docker_image_name: str = "whisper-runpod-serverless"
    docker_tag: str = "latest"
    hugging_face_token: Optional[str] = None
    max_workers: int = 1
    timeout_seconds: int = 300
    retry_attempts: int = 3

@dataclass
class AppConfig:
    """Complete application configuration"""
    environment: Environment = Environment.BASE
    transcription: TranscriptionConfig = None
    speaker: SpeakerConfig = None
    runpod: RunPodConfig = None
    output: OutputConfig = None
    system: SystemConfig = None
    
    def __post_init__(self):
        """Initialize default configurations if not provided"""
        # Only initialize if the field is actually None (not provided)
        # Don't override values that were explicitly set
        pass

class ConfigManager:
    """Configuration manager with environment support"""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._load_env_file()
        self._determine_environment()
        self.config = self._load_configuration()
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists"""
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
    
    def _load_configuration(self) -> AppConfig:
        """Load configuration based on environment"""
        # Load base configuration
        base_config = self._load_config_file("environments/base.json")
        
        # Load environment-specific configuration
        env_config = self._load_config_file(f"environments/{self._determine_environment().value}.json")
        
        # Merge configurations
        merged_config = self._merge_configs(base_config, env_config)
        
        # Override with environment variables
        merged_config = self._override_with_env_vars(merged_config)
        
        # Convert to AppConfig object
        return self._dict_to_config(merged_config)
    
    def _load_config_file(self, filename: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        config_file = self.config_dir / filename
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Warning: Could not load {filename}: {e}")
        return {}
    
    def _merge_configs(self, base: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base and environment configurations"""
        merged = base.copy()
        
        def deep_merge(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
            """Deep merge two dictionaries"""
            result = d1.copy()
            for key, value in d2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(merged, env)
    
    def _override_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables"""
        # Transcription config
        if 'transcription' in config:
            config['transcription']['default_model'] = os.getenv('DEFAULT_MODEL', config['transcription'].get('default_model', 'ivrit-ai/whisper-large-v3-turbo-ct2'))
            config['transcription']['fallback_model'] = os.getenv('FALLBACK_MODEL', config['transcription'].get('fallback_model', 'ivrit-ai/whisper-large-v3-ct2'))
            config['transcription']['default_engine'] = os.getenv('DEFAULT_ENGINE', config['transcription'].get('default_engine', 'faster-whisper'))
        
        # RunPod config
        if 'runpod' in config:
            config['runpod']['api_key'] = os.getenv('RUNPOD_API_KEY', config['runpod'].get('api_key'))
            config['runpod']['endpoint_id'] = os.getenv('RUNPOD_ENDPOINT_ID', config['runpod'].get('endpoint_id'))
        
        # System config
        if 'system' in config:
            # Only override if environment variable is set
            debug_env = os.getenv('DEBUG')
            if debug_env is not None:
                config['system']['debug'] = debug_env.lower() == 'true'
            dev_mode_env = os.getenv('DEV_MODE')
            if dev_mode_env is not None:
                config['system']['dev_mode'] = dev_mode_env.lower() == 'true'
            hugging_face_token = os.getenv('HUGGING_FACE_TOKEN')
            if hugging_face_token is not None:
                config['system']['hugging_face_token'] = hugging_face_token
        
        return config
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object"""
        # Convert nested dictionaries to dataclass instances
        transcription = TranscriptionConfig(**config_dict.get('transcription', {}))
        speaker = SpeakerConfig(**config_dict.get('speaker', {}))
        runpod = RunPodConfig(**config_dict.get('runpod', {}))
        output = OutputConfig(**config_dict.get('output', {}))
        system = SystemConfig(**config_dict.get('system', {}))
        
        # Debug output
        if os.getenv('DEBUG_CONFIG'):
            print(f"Debug: Creating AppConfig with system.debug={system.debug}")
        
        return AppConfig(
            environment=self._determine_environment(),
            transcription=transcription,
            speaker=speaker,
            runpod=runpod,
            output=output,
            system=system
        )
    
    def get_speaker_config(self, preset: str = "default") -> SpeakerConfig:
        """Get speaker configuration for specific preset"""
        from src.core.speaker_config_factory import SpeakerConfigFactory
        return SpeakerConfigFactory.get_config(preset)
    
    def validate(self) -> bool:
        """Validate required configuration"""
        missing_vars = []
        
        # Check RunPod configuration
        if not self.config.runpod.api_key:
            missing_vars.append('RUNPOD_API_KEY')
        if not self.config.runpod.endpoint_id:
            missing_vars.append('RUNPOD_ENDPOINT_ID')
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("💡 Run './setup_env.sh' to set up environment variables")
            return False
        
        return True
    
    def print_config(self, show_sensitive: bool = False):
        """Print current configuration"""
        print(f"🔧 Configuration ({self.config.environment.value}):")
        print("=" * 50)
        
        # Transcription config
        print("🎤 Transcription:")
        print(f"   Default Model: {self.config.transcription.default_model}")
        print(f"   Fallback Model: {self.config.transcription.fallback_model}")
        print(f"   Default Engine: {self.config.transcription.default_engine}")
        print(f"   Beam Size: {self.config.transcription.beam_size}")
        print(f"   Language: {self.config.transcription.language}")
        
        # Speaker config
        print("\n👥 Speaker Diarization:")
        print(f"   Min Speakers: {self.config.speaker.min_speakers}")
        print(f"   Max Speakers: {self.config.speaker.max_speakers}")
        print(f"   Silence Threshold: {self.config.speaker.silence_threshold}s")
        print(f"   Beam Size: {self.config.speaker.beam_size}")
        
        # RunPod config
        print("\n☁️  RunPod:")
        print(f"   API Key: {'✅ Set' if self.config.runpod.api_key else '❌ Not set'}")
        print(f"   Endpoint ID: {'✅ Set' if self.config.runpod.endpoint_id else '❌ Not set'}")
        print(f"   Max Payload Size: {self.config.runpod.max_payload_size:,} bytes")
        print(f"   Streaming Enabled: {self.config.runpod.streaming_enabled}")
        
        # Output config
        print("\n📁 Output:")
        print(f"   Output Directory: {self.config.output.output_dir}")
        print(f"   Log Level: {self.config.output.log_level}")
        print(f"   Save Formats: JSON={self.config.output.save_json}, TXT={self.config.output.save_txt}, DOCX={self.config.output.save_docx}")
        
        # System config
        print("\n⚙️  System:")
        print(f"   Debug Mode: {self.config.system.debug}")
        print(f"   Dev Mode: {self.config.system.dev_mode}")
        print(f"   Docker Image: {self.config.system.docker_image_name}:{self.config.system.docker_tag}")
        print(f"   Max Workers: {self.config.system.max_workers}")
        print(f"   Timeout: {self.config.system.timeout_seconds}s")
    
    def save_config(self, filename: str = None):
        """Save current configuration to file"""
        if filename is None:
            filename = f"{self.config.environment.value}.json"
        
        config_file = self.config_dir / filename
        
        # Convert to dictionary
        config_dict = {
            'environment': self.config.environment.value,
            'transcription': asdict(self.config.transcription),
            'speaker': asdict(self.config.speaker),
            'runpod': asdict(self.config.runpod),
            'output': asdict(self.config.output),
            'system': asdict(self.config.system)
        }
        
        # Remove sensitive data
        config_dict['runpod']['api_key'] = None
        config_dict['system']['hugging_face_token'] = None
        
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        print(f"💾 Configuration saved to: {config_file}")
    
    def create_default_configs(self):
        """Create default configuration files"""
        configs = {
            'environments/base.json': {
                'transcription': {
                    'default_model': 'ivrit-ai/whisper-large-v3-turbo-ct2',
                    'fallback_model': 'ivrit-ai/whisper-large-v3-ct2',
                    'default_engine': 'faster-whisper',
                    'beam_size': 5,
                    'language': 'he',
                    'word_timestamps': True,
                    'vad_enabled': True,
                    'vad_min_silence_duration_ms': 500
                },
                'speaker': {
                    'min_speakers': 2,
                    'max_speakers': 4,
                    'silence_threshold': 2.0,
                    'vad_enabled': True,
                    'word_timestamps': True,
                    'language': 'he',
                    'beam_size': 5,
                    'vad_min_silence_duration_ms': 500
                },
                'runpod': {
                    'api_key': None,
                    'endpoint_id': None,
                    'max_payload_size': 200 * 1024 * 1024,
                    'streaming_enabled': True,
                    'in_queue_timeout': 300,
                    'max_stream_timeouts': 5,
                    'max_payload_len': 10 * 1024 * 1024
                },
                'output': {
                    'output_dir': 'output',
                    'logs_dir': 'output/logs',
                    'transcriptions_dir': 'output/transcriptions',
                    'temp_dir': 'output/temp',
                    'log_level': 'INFO',
                    'log_file': 'transcription.log',
                    'save_json': True,
                    'save_txt': True,
                    'save_docx': True,
                    'cleanup_temp_files': True,
                    'temp_file_retention_hours': 24
                },
                'system': {
                    'debug': False,
                    'dev_mode': False,
                    'docker_image_name': 'whisper-runpod-serverless',
                    'docker_tag': 'latest',
                    'hugging_face_token': None,
                    'max_workers': 1,
                    'timeout_seconds': 300,
                    'retry_attempts': 3
                }
            },
            'environments/development.json': {
                'transcription': {
                    'beam_size': 3,
                    'debug': True
                },
                'system': {
                    'debug': True,
                    'dev_mode': True,
                    'timeout_seconds': 600
                },
                'output': {
                    'log_level': 'DEBUG'
                }
            },
            'environments/production.json': {
                'transcription': {
                    'beam_size': 7
                },
                'system': {
                    'debug': False,
                    'dev_mode': False,
                    'max_workers': 2,
                    'timeout_seconds': 180
                },
                'output': {
                    'log_level': 'WARNING'
                }
            }
        }
        
        for filename, config in configs.items():
            config_file = self.config_dir / filename
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"📄 Created {config_file}")

# Global configuration instances (lazy loading)
_config_manager = None
_config = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> AppConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = get_config_manager().config
    return _config

# For backward compatibility
config_manager = get_config_manager()
config = get_config()

if __name__ == "__main__":
    config_manager.print_config()
    print()
    if config_manager.validate():
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration validation failed!") 