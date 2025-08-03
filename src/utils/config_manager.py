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
    default_model: str = "base"
    fallback_model: str = "tiny"
    default_engine: str = "faster-whisper"
    beam_size: int = 5
    language: str = "he"
    word_timestamps: bool = True
    vad_enabled: bool = True
    vad_min_silence_duration_ms: int = 500
    available_models: Optional[list] = None
    available_engines: Optional[list] = None
    
    def __post_init__(self):
        if self.available_models is None:
            self.available_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        if self.available_engines is None:
            self.available_engines = ["faster-whisper", "stable-whisper", "speaker-diarization"]

@dataclass
class SpeakerConfig:
    """Speaker diarization configuration"""
    min_speakers: int = 1
    max_speakers: int = 4
    silence_threshold: float = 2.0
    vad_enabled: bool = True
    word_timestamps: bool = True
    language: str = "he"
    beam_size: int = 5
    vad_min_silence_duration_ms: int = 500
    presets: Optional[dict] = None
    
    def __post_init__(self):
        if self.presets is None:
            self.presets = {
                "default": {
                    "min_speakers": 1,
                    "max_speakers": 2,
                    "silence_threshold": 2.0
                },
                "conversation": {
                    "min_speakers": 2,
                    "max_speakers": 4,
                    "silence_threshold": 1.5
                },
                "interview": {
                    "min_speakers": 2,
                    "max_speakers": 3,
                    "silence_threshold": 2.5
                }
            }

@dataclass
class BatchConfig:
    """Batch processing configuration"""
    enabled: bool = True
    parallel_processing: bool = False
    max_workers: int = 1
    delay_between_files: int = 0
    progress_tracking: bool = True
    continue_on_error: bool = True
    timeout_per_file: int = 600
    retry_failed_files: bool = True
    max_retries: int = 3

@dataclass
class DockerConfig:
    """Docker container configuration"""
    enabled: bool = False
    image_name: str = "whisper-runpod-serverless"
    tag: str = "latest"
    container_name_prefix: str = "whisper-batch"
    auto_cleanup: bool = True
    timeout_seconds: int = 3600
    memory_limit: str = "4g"
    cpu_limit: str = "2"
    kill_existing_containers: bool = True
    detached_mode: bool = True

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
    enabled: bool = False
    serverless_mode: bool = True
    auto_scale: bool = True

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
    auto_organize: bool = True
    include_metadata: bool = True
    include_timestamps: bool = True

@dataclass
class SystemConfig:
    """System and performance configuration"""
    debug: bool = False
    dev_mode: bool = False
    hugging_face_token: Optional[str] = None
    timeout_seconds: int = 300
    retry_attempts: int = 3
    auto_cleanup: bool = True
    session_management: bool = True
    error_reporting: bool = True

@dataclass
class InputConfig:
    """Input file configuration"""
    directory: str = "examples/audio/voice"
    supported_formats: Optional[list] = None
    recursive_search: bool = True
    max_file_size_mb: int = 100
    validate_files: bool = True
    auto_discover: bool = True
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma"]

