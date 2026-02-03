import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Path: {sys.path}")

try:
    import TTS
    print(f"TTS Package: {TTS}")
    print(f"TTS File: {TTS.__file__}")
except ImportError as e:
    print(f"Failed to import TTS: {e}")
except Exception as e:
    print(f"Error importing TTS: {e}")

try:
    from TTS.api import TTS as TTSAPI
    print("Successfully imported TTS.api.TTS")
except Exception as e:
    print(f"Failed to import TTS.api: {e}")
    # Print traceback
    import traceback
    traceback.print_exc()
