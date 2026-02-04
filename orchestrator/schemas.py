from pydantic import BaseModel
from typing import Optional

class JobRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None

class VisualRequest(BaseModel):
    audio_path: str
    video_path: Optional[str] = None

class PipelineRequest(BaseModel):
    text: str
    video_path: str
    voice_id: Optional[str] = None

class MotionRequest(BaseModel):
    source_image: str
    driven_audio: str
    output_path: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