@dataclass
class AppConfig:
    """Complete application configuration"""
    environment: Environment = Environment.BASE
    transcription: Optional[TranscriptionConfig] = None
    speaker: Optional[SpeakerConfig] = None
    batch: Optional[BatchConfig] = None
    docker: Optional[DockerConfig] = None
    runpod: Optional[RunPodConfig] = None
    output: Optional[OutputConfig] = None
    system: Optional[SystemConfig] = None
    input: Optional[InputConfig] = None
    
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
        batch = BatchConfig(**config_dict.get('batch', {}))
        docker = DockerConfig(**config_dict.get('docker', {}))
        runpod = RunPodConfig(**config_dict.get('runpod', {}))
        output = OutputConfig(**config_dict.get('output', {}))
        system = SystemConfig(**config_dict.get('system', {}))
        input = InputConfig(**config_dict.get('input', {}))
        
        # Debug output
        if os.getenv('DEBUG_CONFIG'):
            print(f"Debug: Creating AppConfig with system.debug={system.debug}")
        
        return AppConfig(
            environment=self._determine_environment(),
            transcription=transcription,
            speaker=speaker,
            batch=batch,
            docker=docker,
            runpod=runpod,
            output=output,
            system=system,
            input=input
        )
    
    def get_speaker_config(self, preset: str = "default") -> 'SpeakerConfig':
        """Get speaker configuration for specific preset"""
        from src.core.speaker_config_factory import SpeakerConfigFactory
        return SpeakerConfigFactory.get_config(preset)
    
    def validate(self) -> bool:
        """Validate required configuration"""
        missing_vars = []
        
        # Check RunPod configuration
        if self.config.runpod and not self.config.runpod.api_key:
            missing_vars.append('RUNPOD_API_KEY')
        if self.config.runpod and not self.config.runpod.endpoint_id:
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
        
        # Ensure all config sections are initialized
        if self.config.transcription is None:
            print("❌ Transcription configuration not initialized")
            return
        if self.config.speaker is None:
            print("❌ Speaker configuration not initialized")
            return
        if self.config.runpod is None:
            print("❌ RunPod configuration not initialized")
            return
        if self.config.output is None:
            print("❌ Output configuration not initialized")
            return
        if self.config.system is None:
            print("❌ System configuration not initialized")
            return
        if self.config.input is None:
            print("❌ Input configuration not initialized")
            return
        if self.config.batch is None:
            print("❌ Batch configuration not initialized")
            return
        if self.config.docker is None:
            print("❌ Docker configuration not initialized")
            return
        
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
        print(f"   Timeout: {self.config.system.timeout_seconds}s")
        print(f"   Retry Attempts: {self.config.system.retry_attempts}")
        print(f"   Auto Cleanup: {self.config.system.auto_cleanup}")
        print(f"   Session Management: {self.config.system.session_management}")
        print(f"   Error Reporting: {self.config.system.error_reporting}")
        
        # Input config
        print("\n📂 Input:")
        print(f"   Directory: {self.config.input.directory}")
        if self.config.input.supported_formats:
            print(f"   Supported Formats: {', '.join(self.config.input.supported_formats)}")
        else:
            print("   Supported Formats: None")
        print(f"   Recursive Search: {self.config.input.recursive_search}")
        print(f"   Max File Size: {self.config.input.max_file_size_mb}MB")
        print(f"   Validate Files: {self.config.input.validate_files}")
        print(f"   Auto Discover: {self.config.input.auto_discover}")
        
        # Batch config
        print("\n🔄 Batch:")
        print(f"   Enabled: {self.config.batch.enabled}")
        print(f"   Parallel Processing: {self.config.batch.parallel_processing}")
        print(f"   Max Workers: {self.config.batch.max_workers}")
        print(f"   Timeout Per File: {self.config.batch.timeout_per_file}s")
        print(f"   Continue On Error: {self.config.batch.continue_on_error}")
        
        # Docker config
        print("\n🐳 Docker:")
        print(f"   Enabled: {self.config.docker.enabled}")
        print(f"   Image: {self.config.docker.image_name}:{self.config.docker.tag}")
        print(f"   Container Prefix: {self.config.docker.container_name_prefix}")
        print(f"   Auto Cleanup: {self.config.docker.auto_cleanup}")
        print(f"   Timeout: {self.config.docker.timeout_seconds}s")
        print(f"   Memory Limit: {self.config.docker.memory_limit}")
        print(f"   CPU Limit: {self.config.docker.cpu_limit}")
    
    def save_config(self, filename: Optional[str] = None):
        """Save current configuration to file"""
        if filename is None:
            filename = f"{self.config.environment.value}.json"
        
        config_file = self.config_dir / filename
        
        # Ensure all config sections are initialized before saving
        if (self.config.transcription is None or self.config.speaker is None or 
            self.config.runpod is None or self.config.output is None or 
            self.config.system is None or self.config.input is None or
            self.config.batch is None or self.config.docker is None):
            print("❌ Cannot save configuration: some sections are not initialized")
            return
        
        # Convert to dictionary
        config_dict = {
            'environment': self.config.environment.value,
            'transcription': asdict(self.config.transcription),
            'speaker': asdict(self.config.speaker),
            'runpod': asdict(self.config.runpod),
            'output': asdict(self.config.output),
            'system': asdict(self.config.system),
            'input': asdict(self.config.input),
            'batch': asdict(self.config.batch),
            'docker': asdict(self.config.docker)
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
                },
                'input': {
                    'directory': 'examples/audio/voice',
                    'supported_formats': [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma"],
                    'recursive_search': True
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