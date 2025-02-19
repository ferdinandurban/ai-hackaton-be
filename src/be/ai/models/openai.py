from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Assistant(BaseModel):
    id: str
    object: str = "assistant"  # Set a default value
    created_at: datetime = Field(alias="created_at") 
    name: str 
    description: Optional[str] = None  # Allow for null values
    model: str
    instructions: str
    tools: list = [] 
    tool_resources: dict = {}
    metadata: dict = {}
    top_p: float = 1.0
    temperature: float = 1.0
    response_format: str = "auto" 

class AssistantList(BaseModel):
    data: List[Assistant]
    object: str = "list"  # Set a default value