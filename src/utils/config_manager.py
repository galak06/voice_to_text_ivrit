#!/usr/bin/env python3
"""
Configuration Manager for ivrit-ai voice transcription service
Follows SOLID principles with clean, focused classes
"""

import os
import json
import logging
from typing import Dict, Any, List, Union
from pathlib import Path
from dotenv import load_dotenv
from src.models.environment import Environment
from src.models.transcription import TranscriptionConfig
from src.models.speaker import SpeakerConfig
from src.models.batch import BatchConfig
from src.models.docker import DockerConfig
from src.models.runpod import RunPodConfig
from src.models.output import OutputConfig
from src.models.system import SystemConfig
from src.models.input import InputConfig
from src.models.chunking import ChunkingConfig
from src.models.processing import ProcessingConfig
from src.models.app_config import AppConfig

logger = logging.getLogger(__name__)



# Import definition paths
try:
    from definition import (
        ROOT_DIR, MODELS_DIR, CONFIG_DIR, OUTPUT_DIR, EXAMPLES_DIR,
        SCRIPTS_DIR, SRC_DIR, TESTS_DIR, TRANSCRIPTIONS_DIR,
        CHUNK_RESULTS_DIR, AUDIO_CHUNKS_DIR, LOGS_DIR, TEMP_DIR, TEMP_CHUNKS_DIR
    )
    DEFINITION_AVAILABLE = True
except ImportError:
    DEFINITION_AVAILABLE = False
    # Fallback values if definition import fails
    ROOT_DIR = os.getcwd()
    MODELS_DIR = 'models'
    CONFIG_DIR = 'config'
    OUTPUT_DIR = 'output'
    EXAMPLES_DIR = 'examples'
    SCRIPTS_DIR = 'scripts'
    SRC_DIR = 'src'
    TESTS_DIR = 'tests'
    TRANSCRIPTIONS_DIR = 'output/transcriptions'
    CHUNK_RESULTS_DIR = 'output/chunk_results'
    AUDIO_CHUNKS_DIR = 'output/audio_chunks'
    LOGS_DIR = 'output/logs'
    TEMP_DIR = 'output/temp'
    TEMP_CHUNKS_DIR = 'output/temp_chunks'


class EnvironmentLoader:
    """Single responsibility: Load and determine environment"""
    
    @staticmethod
    def determine_environment(override: Union[Environment, None] = None) -> Environment:
        """Determine current environment"""
        if override:
            return override
        
        env_var = os.getenv('ENVIRONMENT', '').lower()
        if env_var == 'production':
            return Environment.PRODUCTION
        elif env_var == 'development':
            return Environment.DEVELOPMENT
        else:
            return Environment.BASE


