#!/usr/bin/env python3
import json
from src.models.transcription import TranscriptionConfig

# Load the production config
config = json.load(open('config/environments/production.json'))
trans_dict = config.get('transcription', {})

# Remove unsupported fields
trans_dict.pop('available_models', None)
trans_dict.pop('available_engines', None)

print("Creating TranscriptionConfig with keys:", list(trans_dict.keys()))
print("ctranslate2_optimization keys:", list(trans_dict.get('ctranslate2_optimization', {}).keys()))

try:
    tc = TranscriptionConfig(**trans_dict)
    print("✅ TranscriptionConfig created successfully")
    print("ctranslate2_optimization:", tc.ctranslate2_optimization)
    print("ctranslate2_optimization type:", type(tc.ctranslate2_optimization))
except Exception as e:
    print("❌ Error creating TranscriptionConfig:", e)
    import traceback
    traceback.print_exc()
