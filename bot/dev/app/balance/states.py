from aiogram.fsm.state import StatesGroup, State

class Pay(StatesGroup):
    amount = State()        # ожидание ввода количества звёзд
    wait_payment = State()  # ожидание подтверждения оплаты
