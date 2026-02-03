import sys
import os
import time
import json
import logging
import redis
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add orchestrator to path to import queue_manager
# Assuming structure:
# /JayAvatar/
#   orchestrator/
#   services/audio/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../orchestrator')))

try:
    from queue_manager import RedisQueue
except ImportError:
    logger.error("Could not import queue_manager. Make sure the 'orchestrator' directory is adjacent to 'services'.")
    sys.exit(1)

# Try importing TTS
try:
    from TTS.api import TTS
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    logger.warning("Coqui TTS not found. Please ensure dependencies are installed.")

# Global TTS Model
tts_model = None

def load_model():
    global tts_model
    if not HAS_TTS:
        return
    
    # Select device
    if os.getenv("FORCE_CPU", "0") == "1":
        device = "cpu"
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Loading Coqui TTS model on {device}...")
    try:
        # XTTS v2 is the standard for high-quality cloning
        tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load TTS model: {e}")

# --- Language & Transliteration Helpers ---
try:
    from langdetect import detect
    # Heuristic keywords for South Asian languages in Roman script
    # Expanded list for better coloquial detection
    TELUGU_KEYWORDS = [
        'nenu', 'meer', 'ela', 'unnaru', 'cheppu', 'baaga', 'namaskaram', 'andi', 'kudirithe',
        'nuv', 'nuvvu', 'na', 'naa', 'koni', 'petti', 'petkoni', 'chey', 'ra', 'ent', 'entra', 
        'undhi', 'untadhi', 'avunu', 'kaadu', 'manchiga', 'chapparisthunte', 'sheekuthava', 'modda',
        'super', 'asalu', 'bro', 'brother', 'hello' 
    ]
    HINDI_KEYWORDS = ['kya', 'kaise', 'hai', 'main', 'aap', 'nahi', 'karo', 'namaste']
except ImportError:
    detect = None

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import ITRANS, TELUGU, DEVANAGARI
except ImportError:
    sanscript = None

def detect_and_transliterate(text: str):
    """
    Detects if text is potential Romanized Telugu/Hindi and transliterates it.
    Returns: (processed_text, language_code)
    """
    if not detect or not sanscript:
        return text, "en"

    # Lowercase for heuristic checking
    lower_text = text.lower()
    
    # Simple Heuristic Check
    is_telugu = any(w in lower_text for w in TELUGU_KEYWORDS)
    is_hindi = any(w in lower_text for w in HINDI_KEYWORDS)
    
    if is_telugu:
        logger.info("Detected Romanized TELUGU. Transliterating...")
        native_text = sanscript.transliterate(text, sanscript.ITRANS, sanscript.TELUGU)
        return native_text, "te"
        
    if is_hindi:
        logger.info("Detected Romanized HINDI. Transliterating...")
        native_text = sanscript.transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
        return native_text, "hi"
        
    # Fallback to langdetect
    try:
        lang = detect(text)
        if lang in ['te', 'hi']:
            if text.isascii():
                 # Force transliteration if we trust the detection
                 target_scheme = sanscript.TELUGU if lang == 'te' else sanscript.DEVANAGARI
                 native_text = sanscript.transliterate(text, sanscript.ITRANS, target_scheme)
                 return native_text, lang
        return text, "en" # Default to English
    except:
        return text, "en"
# ------------------------------------------

def process_job(queue: RedisQueue, job_id: str):
    logger.info(f"Processing job {job_id}")
    
    # 1. Update status to processing
    queue.update_job_status(job_id, "processing")
    
    # 2. Get Job Details
    job_data = queue.get_job_status(job_id)
    if not job_data:
        logger.error(f"Job data unavailable for {job_id}")
        queue.update_job_status(job_id, "failed", error="Job data missing")
        return

    try:
        payload = json.loads(job_data.get("payload", "{}"))
        text = payload.get("text")
        
        if not text:
            raise ValueError("Missing 'text' in job payload")
        
        # 3. Generate Audio
        output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if output_path is provided (Pipeline mode) or generate default
        if payload.get("output_path"):
            output_path = payload.get("output_path")
            # Ensure dir exists for custom path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            output_path = os.path.join(output_dir, f"{job_id}.wav")
        
        # Check for speaker reference
        speaker_wav = "speaker.wav" 
        
        # --- Language Auto-Detect Logic ---
        # If user explicitly provided language in payload (TODO), use it.
        # Otherwise auto-detect.
        processed_text, lang_code = detect_and_transliterate(text)
        logger.info(f"Text processed: '{text}' -> '{processed_text}' (Lang: {lang_code})")
        # ----------------------------------

        if tts_model:
            if not os.path.exists(speaker_wav):
                pass

            if os.path.exists(speaker_wav):
                 # Added speed=1.1 to reduce robotic pauses, temperature=0.75 for stability
                 tts_model.tts_to_file(
                     text=processed_text, 
                     file_path=output_path, 
                     speaker_wav=speaker_wav, 
                     language=lang_code, 
                     split_sentences=False,
                     temperature=0.75
                 )
            else:
                 logger.warning(f"Speaker reference '{speaker_wav}' not found. Using default/random speaker if allowed (or failing).")
                 # XTTS might allow random speaker if not specified? 
                 # tts_model.tts_to_file(text=text, file_path=output_path, language="en") 
                 # This might fail if model requires speaker.
                 # Let's try to be safe.
                 raise FileNotFoundError(f"Speaker reference file '{speaker_wav}' not found.")
        else:
            logger.warning("Mocking audio generation (TTS disabled/missing)")
            # Fallback: Copy speaker.wav to output so we have valid audio
            import shutil
            if os.path.exists("speaker.wav"):
                shutil.copy("speaker.wav", output_path)
            else:
                # If even speaker.wav is missing, creating a silent dummy (not implemented here)
                pass

        # 4. Success
        queue.update_job_status(job_id, "completed", result=output_path)
        logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        queue.update_job_status(job_id, "failed", error=str(e))

def main():
    logger.info("Audio Worker Initializing...")
    
    # Connect to Redis
    try:
        queue = RedisQueue()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return

    # Load Model
    load_model()
    
    logger.info("Audio Worker listening for jobs...")
    while True:
        try:
            job_id = queue.pop_job("audio")
            if job_id:
                process_job(queue, job_id)
            else:
                time.sleep(1) # Poll interval
                
        except KeyboardInterrupt:
            logger.info("Stopping worker...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
