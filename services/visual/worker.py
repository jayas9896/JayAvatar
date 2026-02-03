import sys
import os
import time
import json
import logging
import redis
import torch
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add orchestrator to path to import queue_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../orchestrator')))

try:
    from queue_manager import RedisQueue
except ImportError:
    logger.error("Could not import queue_manager. Make sure the 'orchestrator' directory is adjacent to 'services'.")
    sys.exit(1)

# Placeholder for Wav2Lip model loading
model = None

def load_model():
    global model
    # Select device
    if os.getenv("FORCE_CPU", "0") == "1":
        device = "cpu"
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
    logger.info(f"Loading Visual Service (Wav2Lip) on {device}...")
    
    # TODO: Initialize Wav2Lip here
    # For now, we'll verify the infrastructure first
    model = "MOCKED_MODEL"
    logger.info("Visual Model loaded (MOCKED for implementation phase).")

def process_job(queue: RedisQueue, job_id: str):
    logger.info(f"Processing visual job {job_id}")
    
    # 1. Update status
    queue.update_job_status(job_id, "processing")
    
    # 2. Get Job Details
    job_data = queue.get_job_status(job_id)
    if not job_data:
        logger.error(f"Job data unavailable for {job_id}")
        queue.update_job_status(job_id, "failed", error="Job data missing")
        return

    try:
        payload = json.loads(job_data.get("payload", "{}"))
        audio_path = payload.get("audio_path")
        video_path = payload.get("video_path")
        
        if not audio_path or not video_path:
            raise ValueError("Missing audio_path or video_path in payload")
        
        output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if output_path is provided (Pipeline mode) or generate default
        if payload.get("output_path"):
            output_path = payload.get("output_path")
            # Ensure dir exists for custom path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            output_path = os.path.join(output_dir, f"{job_id}.mp4")
        
        result_path = os.path.abspath(output_path)
        
        # Paths for Wav2Lip
        wav2lip_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "Wav2Lip"))
        checkpoint_path = os.path.join(wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
        
        if not os.path.exists(checkpoint_path):
             # Fallback to standard if GAN not found (though we downloaded GAN)
             checkpoint_path = os.path.join(wav2lip_dir, "checkpoints", "wav2lip.pth")
        
        # Construct command
        # python inference.py --checkpoint_path <ckpt> --face <video> --audio <audio> --outfile <out>
        
        cmd = [
            sys.executable,
            "inference.py",
            "--checkpoint_path", checkpoint_path,
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", result_path,
            "--resize_factor", "1",
            "--nosmooth"
        ]
        
        logger.info(f"Running Wav2Lip: {' '.join(cmd)}")
        
        # Prepare Environment (Handle Force CPU)
        env = os.environ.copy()
        if os.getenv("FORCE_CPU", "0") == "1":
            env["CUDA_VISIBLE_DEVICES"] = "" # Hide GPU from subprocess
        
        # Run Inference
        process = subprocess.run(
            cmd,
            cwd=wav2lip_dir,
            env=env,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"Wav2Lip failed: {process.stderr}")
            raise Exception(f"Wav2Lip failed with code {process.returncode}: {process.stderr}")
            
        logger.info(f"Wav2Lip Output: {process.stdout}")

        # 4. Success
        if not os.path.exists(result_path):
             raise Exception("Output file was not created by Wav2Lip.")

        queue.update_job_status(job_id, "completed", result=result_path)
        logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        queue.update_job_status(job_id, "failed", error=str(e))

def main():
    logger.info("Visual Worker Initializing...")
    
    # Connect to Redis
    try:
        queue = RedisQueue()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return

    # Load Model
    load_model()
    
    logger.info("Visual Worker listening for jobs...")
    while True:
        try:
            job_id = queue.pop_job("visual")
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
