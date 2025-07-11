from app.schema import *
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.environ.get("BACKEND_URL")
SERVICE_API_TOKEN = os.getenv("SERVICE_API_TOKEN")

def start_transcribe(file_name: str, file_url: str, tg_id: int):
    """
    Отправить задачу на транскрибацию (POST /transcribe)
    """
    payload = {"file_name": file_name, "file_url": file_url, "telegram_id": tg_id}
    headers = {
        "Authorization": f"Bearer {SERVICE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/transcribe", json=payload, headers=headers, timeout=50)
    response.raise_for_status()
    return response.json()


def get_status(task_id: str):
    """
    Получить статус задачи (GET /status/{task_id})
    """
    headers = {
        "Authorization": f"Bearer {SERVICE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{BASE_URL}/status/{task_id}", headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def get_result(task_id: str):
    """
    Получить результат транскрибации (GET /result/{task_id})
    """
    headers = {
        "Authorization": f"Bearer {SERVICE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{BASE_URL}/result/{task_id}", headers=headers, timeout=60)
    response.raise_for_status()
    return response.json() 

def get_onetime_token(tg_id: int):
    headers = {
        "Authorization": f"Bearer {SERVICE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"telegram_id": tg_id}
    response = requests.post(f"{BASE_URL}/token/one-time/create", headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()

def authorize_onetime_token(token: str):
    response = requests.post(f"{BASE_URL}/auth/one-time", params={"token": token}, timeout=30)
    response.raise_for_status()
    return response.json()