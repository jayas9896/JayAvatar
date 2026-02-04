#!/usr/bin/env python3
"""
Motion Service Worker (SadTalker)
Generates natural head/body motion from audio + source image.
"""
import os
import sys
import json
import time
import logging
import subprocess

# Add parent to path for queue_manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'orchestrator'))
from queue_manager import RedisQueue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
SADTALKER_DIR = os.path.join(os.path.dirname(__file__), 'SadTalker')
CHECKPOINT_DIR = os.path.join(SADTALKER_DIR, 'checkpoints')
RESULT_DIR = os.path.join(os.path.dirname(__file__), 'outputs')

os.makedirs(RESULT_DIR, exist_ok=True)

def process_job(queue: RedisQueue, job_id: str):
    logger.info(f"Processing motion job {job_id}")
    queue.update_job_status(job_id, "processing")

    job_data = queue.get_job_status(job_id)
    if not job_data:
        logger.error(f"Job data unavailable for {job_id}")
        queue.update_job_status(job_id, "failed", error="Job data missing")
        return

    try:
        payload = json.loads(job_data.get("payload", "{}"))
        source_image = payload.get("source_image")
        driven_audio = payload.get("driven_audio")
        output_path = payload.get("output_path")

        if not source_image or not driven_audio:
            raise ValueError("Missing 'source_image' or 'driven_audio' in payload")

        # Determine output location
        if not output_path:
            output_path = os.path.join(RESULT_DIR, f"{job_id}.mp4")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Build SadTalker command
        cmd = [
            sys.executable, os.path.join(SADTALKER_DIR, 'inference.py'),
            '--source_image', source_image,
            '--driven_audio', driven_audio,
            '--checkpoint_dir', CHECKPOINT_DIR,
            '--result_dir', RESULT_DIR,
            '--enhancer', 'gfpgan',  # Enable face enhancement
            '--size', '512',          # Higher quality
            '--preprocess', 'full',   # Keep full frame context
        ]

        logger.info(f"Running SadTalker: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=SADTALKER_DIR)

        if result.returncode != 0:
            logger.error(f"SadTalker failed: {result.stderr}")
            queue.update_job_status(job_id, "failed", error=result.stderr[:500])
            return

        # SadTalker outputs to RESULT_DIR with timestamped names.
        # Find the most recent .mp4 file and rename/move it.
        import glob
        output_files = sorted(glob.glob(os.path.join(RESULT_DIR, '*.mp4')), key=os.path.getmtime, reverse=True)
        if output_files:
            generated_file = output_files[0]
            os.rename(generated_file, output_path)
            logger.info(f"Motion video saved to: {output_path}")
            queue.update_job_status(job_id, "completed", result=output_path)
        else:
            queue.update_job_status(job_id, "failed", error="No output video found")

    except Exception as e:
        logger.exception(f"Error processing motion job {job_id}: {e}")
        queue.update_job_status(job_id, "failed", error=str(e))


if __name__ == "__main__":
    logger.info("Motion Worker Initializing (SadTalker)...")
    queue = RedisQueue()
    logger.info("Motion Worker listening for jobs...")

    while True:
        try:
            job_id = queue.pop_job("motion")
            if job_id:
                process_job(queue, job_id)
            else:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Motion Worker shutting down.")
            break
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            time.sleep(5)
