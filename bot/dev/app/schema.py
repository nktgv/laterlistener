from pydantic import BaseModel, HttpUrl

class TaskTranscribe(BaseModel):
    file_name: str
    file_url: str
