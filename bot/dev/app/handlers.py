from typing import Optional
from aiogram import F, Router
from mutagen.wave import WAVE
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
import os
from aiogram.filters import CommandStart, Command
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import logging
import app.keyboards as kb
from audio_extract import extract_audio
from datetime import datetime
from app.db_storage import add_file_to_storage, upload_file_to_storage
from app.requests import start_transcribe, get_status, get_result, get_onetime_token, authorize_onetime_token
from app.utils.convert import export_dialog
import asyncio
import aiofiles.os
import requests
import json 

router = Router()

# Вспомогательные функции
async def wait_for_transcription_completion(task_id: str, message: Message):
    """Ожидание завершения транскрибации и обновление статуса в одном сообщении"""
    sent_msg = await message.answer("Статус задачи: ⏳ Ожидание...")
    while True:
        status = get_status(task_id)
        status_text = status.get('status')
        await sent_msg.edit_text(f"Статус задачи: {status_text}")
        if status_text == 'FINISHED':
            result = get_result(task_id)
            await sent_msg.edit_text(f"✅ Готово!\nРезультат: {result.get('result_url')}")
            return result
        await asyncio.sleep(10)

async def download_and_convert_result(result_url: str, task_id: str):
    """Скачивание и конвертация результата в DOCX и PDF"""
    local_json = f"downloads/{task_id}.json"
    r = requests.get(result_url)
    with open(local_json, 'wb') as f:
        f.write(r.content)
    
    # Конвертация в DOCX и PDF
    docx_path = export_dialog(local_json, file_format='docx')
    pdf_path = export_dialog(local_json, file_format='pdf')
    
    return local_json, docx_path, pdf_path

