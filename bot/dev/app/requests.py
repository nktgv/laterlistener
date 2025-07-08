from app.schema import *
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.environ.get("BACKEND_URL")

def start_transcribe(file_name: str, file_url: str):
    """
    Отправить задачу на транскрибацию (POST /transcribe)
    """
    payload = {"file_name": file_name, "file_url": file_url}
    response = requests.post(f"{BASE_URL}/transcribe", json=payload, timeout=50)
    response.raise_for_status()
    return response.json()


def get_status(task_id: str):
    """
    Получить статус задачи (GET /status/{task_id})
    """
    response = requests.get(f"{BASE_URL}/status/{task_id}", timeout=20)
    response.raise_for_status()
    return response.json()


def get_result(task_id: str):
    """
    Получить результат транскрибации (GET /result/{task_id})
    """
    response = requests.get(f"{BASE_URL}/result/{task_id}", timeout=60)
    response.raise_for_status()
    return response.json() 

def get_token():
    response = requests.get(f"{BASE_URL}/token", timeout=30)
    response.raise_for_status()
    return response.json()