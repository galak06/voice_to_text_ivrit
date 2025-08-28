import os

# Root directory structure
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Core directories
MODELS_DIR = os.path.join(ROOT_DIR, "models")
CONFIG_DIR = os.path.join(ROOT_DIR, "config")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
SRC_DIR = os.path.join(ROOT_DIR, "src")
TESTS_DIR = os.path.join(ROOT_DIR, "tests")

# Configuration subdirectories
ENVIRONMENTS_DIR = os.path.join(CONFIG_DIR, "environments")
TEMPLATES_DIR = os.path.join(CONFIG_DIR, "templates")

# Output subdirectories
TRANSCRIPTIONS_DIR = os.path.join(OUTPUT_DIR, "transcriptions")
CHUNK_RESULTS_DIR = os.path.join(OUTPUT_DIR, "chunk_results")
AUDIO_CHUNKS_DIR = os.path.join(OUTPUT_DIR, "audio_chunks")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")
TEMP_CHUNKS_DIR = os.path.join(OUTPUT_DIR, "temp_chunks")

# Examples subdirectories
AUDIO_EXAMPLES_DIR = os.path.join(EXAMPLES_DIR, "audio")
AUDIO_TEST_DIR = os.path.join(AUDIO_EXAMPLES_DIR, "test")
AUDIO_VOICE_DIR = os.path.join(AUDIO_EXAMPLES_DIR, "voice")

# Input directories (where audio files are read from)
INPUT_AUDIO_DIR = AUDIO_EXAMPLES_DIR  # Default input directory
INPUT_VOICE_DIR = AUDIO_VOICE_DIR     # Voice audio files
INPUT_TEST_DIR = AUDIO_TEST_DIR        # Test audio files

# Model-specific paths
IVRIT_WHISPER_LARGE_V3_CT2_DIR = os.path.join(MODELS_DIR, "ivrit-ai", "whisper-large-v3-ct2")
IVRIT_FASTER_WHISPER_V2_D4_DIR = os.path.join(MODELS_DIR, "ivrit-ai", "faster-whisper-v2-d4")

# System constants
SYSTEM_PATHS = {
    "root": ROOT_DIR,
    "models": MODELS_DIR,
    "config": CONFIG_DIR,
    "output": OUTPUT_DIR,
    "examples": EXAMPLES_DIR,
    "scripts": SCRIPTS_DIR,
    "src": SRC_DIR,
    "tests": TESTS_DIR
}

# Output paths
OUTPUT_PATHS = {
    "transcriptions": TRANSCRIPTIONS_DIR,
    "chunk_results": CHUNK_RESULTS_DIR,
    "audio_chunks": AUDIO_CHUNKS_DIR,
    "logs": LOGS_DIR,
    "temp": TEMP_DIR
}

# Configuration paths
CONFIG_PATHS = {
    "environments": ENVIRONMENTS_DIR,
    "templates": TEMPLATES_DIR
}

# Example paths
EXAMPLE_PATHS = {
    "audio": AUDIO_EXAMPLES_DIR,
    "test": AUDIO_TEST_DIR,
    "voice": AUDIO_VOICE_DIR
}

# Input paths
INPUT_PATHS = {
    "audio": INPUT_AUDIO_DIR,
    "voice": INPUT_VOICE_DIR,
    "test": INPUT_TEST_DIR,
    "default": INPUT_AUDIO_DIR
}

# Model paths
MODEL_PATHS = {
    "ivrit-ai/whisper-large-v3-ct2": IVRIT_WHISPER_LARGE_V3_CT2_DIR,
    "ivrit-ai/faster-whisper-v2-d4": IVRIT_FASTER_WHISPER_V2_D4_DIR
}