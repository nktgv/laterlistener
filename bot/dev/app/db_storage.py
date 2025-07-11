from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "url")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "key")
supabase_conn: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
SUPABASE_BUCKET: str = os.environ.get("SUPABASE_BUCKET", "bucket")


async def add_file_to_storage(file_path: str, audio_file_name: str) -> str:
    with open(file_path, "rb") as f:
        res = supabase_conn.storage.from_(SUPABASE_BUCKET).upload(audio_file_name, f, {"content-type": "audio/wav"})

    if not res:
        raise Exception("Ошибка добавления файла в хранилище")
    
    file_url = supabase_conn.storage.from_(SUPABASE_BUCKET).get_public_url(audio_file_name)
    return file_url

async def upload_file_to_storage(file_path: str, file_name: str, content_type: str = "application/octet-stream") -> str:
    with open(file_path, "rb") as f:
        res = supabase_conn.storage.from_(SUPABASE_BUCKET).upload(file_name, f, {"content-type": content_type})
    if not res:
        raise Exception("Ошибка добавления файла в хранилище")
    file_url = supabase_conn.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
    return file_url