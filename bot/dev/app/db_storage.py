from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase_conn: Client = create_client(url, key)


async def add_file_to_storage(file_path: str, audio_file_name: str) -> str:
    bucket_name = "supatest"
    with open(file_path, "rb") as f:
        res = supabase_conn.storage.from_(bucket_name).upload(audio_file_name, f, {"content-type": "audio/wav"})

    if not res:
        raise Exception("Ошибка добавления файла в хранилище")
    
    file_url = supabase_conn.storage.from_(bucket_name).get_public_url(file_path)
    return file_url