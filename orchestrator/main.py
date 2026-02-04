from fastapi import FastAPI, HTTPException
from schemas import JobRequest, JobResponse, VisualRequest, PipelineRequest, MotionRequest
from queue_manager import RedisQueue
import uvicorn

app = FastAPI(title="JayAvatar Orchestrator")
queue = RedisQueue()

@app.post("/generate", response_model=JobResponse)
async def generate_audio(request: JobRequest):
    job_id = queue.submit_job("audio", request.model_dump())
    return JobResponse(job_id=job_id, status="queued")

@app.post("/animate", response_model=JobResponse)
async def animate_face(request: VisualRequest):
    job_id = queue.submit_job("visual", request.model_dump())
    return JobResponse(job_id=job_id, status="queued")

@app.post("/pipeline", response_model=JobResponse)
async def run_pipeline(request: PipelineRequest):
    job_id = queue.submit_job("pipeline", request.model_dump())
    return JobResponse(job_id=job_id, status="queued")

@app.post("/motion", response_model=JobResponse)
async def generate_motion(request: MotionRequest):
    """Generate talking head video with natural motion (SadTalker)."""
    job_id = queue.submit_job("motion", request.model_dump())
    return JobResponse(job_id=job_id, status="queued")

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    status = queue.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
