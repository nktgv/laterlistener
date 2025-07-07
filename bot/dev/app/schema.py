from pydantic import BaseModel, HttpUrl

class TaskTranscribe(BaseModel):
    file_name: str
    file_url: str

# https://qdpwrkmdezjvnlkrtoso.supabase.co/storage/v1/object/public/supatest//audio.wav