async def upload_files_to_storage(docx_path: str, pdf_path: str):
    """Загрузка файлов в Supabase и получение URL"""
    docx_name = os.path.basename(docx_path)
    pdf_name = os.path.basename(pdf_path)
    
    docx_url = await upload_file_to_storage(
        docx_path, f"docs/{docx_name}", 
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    pdf_url = await upload_file_to_storage(pdf_path, f"pdfs/{pdf_name}", content_type='application/pdf')
    
    # Удаляем локальные файлы после загрузки в storage
    try:
        await aiofiles.os.remove(docx_path)
        await aiofiles.os.remove(pdf_path)
        logging.info(f"Удалены локальные файлы: {docx_path}, {pdf_path}")
    except Exception as e:
        logging.error(f"Ошибка при удалении файлов: {e}")
    
    return docx_url, pdf_url

def create_download_keyboard(docx_url: str, pdf_url: str, task_id: str):
    """Создание клавиатуры для скачивания файлов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Скачать DOCX", url=docx_url)],
            [InlineKeyboardButton(text="Скачать PDF", url=pdf_url)],
            [InlineKeyboardButton(text="📩 Отправить в чат", callback_data=f"send_to_pm_{task_id}")]
        ]
    )

async def send_webapp_link(message: Message):
    """Отправка ссылки на веб-приложение"""
    try:
        response = get_onetime_token(tg_id=message.from_user.id)
        reply_button = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Перейти в веб-приложение', url=f"https://139.59.145.185?token={response.get('token')}")]]
        )
        await message.answer(
            "🔗 Вот ссылка на твою расшифровку!\n\n"
            "🎛️ На сайте можешь:\n\n"
            "✏️ Редактировать текст\n"
            "🎤 Назначать спикеров\n"
            "⚙️ И многое другое!\n\n"
            "Удачной работы! 🚀✨", 
            parse_mode="Markdown",
            reply_markup=reply_button
        )
    except Exception as e:
        logging.error(f"Ошибка при получении токена: {e}")
        await message.answer("Ошибка при создании ссылки на веб-приложение")

async def process_transcription_result(result: dict, task_id: str, message: Message):
    """Обработка результата транскрибации"""
    result_url = result.get('result_url')
    if not result_url:
        await message.answer("Ошибка: не получен URL результата")
        return
    
    try:
        # Скачивание и конвертация
        local_json, docx_path, pdf_path = await download_and_convert_result(result_url, task_id)
        
        # Загрузка в хранилище
        docx_url, pdf_url = await upload_files_to_storage(docx_path, pdf_path)
        
        # Удаляем JSON файл после конвертации
        try:
            await aiofiles.os.remove(local_json)
            logging.info(f"Удален JSON файл: {local_json}")
        except Exception as e:
            logging.error(f"Ошибка при удалении JSON файла: {e}")
        
        # Создание клавиатуры
        keyboard = create_download_keyboard(docx_url, pdf_url, task_id)
        await message.answer(
            "🎉 Я обработал твой файл!\n\n"
            "📋 Выбери, как тебе удобнее получить результат:\n"
            "📱 Текстом в чат — читай прямо здесь!\n"
            "📎 Файлом — скачай и сохрани",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        # Отправка ссылки на веб-приложение
        await send_webapp_link(message)
        
    except Exception as e:
        logging.error(f"Ошибка при обработке результата: {e}")
        await message.answer("Ошибка при обработке результата транскрибации")

async def start_transcription_task(file_name: str, file_url: str, message: Message):
    """Запуск задачи транскрибации"""
    try:
        start_resp = start_transcribe(file_name, file_url, message.from_user.id)
        task_id = start_resp.get("id")
        await message.answer(
            f"📋 Твой ID: {task_id}\n\n"
            "💾 Сохрани на всякий случай — может пригодиться саппорту! 🆘", 
            parse_mode="Markdown"
        )
        return task_id
    except Exception as e:
        await message.answer(f"Ошибка при запуске транскрибации: {e}")
        return None

@router.message(CommandStart())
async def cmd_start(message: Message):
    # 1. Получение one-time token
    try:
        token_response = get_onetime_token(tg_id=message.from_user.id)
        token = token_response.get('token')
    except Exception as e:
        await message.answer(f'Ошибка при получении one-time token: {e}')
        return

    # 2. Авторизация по one-time token
    try:
        auth_response = authorize_onetime_token(token)
    except Exception as e:
        await message.answer(f'Ошибка авторизации: {e}')
        return

    # 3. Продолжение логики бота
    await message.answer(
        "🎤 Привет! Я расшифровываю видео и аудио!\n\n"
        "Просто отправьте аудиофайл или голосовое сообщение, и я переведу его в текст.\n"
        "Первые 20 минут — БЕСПЛАТНО! 🆓\n\n"
        "Дальше: X рублей за минуту\n"
        "🚀 Жду твой файл! 📤",
        parse_mode="Markdown",
        reply_markup=kb.main
    )
    

#А НУЖЕН ЛИ ХЕЛП?
@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Руководство по командам бота:')

@router.message(F.text == '📤 Загрузить аудио')
async def cmd_audio(message: Message):
    await message.answer(
        "📁 Жду твое аудио или видео! 🎵🎬\n"
        "⚠️ Проверь, чтобы файл был не более 2 ГБ\n"
        "📤 Отправляй! ✨",
        parse_mode="Markdown",
    )


# ОБРАБОТЧИК ГС
@router.message(F.voice)
async def handle_voice(message: Message):
    file_id = message.voice.file_id
    try:
        await process_audio(message, file_id, "voice")
    except Exception as e:
        logging.error(f"Ошибка обработки гс: {str(e)}")
        return

# ОБРАБОТЧИК АУДИО
@router.message(F.audio)
async def handle_audio(message: Message):
    file_id = message.audio.file_id
    try:
        await process_audio(message, file_id, "audio")
    except Exception as e:
        logging.error(f"Ошибка обработки аудио файла: {str(e)}")
        return

# ОБРАБОТЧИК ВИДЕО
@router.message(F.content_type == "video")
async def handle_video(message: Message):
    logging.basicConfig(level=logging.INFO)
    file_id = message.video.file_id
    file_size = message.video.file_size
    logging.info(f"Размер файла: {file_size}")
    try:
        await process_video(message, file_id)
    except Exception as e:
        logging.error(f"Ошибка обработки видео: {str(e)}")
        return

# ОБРАБОТЧИК КРУЖОЧКОВ В ТГ
@router.message(F.content_type == "video_note")
async def handle_video_note(message: Message):
    file_id = message.video_note.file_id
    try:
        await process_video(message, file_id)
    except Exception as e:
        logging.error(f"Ошибка обработки кружочка в тг: {str(e)}")
        return

# ОБРАБОТЧИК ФАЙЛОВ НЕ ЯВЛЯЮЩИХСЯ АУДИО ИЛИ ГС 
@router.message(F.photo | F.document)
async def handle_another_files(message: Message):
    await message.answer("Файл не является аудио или голосовым сообщением")

async def process_video(message: Message, file_id: str):
    logging.basicConfig(level=logging.INFO)
    try:
        bot = message.bot
        file = await bot.get_file(file_id)
        file_path = file.file_path

        file_format = get_video_format(file_path.lower())
        if not file_format:
            logging.error(f"Данный формат видео не поддерживается: {file_path}")
            await message.reply("Данный формат файла не поддерживается. Отправьте другой файл")
            return
        
        timestamp = datetime.now().strftime("%Y.%m.%d_%H-%M-%S")
        file_name = f"{message.from_user.id}_{timestamp}{file_format}"
        save_path = os.path.join("downloads", file_name)

        await bot.download_file(file_path, destination=save_path)
        logging.info("Скачан видео файл")
        
        audio_file_name = f"{message.from_user.id}_{timestamp}.wav"
        output_path = os.path.join("downloads", audio_file_name)
        await asyncio.to_thread(extract_audio, f"downloads/{file_name}", output_path, output_format="wav")
        await aiofiles.os.remove(f"downloads/{file_name}")

        if not await has_audio(output_path):
            logging.error(f"Файл не содержит звука или битый")
            await message.answer('Файл тихий или битый, загрузите качественный аудио файл')
            # Удаляем все временные файлы
            try:
                await aiofiles.os.remove(save_path)
                await aiofiles.os.remove(output_path)
                logging.info(f"Удалены временные файлы: {save_path}, {output_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временных файлов: {e}")
            return
        
        file_url = await add_file_to_storage(output_path, f"audio/{audio_file_name}")

        # Получаем длительность аудио перед удалением файла
        audio = WAVE(output_path)
        duration = audio.info.length
        logging.info(f"Получена длина аудио дорожки: {duration:.2f}")
        await print_price(int(duration), message)

        # Удаляем аудио файл после загрузки в storage
        try:
            await aiofiles.os.remove(output_path)
            logging.info(f"Удален аудио файл: {output_path}")
        except Exception as e:
            logging.error(f"Ошибка при удалении аудио файла: {e}")

        # Запуск транскрибации
        task_id = await start_transcription_task(audio_file_name, file_url, message)
        if not task_id:
            return

        # Ожидание завершения и обработка результата
        result = await wait_for_transcription_completion(task_id, message)
        await process_transcription_result(result, task_id, message)
        
    except Exception as e:
        logging.error(f"Ошибка обработки видео: {str(e)}")
        # Очищаем временные файлы в случае ошибки
        try:
            if 'save_path' in locals():
                await aiofiles.os.remove(save_path)
            if 'output_path' in locals():
                await aiofiles.os.remove(output_path)
            logging.info("Очищены временные файлы после ошибки")
        except Exception as cleanup_error:
            logging.error(f"Ошибка при очистке временных файлов: {cleanup_error}")

def get_video_format(file_path: str) -> Optional[str]:
    formats = [".webm", ".mp4", ".mov", ".avi", ".mkv"]
    for fmt in formats:
        if file_path.endswith(fmt):
            return fmt
    return None

async def process_audio(message: Message, file_id: str, file_type: str):
    logging.basicConfig(level=logging.INFO)
    try:
        # ИНФОРМАЦИЯ О ФАЙЛЕ
        bot = message.bot
        file = await bot.get_file(file_id)
        file_path = file.file_path    

        timestamp = datetime.now().strftime("%Y.%m.%d_%H-%M-%S")
        # ИМЯ ФАЙЛА
        audio_format = get_audio_format(file_path.lower())
        file_name = f"{message.from_user.id}_{timestamp}{audio_format}"
        logging.info(f"{file_path}: {audio_format}")
        save_path = os.path.join("downloads", file_name)

        await bot.download_file(file_path, destination=save_path)
        logging.info(f"Файл сохранен: {save_path}")

        # ПРОВЕРКА НА ЗВУК В ФАЙЛЕ
        if not await has_audio(save_path):
            logging.error(f"Файл не содержит звука или битый")
            await message.answer('Файл тихий или битый, загрузите качественный аудио файл')
            # Удаляем временный файл
            try:
                await aiofiles.os.remove(save_path)
                logging.info(f"Удален временный файл: {save_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {e}")
            return
        
        file_url = await add_file_to_storage(save_path, f"audio/{file_name}")

        # Удаляем аудио файл после загрузки в storage
        try:
            await aiofiles.os.remove(save_path)
            logging.info(f"Удален аудио файл: {save_path}")
        except Exception as e:
            logging.error(f"Ошибка при удалении аудио файла: {e}")

        duration = message.voice.duration if file_type == "voice" else message.audio.duration
        await print_price(duration, message)

        # Запуск транскрибации
        task_id = await start_transcription_task(file_name, file_url, message)
        if not task_id:
            return

        # Ожидание завершения и обработка результата
        result = await wait_for_transcription_completion(task_id, message)
        await process_transcription_result(result, task_id, message)
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        # Очищаем временные файлы в случае ошибки
        try:
            if 'save_path' in locals():
                await aiofiles.os.remove(save_path)
            logging.info("Очищен временный файл после ошибки")
        except Exception as cleanup_error:
            logging.error(f"Ошибка при очистке временного файла: {cleanup_error}")
                      
def get_audio_format(file_path: str) -> Optional[str]:
    formats = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".oga"]
    for fmt in formats:
        if file_path.endswith(fmt):
            return fmt
    return None


async def print_price(duration: int, message: Message):
    cost = calculate_cost(duration)  # СТОИМОСТЬ
    prices = [LabeledPrice(label="XTR", amount=int(cost))] 
    await message.answer(
        "✅ Получил твой файл!\n"
        f"⏱️ Длительность: {duration // 60}:{duration % 60:02d} мин.\n"
        f"💰 Стоимость: {cost} XTR\n"
        "🔄 Начинаю обработку... ⚡",
        parse_mode="Markdown",
    )

    # --- ЗАГЛУШКА ОПЛАТЫ ---
    # await message.answer_invoice(
    #     title="Оплата транскрибации",
    #     description=f"Сумма: {cost} XTR",
    #     prices=prices,
    #     provider_token="",
    #     payload="trancrib_payment",
    #     currency="XTR",
    #     reply_markup=kb.payment_keyboard(int(cost)), 
    # )
    await message.answer("Оплата прошла успешно! Начинаю обработку...")

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
# ОБРАБОТКА НА ЗАПРОС ПОЛЬЗОВАТЕЛЯ ОТПРАВИТЬ ТЕКСТ В ЛС
from aiogram.types import CallbackQuery

@router.callback_query(lambda c: c.data.startswith("send_to_pm_"))
async def send_to_private(callback_query: CallbackQuery):
    task_id = callback_query.data.split("_")[-1]
    user_id = callback_query.from_user.id
    json_path = f"downloads/{task_id}.json"

    try:
        if not os.path.exists(json_path):
            await callback_query.answer("Файл не найден", show_alert=True)
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            json_content = json.load(f)

        # json_content - список с сегментами
        formatted_text = ""
        for segment in json_content:
            speaker = segment.get("speaker", "UNKNOWN_SPEAKER")
            word = segment.get("word", "")
            formatted_text += f"{speaker}: {word}\n"

        formatted_text = formatted_text.strip()
        if not formatted_text:
            await callback_query.answer("Текст пустой, нечего отправлять", show_alert=True)
            return

        max_length = 4000
        if len(formatted_text) > max_length:
            parts = [formatted_text[i:i+max_length] for i in range(0, len(formatted_text), max_length)]
            for i, part in enumerate(parts, 1):
                await callback_query.bot.send_message(chat_id=user_id, text=f"Транскрипция (часть {i}):\n{part}")
            await callback_query.answer("Отправлено в ЛС частями!")
        else:
            await callback_query.bot.send_message(chat_id=user_id, text=f"Транскрипция:\n{formatted_text}")
            await callback_query.answer("Отправлено в ЛС!")

    except Exception as e:
        logging.error(f"Ошибка при отправке в ЛС: {e}")
        await callback_query.answer(" Ошибка при отправке в ЛС", show_alert=True)
