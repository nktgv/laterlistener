from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder 

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Выгрузить аудио')],
                                     [KeyboardButton(text='Личный кабинет')],
                                     [KeyboardButton(text='Баланс')],
                                     [KeyboardButton(text='О нас', callback_data='about'), KeyboardButton(text='Контакты')]],
                                     resize_keyboard=True,
                                     input_field_placeholder='Выберите пункт меню')
def payment_keyboard(amount: int):  
    builder = InlineKeyboardBuilder()  
    builder.button(text=f"Оплатить {amount} ⭐️", pay=True)  
  
    return builder.as_markup()

def balance_menu():
    kb = [
        [InlineKeyboardButton(text="Посмотреть баланс", callback_data="balance_check")],
        [InlineKeyboardButton(text="Пополнить баланс", callback_data="balance_add")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def packages_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="100 минут за 100 звезд (+15 бесплатно)", callback_data="buy_100")],
            [InlineKeyboardButton(text="200 минут за 200 звезд (+30 бесплатно)", callback_data="buy_200")],
            [InlineKeyboardButton(text="300 минут за 300 звезд (+50 бесплатно)", callback_data="buy_300")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_balance_menu")]
        ]
    )