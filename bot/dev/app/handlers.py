from typing import Optional
from aiogram import F, Router
from mutagen.wave import WAVE
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
import os
from aiogram.filters import CommandStart, Command
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import logging
import app.keyboards as kb
from audio_extract import extract_audio
from datetime import datetime
from app.db_storage import add_file_to_storage

router = Router()

file_url = ""
end_file_name = ""

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
    "🎤 Добро пожаловать в бота для транскрибации аудио!\n\n"
    "Просто отправьте аудиофайл или голосовое сообщение, и я переведу его в текст.\n"
    "Первая транскрибация — бесплатно!\n\n"
    "Стоимость: X за минуту аудио",
    parse_mode="Markdown",
    reply_markup=kb.main
)

#А НУЖЕН ЛИ ХЕЛП?
@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Руководство по командам бота:')

@router.message(F.text == 'Выгрузить аудио')
async def cmd_audio(message: Message):
    await message.answer('Пожалуйста, отправьте ваш файл')


# ОБРАБОТЧИК ГС
@router.message(F.voice)
async def handle_voice(message: Message):
    file_id = message.voice.file_id
    await process_audio(message, file_id, "voice")

# ОБРАБОТЧИК АУДИО
@router.message(F.audio)
async def handle_audio(message: Message):
    file_id = message.audio.file_id
    await process_audio(message, file_id, "audio")

# ОБРАБОТЧИК ВИДЕО
@router.message(F.content_type == "video")
async def handle_video(message: Message):
    logging.basicConfig(level=logging.INFO)
    file_id = message.video.file_id
    file_size = message.video.file_size
    logging.info(f"Размер файла: {file_size}")
    max_size = 20 * 1024 * 1024
    if file_size < max_size:
        await process_video(message, file_id)
    else:
        await message.reply("Файл слишком большой, максимальный размер 20МБ, отправьте другой файл")

# ОБРАБОТЧИК КРУЖОЧКОВ В ТГ
@router.message(F.content_type == "video_note")
async def handle_video(message: Message):
    file_id = message.video_note.file_id
    await process_video(message, file_id)

# ОБРАБОТЧИК ФАЙЛОВ НЕ ЯВЛЯЮЩИХСЯ АУДИО ИЛИ ГС 
@router.message(F.photo | F.document)
async def handle_another_files(message: Message):
    await message.answer("Файл не является аудио или голосовым сообщением")

async def process_video(message: Message, file_id: str):
    global file_url
    global end_file_name
    logging.basicConfig(level=logging.INFO)
    bot = message.bot
    file = await bot.get_file(file_id)
    file_path = file.file_path

    file_format = get_video_format(file_path)
    if not file_format:
        logging.error(f"Данный формат видео не поддерживается: {file_path}")
        message.reply("Данный формат файла не поддерживается. Отправьте другой файл")
    
    timestamp = datetime.now().strftime("%Y.%m.%d_%H:%M:%S")
    file_name = f"{message.from_user.id}_{timestamp}{file_format}"
    save_path = os.path.join("downloads", file_name)

    await bot.download_file(file_path, destination=save_path)
    logging.info("Скачан видео файл")
       
    audio_file_name = f"{message.from_user.id}_{timestamp}.wav"
    output_path = os.path.join("downloads", audio_file_name)
    extract_audio(f"downloads/{file_name}", output_path, output_format="wav")
    os.remove(f"downloads/{file_name}")

    if not await has_audio(output_path):
        logging.error(f"Файл не содержит звука или битый")
        await message.answer('Файл тихий или битый, загрузите качественный аудио файл')
        os.remove(save_path)
        os.remove(output_path)
        return

    file_url = await add_file_to_storage(output_path, audio_file_name)
    end_file_name = output_path

    audio = WAVE(output_path)
    duration = audio.info.length
    logging.info(f"Получена длина аудио дорожки: {duration:.2f}")
    await print_price(int(duration), message)


def get_video_format(file_path: str) -> Optional[str]:
    formats = [".webm", ".mp4", ".mov", ".avi", ".mkv"]
    for fmt in formats:
        if file_path.endswith(fmt):
            return fmt
    return None

async def process_audio(message: Message, file_id: str, file_type: str):
    global file_url
    global end_file_name
    logging.basicConfig(level=logging.INFO)
    try:
        # ИНФОРМАЦИЯ О ФАЙЛЕ
        bot = message.bot
        file = await bot.get_file(file_id)
        file_path = file.file_path    

        timestamp = datetime.now().strftime("%Y.%m.%d_%H:%M:%S")
        # ИМЯ ФАЙЛА
        audio_format = get_audio_format(file_path)
        file_name = f"{message.from_user.id}_{timestamp}{audio_format}"
        logging.info(f"{file_path}: {audio_format}")
        save_path = os.path.join("downloads", file_name)


        await bot.download_file(file_path, destination=save_path)
        logging.info(f"Файл сохранен: {save_path}")

        # ПРОВЕРКА НА ЗВУК В ФАЙЛЕ
        if not await has_audio(save_path):
            logging.error(f"Файл не содержит звука или битый")
            await message.answer('Файл тихий или битый, загрузите качественный аудио файл')
            os.remove(save_path)
            return
        
        file_url = await add_file_to_storage(save_path, file_name)
        end_file_name = file_name
        duration = message.voice.duration if file_type == "voice" else message.audio.duration
        await print_price(duration, message)
    except Exception as e:
        logging.error(f"Error: {str(e)}")

def get_audio_format(file_path: str) -> Optional[str]:
    formats = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".oga"]
    for fmt in formats:
        if file_path.endswith(fmt):
            return fmt
    return None

async def print_price(duration: int, message: Message):
    cost = calculate_cost(duration)  # СТОИМОСТЬ
    prices = [LabeledPrice(label="XTR", amount=cost)] 
    await message.answer(
        f"✅ Файл получен!\n"
        f"Длительность: {duration // 60}:{duration % 60:02d} мин.\n"
        f"Стоимость: {cost} XTR")

    await message.answer_invoice(
        title="Оплата транскрибации",
        description=f"Сумма: {cost} XTR",
        prices=prices,
        provider_token="",
        payload="trancrib_payment",
        currency="XTR",
        reply_markup=kb.payment_keyboard(cost), 
    )

async def has_audio(audio_path: str, silence_thresh=-50.0, min_silence_len=1000) -> bool:
    audio = AudioSegment.from_file(audio_path)
    nonsilent_ranges = detect_nonsilent(
        audio, 
        min_silence_len=min_silence_len, 
        silence_thresh=silence_thresh
    )
    return len(nonsilent_ranges) > 0

from aiogram.types import PreCheckoutQuery

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):  
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def success_payment_handler(message: Message):  
    await message.answer(text="Спасибо за вашу оплату!🤗")


def calculate_cost(duration_sec: int) -> float:
    cost_per_minute = 1 # ЗВЁЗДЫ
    minutes = max(1, (duration_sec + 59) // 60)  # Округление вверх
    return minutes * cost_per_minute
#ТРАНСКРИБАЦИЯ
