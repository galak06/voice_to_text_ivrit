#!/usr/bin/env python3
"""
Comprehensive Configuration Manager for ivrit-ai voice transcription service
Supports base, development, and production configurations
"""

import os
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Import Pydantic models
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
        
        # Convert to AppConfig object using Pydantic
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
                config['system']['debug'] = debug_env.lower() in ('true', '1', 'yes', 'on')
            
            dev_mode_env = os.getenv('DEV_MODE')
            if dev_mode_env is not None:
                config['system']['dev_mode'] = dev_mode_env.lower() in ('true', '1', 'yes', 'on')
            
            config['system']['hugging_face_token'] = os.getenv('HUGGING_FACE_TOKEN', config['system'].get('hugging_face_token'))
        
        return config
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object using Pydantic"""
        try:
            # Create AppConfig with environment and nested configs
            app_config = AppConfig(
                environment=self._determine_environment(),
                transcription=TranscriptionConfig(**config_dict.get('transcription', {})) if config_dict.get('transcription') else None,
                speaker=SpeakerConfig(**config_dict.get('speaker', {})) if config_dict.get('speaker') else None,
                batch=BatchConfig(**config_dict.get('batch', {})) if config_dict.get('batch') else None,
                docker=DockerConfig(**config_dict.get('docker', {})) if config_dict.get('docker') else None,
                runpod=RunPodConfig(**config_dict.get('runpod', {})) if config_dict.get('runpod') else None,
                output=OutputConfig(**config_dict.get('output', {})) if config_dict.get('output') else None,
                system=SystemConfig(**config_dict.get('system', {})) if config_dict.get('system') else None,
                input=InputConfig(**config_dict.get('input', {})) if config_dict.get('input') else None
            )
            
            # Debug output
            if os.getenv('DEBUG_CONFIG'):
                if app_config.system:
                    print(f"Debug: Created AppConfig with system.debug={app_config.system.debug}")
            
            return app_config
            
        except Exception as e:
            print(f"❌ Error creating configuration: {e}")
            # Return default configuration on error
            return AppConfig()
    
    def get_speaker_config(self, preset: str = "default"):
        """Get speaker configuration for specific preset"""
        from src.core.speaker_config_factory import SpeakerConfigFactory
        return SpeakerConfigFactory.get_config(preset)
    
    def validate(self) -> bool:
        """Validate required configuration using Pydantic validation"""
        try:
            # Pydantic will automatically validate the config
            self.config.model_validate(self.config.model_dump())
            
            # Additional business logic validation
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
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
    
    def print_config(self, show_sensitive: bool = False):
        """Print current configuration"""
        print(f"🔧 Configuration ({self.config.environment.value}):")
        print("=" * 50)
        
        # Transcription config
        if self.config.transcription:
            print("🎤 Transcription:")
            print(f"   Default Model: {self.config.transcription.default_model}")
            print(f"   Fallback Model: {self.config.transcription.fallback_model}")
            print(f"   Default Engine: {self.config.transcription.default_engine}")
            print(f"   Beam Size: {self.config.transcription.beam_size}")
            print(f"   Language: {self.config.transcription.language}")
        
        # Speaker config
        if self.config.speaker:
            print("\n👥 Speaker Diarization:")
            print(f"   Min Speakers: {self.config.speaker.min_speakers}")
            print(f"   Max Speakers: {self.config.speaker.max_speakers}")
            print(f"   Silence Threshold: {self.config.speaker.silence_threshold}s")
            print(f"   Beam Size: {self.config.speaker.beam_size}")
        
        # RunPod config
        if self.config.runpod:
            print("\n☁️  RunPod:")
            print(f"   API Key: {'✅ Set' if self.config.runpod.api_key else '❌ Not set'}")
            print(f"   Endpoint ID: {'✅ Set' if self.config.runpod.endpoint_id else '❌ Not set'}")
            if show_sensitive and self.config.runpod.api_key:
                print(f"   API Key: {self.config.runpod.api_key[:10]}...")
            print(f"   Enabled: {self.config.runpod.enabled}")
            print(f"   Serverless Mode: {self.config.runpod.serverless_mode}")
        
        # Output config
        if self.config.output:
            print("\n📁 Output:")
            print(f"   Output Directory: {self.config.output.output_dir}")
            print(f"   Logs Directory: {self.config.output.logs_dir}")
            print(f"   Save JSON: {self.config.output.save_json}")
            print(f"   Save TXT: {self.config.output.save_txt}")
            print(f"   Save DOCX: {self.config.output.save_docx}")
        
        # System config
        if self.config.system:
            print("\n⚙️  System:")
            print(f"   Debug Mode: {self.config.system.debug}")
            print(f"   Dev Mode: {self.config.system.dev_mode}")
            print(f"   Timeout: {self.config.system.timeout_seconds}s")
            print(f"   Retry Attempts: {self.config.system.retry_attempts}")
        
        # Input config
        if self.config.input:
            print("\n📂 Input:")
            print(f"   Directory: {self.config.input.directory}")
            print(f"   Recursive Search: {self.config.input.recursive_search}")
            print(f"   Max File Size: {self.config.input.max_file_size_mb}MB")
            print(f"   Supported Formats: {', '.join(self.config.input.supported_formats) if self.config.input.supported_formats else 'None'}")
        
        # Batch config
        if self.config.batch:
            print("\n🔄 Batch Processing:")
            print(f"   Enabled: {self.config.batch.enabled}")
            print(f"   Parallel Processing: {self.config.batch.parallel_processing}")
            print(f"   Max Workers: {self.config.batch.max_workers}")
            print(f"   Timeout Per File: {self.config.batch.timeout_per_file}s")
        
        # Docker config
        if self.config.docker:
            print("\n🐳 Docker:")
            print(f"   Enabled: {self.config.docker.enabled}")
            if self.config.docker.enabled:
                print(f"   Image: {self.config.docker.image_name}:{self.config.docker.tag}")
                print(f"   Memory Limit: {self.config.docker.memory_limit}")
                print(f"   CPU Limit: {self.config.docker.cpu_limit}")
    
    def save_config(self, filename: Optional[str] = None):
        """Save current configuration to JSON file"""
        if filename is None:
            filename = f"config_{self.config.environment.value}.json"
        
        config_file = self.config_dir / filename
        
        try:
            # Use Pydantic's model_dump method for serialization
            config_dict = self.config.model_dump(exclude_none=True)
            
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            print(f"✅ Configuration saved to {config_file}")
            
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    def create_default_configs(self):
        """Create default configuration files"""
        environments = ['base', 'development', 'production']
        
        for env in environments:
            # Create default AppConfig for each environment
            if env == 'production':
                env_enum = Environment.PRODUCTION
            elif env == 'development':
                env_enum = Environment.DEVELOPMENT
            else:
                env_enum = Environment.BASE
            
            # Create default config with environment-specific overrides
            default_config = AppConfig(environment=env_enum)
            
            # Apply environment-specific defaults
            if env == 'production':
                if default_config.system:
                    default_config.system.debug = False
                    default_config.system.dev_mode = False
                if default_config.batch:
                    default_config.batch.parallel_processing = True
                    default_config.batch.max_workers = 4
            elif env == 'development':
                if default_config.system:
                    default_config.system.debug = True
                    default_config.system.dev_mode = True
                if default_config.batch:
                    default_config.batch.parallel_processing = False
                    default_config.batch.max_workers = 1
            
            # Save to file
            config_file = self.config_dir / "environments" / f"{env}.json"
            config_file.parent.mkdir(exist_ok=True)
            
            try:
                config_dict = default_config.model_dump(exclude_none=True)
                with open(config_file, 'w') as f:
                    json.dump(config_dict, f, indent=2, default=str)
                print(f"✅ Created {env} configuration: {config_file}")
            except Exception as e:
                print(f"❌ Error creating {env} configuration: {e}")


# Global configuration instances (lazy loading)
_config_manager = None
_config = None


def get_config_manager() -> ConfigManager:
    """Get singleton configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get current configuration"""
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