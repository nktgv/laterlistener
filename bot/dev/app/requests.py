from fastapi import FastAPI, HTTPException
from schema import *
from app.handlers import file_url, end_file_name
from dotenv import load_dotenv
import os
import requests

app = FastAPI()

load_dotenv()
local_host = os.environ.get("BACKEND_URL")

@app.post('/transcribe')
def start_transcribe(task: TaskTranscribe):
    task.file_name = end_file_name
    task.file_url = file_url
    payload = {
        "file_name": task.file_name,
        "file_url": task.file_url
    }
    try:
        response = requests.post(local_host, json=payload, timeout=50)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Worker error: {response.text}")
        
        return response.status_code
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения: {e}")



# result -> localhost/user1/task_id
# status -> enum
# trasncribe -> 