from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder 

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Выгрузить аудио')],
                                     [KeyboardButton(text='Личный кабинет')],
                                     [KeyboardButton(text='О нас', callback_data='about'), KeyboardButton(text='Контакты')]],
                                     resize_keyboard=True,
                                     input_field_placeholder='Выберите пункт меню')
def payment_keyboard(amount: int):  
    builder = InlineKeyboardBuilder()  
    builder.button(text=f"Оплатить {amount} ⭐️", pay=True)  
  
    return builder.as_markup()

