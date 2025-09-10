from pydantic import BaseModel
from typing import Optional, Dict, Any

class TaskResults(BaseModel):
    success: Optional[bool] = True
    message: str
    object_id: str
    results: Optional[Dict[str, Any]] = None
    background_tasks_scheduled: Optional[int] = 0