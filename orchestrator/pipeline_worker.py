import sys
import os
import time
import json
import logging
import redis
import wave

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add local directory to path to import queue_manager
sys.path.append(os.path.dirname(__file__))

try:
    from queue_manager import RedisQueue
except ImportError:
    logger.error("Could not import queue_manager.")
    sys.exit(1)


def generate_srt_file(text: str, audio_path: str, output_path: str):
    """
    Generate an SRT subtitle file from text and audio duration.
    Splits text into chunks and distributes across the audio duration.
    """
    # Get audio duration
    try:
        with wave.open(audio_path, 'rb') as audio:
            frames = audio.getnframes()
            rate = audio.getframerate()
            duration = frames / float(rate)
    except Exception as e:
        logger.warning(f"Could not read audio duration: {e}. Using 10s default.")
        duration = 10.0
    
    # Split text into sentences or chunks
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        sentences = [text]
    
    # Calculate time per sentence
    time_per_sentence = duration / len(sentences)
    
    # Generate SRT content
    srt_content = []
    current_time = 0.0
    
    for i, sentence in enumerate(sentences, 1):
        start_time = current_time
        end_time = min(current_time + time_per_sentence, duration)
        
        # Format timestamps as HH:MM:SS,mmm
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        srt_content.append(f"{i}")
        srt_content.append(f"{format_time(start_time)} --> {format_time(end_time)}")
        srt_content.append(sentence.strip())
        srt_content.append("")
        
        current_time = end_time
    
    # Write SRT file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    
    logger.info(f"Generated subtitles: {output_path}")


def process_pipeline_job(queue: RedisQueue, job_id: str):
    logger.info(f"Processing pipeline job {job_id}")
    
    # 1. Update status
    queue.update_job_status(job_id, "processing")
    
    # 2. Get Job Details
    job_data = queue.get_job_status(job_id)
    if not job_data:
        queue.update_job_status(job_id, "failed", error="Job data missing")
        return

    try:
        payload = json.loads(job_data.get("payload", "{}"))
        text = payload.get("text")
        video_input_path = payload.get("video_path")
        
        if not text or not video_input_path:
            raise ValueError("Missing 'text' or 'video_path' in pipeline payload")
        
        # 3. Create Master Output Directory
        # This will be in JayAvatar/outputs/{job_id}/
        # We need absolute path. Assuming we are in orchestrator/
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        master_output_dir = os.path.join(project_root, "outputs", job_id)
        os.makedirs(master_output_dir, exist_ok=True)
        
        logger.info(f"Created master output dir: {master_output_dir}")
        
        # 4. Submit Audio Job
        audio_output_path = os.path.join(master_output_dir, "audio.wav")
        audio_payload = {
            "text": text,
            "voice_id": payload.get("voice_id"),
            "output_path": audio_output_path
        }
        
        audio_job_id = queue.submit_job("audio", audio_payload)
        logger.info(f"Submitted Audio Job {audio_job_id}. Waiting for completion...")
        
        # 5. Wait for Audio Job
        while True:
            audio_status = queue.get_job_status(audio_job_id)
            if audio_status["status"] == "completed":
                break
            elif audio_status["status"] == "failed":
                raise Exception(f"Audio generation failed: {audio_status.get('error')}")
            time.sleep(1)
            
        logger.info("Audio generation complete.")

        # 5.5 Generate Subtitles (if enabled)
        srt_output_path = os.path.join(master_output_dir, "subtitles.srt")
        if payload.get("generate_subtitles", True):
            generate_srt_file(text, audio_output_path, srt_output_path)

        # 6. Submit Visual/Motion Job based on mode
        video_output_path = os.path.join(master_output_dir, "video.mp4")
        mode = payload.get("mode", "motion")  # Default to motion (SadTalker)
        
        if mode == "lipsync":
            # Wav2Lip - lip sync only (faster, but static head)
            visual_payload = {
                "audio_path": audio_output_path,
                "video_path": video_input_path,
                "output_path": video_output_path
            }
            job_id_visual = queue.submit_job("visual", visual_payload)
            queue_name = "visual"
            logger.info(f"Mode: lipsync (Wav2Lip). Submitted Visual Job {job_id_visual}")
            
        elif mode == "emage":
            # Future: EMAGE full-body (not yet implemented)
            raise NotImplementedError("EMAGE full-body mode not yet implemented. Use 'motion' or 'lipsync'.")
            
        else:  # mode == "motion" (default)
            # SadTalker - lip sync + head motion + blinking
            motion_payload = {
                "source_image": video_input_path,
                "driven_audio": audio_output_path,
                "output_path": video_output_path
            }
            job_id_visual = queue.submit_job("motion", motion_payload)
            queue_name = "motion"
            logger.info(f"Mode: motion (SadTalker). Submitted Motion Job {job_id_visual}")
        
        # 7. Wait for Visual/Motion Job
        while True:
            job_status = queue.get_job_status(job_id_visual)
            if job_status["status"] == "completed":
                break
            elif job_status["status"] == "failed":
                raise Exception(f"{queue_name.capitalize()} generation failed: {job_status.get('error')}")
            time.sleep(1)
            
        logger.info(f"{queue_name.capitalize()} video generation complete.")
        
        # 8. Success
        queue.update_job_status(job_id, "completed", result=video_output_path)
        logger.info(f"Pipeline Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error processing pipeline job {job_id}: {e}")
        queue.update_job_status(job_id, "failed", error=str(e))


# Configuration for parallel processing
MAX_CONCURRENT_PIPELINES = int(os.environ.get("MAX_CONCURRENT_PIPELINES", "3"))


def main():
    from concurrent.futures import ThreadPoolExecutor
    
    logger.info(f"Pipeline Worker Initializing (max concurrent: {MAX_CONCURRENT_PIPELINES})...")
    
    try:
        queue = RedisQueue()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return

    logger.info("Pipeline Worker listening for 'pipeline' jobs...")
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PIPELINES) as executor:
        futures = set()
        
        while True:
            try:
                # Remove completed futures
                done_futures = {f for f in futures if f.done()}
                for f in done_futures:
                    try:
                        f.result()  # Raise any exceptions
                    except Exception as e:
                        logger.error(f"Pipeline job exception: {e}")
                futures -= done_futures
                
                # Only pop new jobs if we have capacity
                if len(futures) < MAX_CONCURRENT_PIPELINES:
                    job_id = queue.pop_job("pipeline")
                    if job_id:
                        logger.info(f"Submitting job {job_id} to thread pool ({len(futures)+1}/{MAX_CONCURRENT_PIPELINES})")
                        future = executor.submit(process_pipeline_job, queue, job_id)
                        futures.add(future)
                    else:
                        time.sleep(0.5)
                else:
                    time.sleep(0.5)
                    
            except KeyboardInterrupt:
                logger.info("Stopping worker...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    main()

