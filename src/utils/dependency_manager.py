#!/usr/bin/env python3
"""
Centralized dependency manager for the project
Provides unified optional dependency handling across all modules
"""

import logging
import threading
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages optional dependencies with better error handling and documentation"""
    
    def __init__(self):
        self._dependencies = {}
        self._load_dependencies()
    
    def _load_dependencies(self):
        """Load all optional dependencies with proper error handling"""
        dependencies = {
            'torch': {
                'import_name': 'torch',
                'description': 'PyTorch for GPU acceleration and model loading',
                'required_for': ['GPU acceleration', 'Model loading']
            },
            'whisper': {
                'import_name': 'whisper',
                'description': 'OpenAI Whisper for speech recognition',
                'required_for': ['Speech transcription', 'Model loading']
            },
            'librosa': {
                'import_name': 'librosa',
                'description': 'Audio processing library',
                'required_for': ['Audio file loading', 'Duration calculation']
            },
            'psutil': {
                'import_name': 'psutil',
                'description': 'System and process utilities',
                'required_for': ['Memory monitoring', 'Process information']
            },
            'soundfile': {
                'import_name': 'soundfile',
                'description': 'Audio file I/O library',
                'required_for': ['Audio file reading/writing']
            },
            'stable_whisper': {
                'import_name': 'stable_whisper',
                'description': 'Stable Whisper for improved transcription',
                'required_for': ['Stable transcription', 'Better accuracy']
            },
            'ctranslate2': {
                'import_name': 'ctranslate2',
                'description': 'CTranslate2 for optimized inference',
                'required_for': ['Fast inference', 'Optimized models']
            },
            'runpod': {
                'import_name': 'runpod',
                'description': 'RunPod API client',
                'required_for': ['Cloud inference', 'API communication']
            }
        }
        
        for dep_name, dep_info in dependencies.items():
            try:
                module = __import__(dep_info['import_name'])
                self._dependencies[dep_name] = {
                    'available': True,
                    'module': module,
                    'description': dep_info['description'],
                    'required_for': dep_info['required_for']
                }
            except ImportError:
                self._dependencies[dep_name] = {
                    'available': False,
                    'module': None,
                    'description': dep_info['description'],
                    'required_for': dep_info['required_for']
                }
    
    def is_available(self, dependency: str) -> bool:
        """Check if a dependency is available"""
        return self._dependencies.get(dependency, {}).get('available', False)
    
    def get_module(self, dependency: str):
        """Get the imported module if available"""
        dep_info = self._dependencies.get(dependency, {})
        if dep_info.get('available', False):
            return dep_info['module']
        raise ImportError(f"Dependency '{dependency}' is not available")
    
    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies"""
        return [name for name, info in self._dependencies.items() 
                if not info.get('available', False)]
    
    def get_available_dependencies(self) -> List[str]:
        """Get list of available dependencies"""
        return [name for name, info in self._dependencies.items() 
                if info.get('available', False)]
    
    def log_dependency_status(self, logger_instance=None):
        """Log the status of all dependencies"""
        log_func = logger_instance or logger
        available = self.get_available_dependencies()
        missing = self.get_missing_dependencies()
        
        if available:
            log_func.info(f"✅ Available dependencies: {', '.join(available)}")
        
        if missing:
            log_func.warning(f"⚠️ Missing dependencies: {', '.join(missing)}")
            for dep in missing:
                dep_info = self._dependencies[dep]
                log_func.warning(f"   - {dep}: {dep_info['description']}")
                log_func.warning(f"     Required for: {', '.join(dep_info['required_for'])}")


# Thread-safe global instance with lazy initialization
_dependency_manager_instance = None
_dependency_manager_lock = threading.Lock()

def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance with thread-safe initialization"""
    global _dependency_manager_instance
    if _dependency_manager_instance is None:
        with _dependency_manager_lock:
            if _dependency_manager_instance is None:
                _dependency_manager_instance = DependencyManager()
    return _dependency_manager_instance

# Convenience functions for backward compatibility
def TORCH_AVAILABLE(): return get_dependency_manager().is_available('torch')
def WHISPER_AVAILABLE(): return get_dependency_manager().is_available('whisper')
def LIBROSA_AVAILABLE(): return get_dependency_manager().is_available('librosa')
def PSUTIL_AVAILABLE(): return get_dependency_manager().is_available('psutil')
def SOUNDFILE_AVAILABLE(): return get_dependency_manager().is_available('soundfile')
def STABLE_WHISPER_AVAILABLE(): return get_dependency_manager().is_available('stable_whisper')
def CTRANSLATE2_AVAILABLE(): return get_dependency_manager().is_available('ctranslate2')
def TRANSFORMERS_AVAILABLE(): return get_dependency_manager().is_available('transformers')
def RUNPOD_AVAILABLE(): return get_dependency_manager().is_available('runpod')

# Backward compatibility - direct access (deprecated)
dependency_manager = get_dependency_manager()
