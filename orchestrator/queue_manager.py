import json
import uuid
import time
import redis
from typing import Dict, Optional, Any

class RedisQueue:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.QUEUE_KEY = "jayavatar:jobs:queue"
        self.JOB_PREFIX = "jayavatar:job:"

    def submit_job(self, job_type: str, payload: Dict[str, Any]) -> str:
        """Creates a new job and pushes it to the queue."""
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "type": job_type,  # 'audio', 'visual', 'composition'
            "status": "queued",
            "created_at": time.time(),
            "payload": json.dumps(payload),
            "result": "",
            "error": ""
        }
        
        # 1. Save Job Data (Persistent)
        self.redis.hset(f"{self.JOB_PREFIX}{job_id}", mapping=job_data)
        
        # 2. Push ID to Queue (Separated by Type)
        queue_name = f"{self.QUEUE_KEY}:{job_type}"
        self.redis.rpush(queue_name, job_id)
        
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Retrieves the full status of a job."""
        job_data = self.redis.hgetall(f"{self.JOB_PREFIX}{job_id}")
        if not job_data:
            return None
        return job_data

    def update_job_status(self, job_id: str, status: str, result: Optional[str] = None, error: Optional[str] = None):
        """Updates job status. Used by Workers."""
        updates = {"status": status}
        if result:
            updates["result"] = result
        if error:
            updates["error"] = error
            
        self.redis.hset(f"{self.JOB_PREFIX}{job_id}", mapping=updates)

    def pop_job(self, job_type: str) -> Optional[str]:
        """Worker calls this to get next job ID for a specific type."""
        # Non-blocking pop. In prod, use blpop for blocking.
        queue_name = f"{self.QUEUE_KEY}:{job_type}"
        return self.redis.lpop(queue_name)