class JsonConfigLoader:
    """Single responsibility: Load and merge JSON configuration files"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
    
    def load_config(self, environment: Environment) -> Dict[str, Any]:
        """Load and merge configuration for given environment"""
        # Load base config (if exists)
        base_config = self.load_json_file("base.json")
        logger.info(f"🔍 Base config loaded: {list(base_config.keys()) if base_config else 'Empty'}")
        
        # Load environment-specific config
        env_config = self.load_json_file(f"{environment.value}.json")
        logger.info(f"🔍 Environment config loaded: {list(env_config.keys()) if env_config else 'Empty'}")
        
        # Merge configurations
        merged_config = self._merge_configs(base_config, env_config)
        logger.info(f"🔍 Merged config keys: {list(merged_config.keys()) if merged_config else 'Empty'}")
        
        # Enhanced transcription config debugging
        if 'transcription' in merged_config:
            transcription_keys = list(merged_config['transcription'].keys()) if merged_config['transcription'] else []
            logger.info(f"🔍 Transcription config keys after merge: {transcription_keys}")
            
            # Debug default_engine specifically
            if 'default_engine' in merged_config['transcription']:
                engine = merged_config['transcription']['default_engine']
                logger.info(f"🔍 CONFIG DEBUG: Default engine after merge: {engine} (type: {type(engine)})")
            else:
                logger.warning(f"⚠️ CONFIG DEBUG: No default_engine found in transcription config!")
            
            # Debug ctranslate2_optimization
            if 'ctranslate2_optimization' in merged_config['transcription']:
                ct2_config = merged_config['transcription']['ctranslate2_optimization']
                logger.info(f"🔍 CTranslate2 config after merge: {ct2_config}")
                if ct2_config is None:
                    logger.error(f"❌ CONFIG DEBUG: ctranslate2_optimization is None - this will cause failures!")
            else:
                logger.warning(f"⚠️ CONFIG DEBUG: No ctranslate2_optimization found in transcription config!")
        else:
            logger.error(f"❌ CONFIG DEBUG: No transcription section found in merged config!")
        
        # Validate critical configuration after merge
        self._validate_critical_config(merged_config)
        
        return merged_config
    
    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load JSON file safely"""
        file_path = self.config_dir / filename
        logger.info(f"🔍 Trying to load file: {file_path}")
        logger.info(f"🔍 File exists: {file_path.exists()}")
        logger.info(f"🔍 Config dir: {self.config_dir}")
        logger.info(f"🔍 Current working directory: {Path.cwd()}")
        
        if not file_path.exists():
            logger.warning(f"⚠️ File not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)
                logger.info(f"✅ Successfully loaded {filename} with keys: {list(content.keys()) if content else 'Empty'}")
                return content
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
    
    def _validate_critical_config(self, config: Dict[str, Any]) -> None:
        """Validate critical configuration requirements"""
        logger.info("🔍 CONFIG DEBUG: Validating critical configuration...")
        
        if 'transcription' not in config:
            logger.error("❌ CONFIG DEBUG: Missing transcription section in configuration")
            return
        
        transcription = config['transcription']
        
        # Validate engine type
        if 'default_engine' in transcription:
            engine = transcription['default_engine']
            logger.info(f"🔍 CONFIG DEBUG: Engine type: {engine}")
            
            # Validate CTranslate2 configuration
            if engine == 'ctranslate2-whisper':
                if 'ctranslate2_optimization' not in transcription or transcription['ctranslate2_optimization'] is None:
                    logger.error("❌ CONFIG DEBUG: ctranslate2_optimization is required for ctranslate2-whisper engine")
                else:
                    logger.info("✅ CONFIG DEBUG: ctranslate2_optimization configuration found")
            else:
                logger.info(f"🔍 CONFIG DEBUG: Engine {engine} does not require ctranslate2_optimization")
        else:
            logger.warning("⚠️ CONFIG DEBUG: No default_engine specified in transcription config")
        
        logger.info("🔍 CONFIG DEBUG: Critical configuration validation completed")


class AppConfigFactory:
    """Single responsibility: Create AppConfig from dictionary"""
    
    @staticmethod
    def create_config(config_dict: Dict[str, Any], environment: Environment) -> AppConfig:
        """Create AppConfig from dictionary with proper default initialization"""
        try:
            # Initialize with defaults if not provided
            config_dict = config_dict.copy()
            
            # Ensure all sections exist with defaults
            sections = ['transcription', 'speaker', 'batch', 'docker', 'runpod', 'output', 'system', 'input', 'chunking', 'processing']
            for section in sections:
                if section not in config_dict or not config_dict[section]:
                    config_dict[section] = {}
            
            # Sanitize unsupported fields for Pydantic models
            trans_dict = dict(config_dict['transcription'])
            trans_dict.pop('available_models', None)
            trans_dict.pop('available_engines', None)
            
            # Ensure sanitized fallback_model
            fb = trans_dict.get('fallback_model')
            if isinstance(fb, str):
                if fb.endswith('-turbo') or fb.endswith('large-v3-turbo'):
                    if 'ivrit-ai/whisper-large-v3' in fb:
                        trans_dict['fallback_model'] = 'ivrit-ai/whisper-large-v3-ct2'
                    else:
                        trans_dict['fallback_model'] = 'large-v3'

            # Map speaker_diarization to speaker for backward compatibility
            # Use 'speaker' section first (from production.json), then fallback to 'speaker_diarization' (from base.json)
            speaker_dict = config_dict.get('speaker', config_dict.get('speaker_diarization', {}))
            
            return AppConfig(
                environment=environment,
                transcription=TranscriptionConfig(**trans_dict),
                speaker=SpeakerConfig(**speaker_dict),
                batch=BatchConfig(**config_dict['batch']),
                docker=DockerConfig(**config_dict['docker']),
                runpod=RunPodConfig(**config_dict['runpod']),
                output=OutputConfig(**config_dict['output']),
                system=SystemConfig(**config_dict['system']),
                input=InputConfig(**config_dict['input']),
                chunking=ChunkingConfig(**config_dict['chunking']),
                processing=ProcessingConfig(**config_dict['processing'])
            )
        except Exception as e:
            logger.error(f"Error creating configuration: {e}")
            # Return config with default-initialized sections
            try:
                return AppConfig(
                    environment=environment,
                    transcription=TranscriptionConfig(),
                    speaker=SpeakerConfig(),
                    batch=BatchConfig(),
                    docker=DockerConfig(),
                    runpod=RunPodConfig(),
                    output=OutputConfig(),
                    system=SystemConfig(),
                    input=InputConfig(),
                    chunking=ChunkingConfig(),
                    processing=ProcessingConfig()
                )
            except Exception:
                return AppConfig(environment=environment)


class EnvFileLoader:
    """Single responsibility: Load .env file using python-dotenv"""
    
    @staticmethod
    def load_env_file(env_file_path: Union[Path, None] = None) -> bool:
        """Load .env file into environment variables"""
        if env_file_path is None:
            env_file_path = Path(".env")
        
        if not env_file_path.exists():
            logger.debug("No .env file found")
            return False
        
        try:
            load_dotenv(env_file_path, override=True)
            logger.info("✅ .env file loaded into environment")
            return True
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
            return False


class ConfigOverrideApplier:
    """Single responsibility: Apply environment variable overrides to config object"""
    
    @staticmethod
    def apply_overrides(config: AppConfig) -> None:
        """Apply all environment variable overrides to config object"""
        # Get all relevant environment variables
        env_vars = {
            'DEFAULT_MODEL': os.getenv('DEFAULT_MODEL'),
            'DEFAULT_ENGINE': os.getenv('DEFAULT_ENGINE'),
            'RUNPOD_API_KEY': os.getenv('RUNPOD_API_KEY'),
            'RUNPOD_ENDPOINT_ID': os.getenv('RUNPOD_ENDPOINT_ID'),
            'DEBUG': os.getenv('DEBUG'),
            'DEV_MODE': os.getenv('DEV_MODE'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL'),
            'HUGGING_FACE_TOKEN': os.getenv('HUGGING_FACE_TOKEN'),
        }
        
        # Apply each environment variable override
        for key, value in env_vars.items():
            if value is not None:
                ConfigOverrideApplier._apply_single_override(config, key, value)
    
    @staticmethod
    def _apply_single_override(config: AppConfig, key: str, value: str) -> None:
        """Apply a single environment variable override"""
        try:
            if key == 'DEFAULT_MODEL':
                ConfigOverrideApplier._apply_transcription_override(config, 'default_model', value)
            elif key == 'DEFAULT_ENGINE':
                ConfigOverrideApplier._apply_transcription_override(config, 'default_engine', value)
            elif key == 'RUNPOD_API_KEY':
                ConfigOverrideApplier._apply_runpod_override(config, 'api_key', value)
            elif key == 'RUNPOD_ENDPOINT_ID':
                ConfigOverrideApplier._apply_runpod_override(config, 'endpoint_id', value)
            elif key == 'DEBUG':
                ConfigOverrideApplier._apply_system_override(config, 'debug', value)
            elif key == 'DEV_MODE':
                ConfigOverrideApplier._apply_system_override(config, 'dev_mode', value)
            elif key == 'LOG_LEVEL':
                ConfigOverrideApplier._apply_system_override(config, 'log_level', value.upper())
            elif key == 'HUGGING_FACE_TOKEN':
                ConfigOverrideApplier._apply_system_override(config, 'hugging_face_token', value)
            else:
                logger.debug(f"Environment variable {key} not mapped to config override")
                
        except Exception as e:
            logger.warning(f"Could not apply {key}={value} to config: {e}")
    
    @staticmethod
    def _apply_transcription_override(config: AppConfig, field: str, value: str) -> None:
        """Apply transcription override"""
        if hasattr(config, 'transcription'):
            setattr(config.transcription, field, value)
            logger.info(f"🔧 Applied {field}={value} to transcription config")
    
    @staticmethod
    def _apply_runpod_override(config: AppConfig, field: str, value: str) -> None:
        """Apply RunPod override"""
        if hasattr(config, 'runpod'):
            setattr(config.runpod, field, value)
            mask = '***' if field == 'api_key' else value
            logger.info(f"🔧 Applied {field}={mask} to RunPod config")
    
    @staticmethod
    def _apply_system_override(config: AppConfig, field: str, value: Any) -> None:
        """Apply system override"""
        if hasattr(config, 'system'):
            if field in ['debug', 'dev_mode']:
                value = value.lower() in ('true', '1', 'yes', 'on')
            setattr(config.system, field, value)
            logger.info(f"🔧 Applied {field}={value} to system config")


class ConfigValidator:
    """Single responsibility: Validate configuration"""
    
    @staticmethod
    def validate(config: AppConfig) -> bool:
        """Validate configuration with comprehensive checks"""
        try:
            # Pydantic validation
            config.model_validate(config.model_dump())
            
            # Business logic validation
            errors = []
            errors.extend(ConfigValidator._check_required_env_vars(config))
            errors.extend(ConfigValidator._validate_paths(config))
            errors.extend(ConfigValidator._check_consistency(config))
            errors.extend(ConfigValidator._check_model_engine_compatibility(config))
            
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
            if len(config.system.hugging_face_token) < 10:
                errors.append('HUGGING_FACE_TOKEN appears to be invalid (too short)')
        
        return errors
    
    @staticmethod
    def _validate_paths(config: AppConfig) -> List[str]:
        """Validate file paths and directories"""
        errors = []
        
        if config.output and config.output.output_dir:
            output_path = Path(config.output.output_dir)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                test_file = output_path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                errors.append(f'Output directory {config.output.output_dir} is not writable: {e}')
        
        if config.output and config.output.logs_dir:
            logs_path = Path(config.output.logs_dir)
            try:
                logs_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f'Logs directory {config.output.logs_dir} cannot be created: {e}')
        
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
        
        if config.speaker:
            if config.speaker.min_speakers > config.speaker.max_speakers:
                errors.append('min_speakers cannot be greater than max_speakers')
            if config.speaker.min_speakers < 1:
                errors.append('min_speakers must be at least 1')
            if config.speaker.max_speakers > 20:
                errors.append('max_speakers cannot exceed 20')
        
        if config.transcription:
            if config.transcription.beam_size < 1 or config.transcription.beam_size > 10:
                errors.append('beam_size must be between 1 and 10')
            if config.transcription.vad_min_silence_duration_ms < 0:
                errors.append('vad_min_silence_duration_ms cannot be negative')
        
        return errors
    
    @staticmethod
    def _check_model_engine_compatibility(config: AppConfig) -> List[str]:
        """Check model and engine compatibility"""
        errors = []
        
        if not config.transcription:
            return errors
        
        custom_whisper_models = {'ivrit-ai/whisper-large-v3-ct2'}
        stable_whisper_models = {'ivrit-ai/whisper-large-v3-ct2'}
        
        model = config.transcription.default_model
        engine = config.transcription.default_engine
        
        if engine == 'stable-whisper' and model in custom_whisper_models:
            errors.append(f'Model {model} requires custom-whisper engine, not stable-whisper')
        elif engine == 'custom-whisper' and model in stable_whisper_models:
            errors.append(f'Model {model} should use stable-whisper engine for better performance')
        
        return errors


class ConfigPrinter:
    """Single responsibility: Display configuration information"""
    
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
            ('Input', config.input, [
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
    """Main configuration manager - orchestrates other components"""
    
    def __init__(self, config_dir: str = "config", environment: Union[Environment, None] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
            environment: Optional environment override
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Determine environment
        self.environment = EnvironmentLoader.determine_environment(environment)
        
        # Load configuration using the pipeline
        self.config = self._load_configuration()
    
    def _load_configuration(self) -> AppConfig:
        """Load configuration using the clean pipeline approach"""
        # 1. Load JSON configurations first
        logger.info("📁 Loading configuration from JSON files...")
        json_loader = JsonConfigLoader(self.config_dir)
        json_config = json_loader.load_config(self.environment)
        logger.info("✅ JSON configuration loaded")
        
        # 2. Create AppConfig from JSON
        config_factory = AppConfigFactory()
        app_config = config_factory.create_config(json_config, self.environment)
        
        # 3. Load .env file last (highest priority)
        logger.info("🔧 Loading .env file and applying final overrides...")
        env_loader = EnvFileLoader()
        env_loader.load_env_file()
        
        # 4. Apply environment variable overrides to config object
        override_applier = ConfigOverrideApplier()
        override_applier.apply_overrides(app_config)
        
        return app_config
    
    def validate(self) -> bool:
        """Validate configuration"""
        return ConfigValidator.validate(self.config)
    
    def debug_config(self) -> None:
        """Debug configuration loading and show critical settings"""
        logger.info("🔍 CONFIG DEBUG: ==========================================")
        logger.info("🔍 CONFIG DEBUG: CONFIGURATION DEBUG INFORMATION")
        logger.info("🔍 CONFIG DEBUG: ==========================================")
        
        # Show environment
        logger.info(f"🔍 CONFIG DEBUG: Environment: {self.environment.value}")
        logger.info(f"🔍 CONFIG DEBUG: Config directory: {self.config_dir}")
        
        # Show transcription config
        if hasattr(self.config, 'transcription') and self.config.transcription:
            trans = self.config.transcription
            logger.info(f"🔍 CONFIG DEBUG: Default engine: {getattr(trans, 'default_engine', 'NOT_SET')}")
            logger.info(f"🔍 CONFIG DEBUG: Default model: {getattr(trans, 'default_model', 'NOT_SET')}")
            logger.info(f"🔍 CONFIG DEBUG: CTranslate2 optimization: {getattr(trans, 'ctranslate2_optimization', 'NOT_SET')}")
            logger.info(f"🔍 CONFIG DEBUG: Beam size: {getattr(trans, 'beam_size', 'NOT_SET')}")
        else:
            logger.error("❌ CONFIG DEBUG: No transcription configuration found!")
        
        # Show output config
        if hasattr(self.config, 'output') and self.config.output:
            output = self.config.output
            logger.info(f"🔍 CONFIG DEBUG: Output directory: {getattr(output, 'output_dir', 'NOT_SET')}")
            logger.info(f"🔍 CONFIG DEBUG: Use processed text only: {getattr(output, 'use_processed_text_only', 'NOT_SET')}")
        else:
            logger.error("❌ CONFIG DEBUG: No output configuration found!")
        
        logger.info("🔍 CONFIG DEBUG: ==========================================")
    
    def print_config(self, show_sensitive: bool = False):
        """Print configuration"""
        ConfigPrinter.print_config(self.config, show_sensitive)
    
    def save_config(self, filename: Union[str, None] = None):
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
    
    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load JSON file safely"""
        file_path = self.config_dir / filename
        logger.info(f"🔍 Trying to load file: {file_path}")
        logger.info(f"🔍 File exists: {file_path.exists()}")
        logger.info(f"🔍 Config dir: {self.config_dir}")
        logger.info(f"🔍 Current working directory: {Path.cwd()}")
        
        if not file_path.exists():
            logger.warning(f"⚠️ File not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)
                logger.info(f"✅ Successfully loaded {filename} with keys: {list(content.keys()) if content else 'Empty'}")
                return content
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
    
    def get_speaker_config(self, preset: str = "default"):
        """Get speaker configuration for specific preset"""
        from src.core.factories.speaker_config_factory import SpeakerConfigFactory
        return SpeakerConfigFactory.get_config(preset)
    
    def set_custom_config_file(self, config_file_path: str) -> None:
        """Set a custom config file to override environment config loading"""
        try:
            from pathlib import Path
            custom_config = self.load_json_file(Path(config_file_path).name)
            if custom_config:
                # Merge custom config with existing config, but preserve the AppConfig object
                merged_dict = self._merge_configs(self.config.model_dump(), custom_config)
                
                # Recreate the AppConfig from the merged dictionary
                from src.models.app_config import AppConfig
                self.config = AppConfig(**merged_dict)
                
                logger.info(f"✅ Custom config file loaded: {config_file_path}")
                logger.info(f"🔍 Custom config keys: {list(custom_config.keys()) if custom_config else 'Empty'}")
            else:
                logger.warning(f"⚠️ Could not load custom config file: {config_file_path}")
        except Exception as e:
            logger.error(f"❌ Error loading custom config file: {e}")
    
    def get_directory_paths(self) -> Dict[str, str]:
        """Get directory paths from definition.py through config manager"""
        if DEFINITION_AVAILABLE:
            return {
                'root_dir': ROOT_DIR,
                'models_dir': MODELS_DIR,
                'config_dir': CONFIG_DIR,
                'output_dir': OUTPUT_DIR,
                'examples_dir': EXAMPLES_DIR,
                'scripts_dir': SCRIPTS_DIR,
                'src_dir': SRC_DIR,
                'tests_dir': TESTS_DIR,
                'transcriptions_dir': TRANSCRIPTIONS_DIR,
                'chunk_results_dir': CHUNK_RESULTS_DIR,
                'audio_chunks_dir': AUDIO_CHUNKS_DIR,
                'logs_dir': LOGS_DIR,
                'temp_dir': TEMP_DIR,
                'temp_chunks_dir': TEMP_CHUNKS_DIR
            }
        else:
            # Fallback paths if definition.py is not available
            return {
                'root_dir': os.getcwd(),
                'models_dir': 'models',
                'config_dir': 'config',
                'output_dir': 'output',
                'scripts_dir': 'scripts',
                'src_dir': 'src',
                'tests_dir': 'tests',
                'transcriptions_dir': 'output/transcriptions',
                'chunk_results_dir': 'output/chunk_results',
                'audio_chunks_dir': 'output/audio_chunks',
                'logs_dir': 'output/logs',
                'temp_dir': 'output/temp',
                'temp_chunks_dir': 'output/temp_chunks'
            }
    

