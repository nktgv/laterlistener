# Архитектура папок Telegram-бота LaterListener

## Структура проекта

```
bot/
├── README.md                    # Документация бота
├── requirements.txt             # Зависимости Python
├── .env.example                 # Пример переменных окружения
├── .env                         # Локальные переменные (не в git)
├── docker-compose.yml           # Конфигурация для разработки
├── Dockerfile                   # Production образ
├── .dockerignore               # Исключения для Docker
├── .gitignore                  # Исключения для Git
│
├── src/                        # Исходный код
│   ├── __init__.py
│   ├── main.py                 # Точка входа приложения
│   ├── config.py               # Конфигурация и переменные окружения
│   ├── bot.py                  # Основной класс бота
│   │
│   ├── handlers/               # Обработчики сообщений
│   │   ├── __init__.py
│   │   ├── base.py             # Базовый класс для хендлеров
│   │   ├── commands.py         # Обработчики команд (/start, /help)
│   │   ├── audio.py            # Обработчики аудиофайлов
│   │   ├── errors.py           # Обработка ошибок
│   │   └── payments.py         # Обработка платежей Stars
│   │
│   ├── services/               # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── file_validator.py   # Валидация аудиофайлов
│   │   ├── queue_client.py     # Клиент для работы с очередью
│   │   ├── payment_service.py  # Логика работы с Telegram Stars
│   │   └── notification.py     # Отправка уведомлений
│   │
│   ├── models/                 # Модели данных
│   │   ├── __init__.py
│   │   ├── task.py             # Модель задачи для очереди
│   │   ├── user.py             # Модель пользователя
│   │   └── file.py             # Модель файла
│   │
│   ├── database/               # Работа с базой данных
│   │   ├── __init__.py
│   │   ├── connection.py       # Подключение к БД
│   │   ├── models.py           # SQLAlchemy модели
│   │   └── repositories.py     # Репозитории для работы с данными
│   │
│   ├── utils/                  # Утилиты
│   │   ├── __init__.py
│   │   ├── logger.py           # Настройка логирования
│   │   ├── exceptions.py       # Кастомные исключения
│   │   └── helpers.py          # Вспомогательные функции
│   │
│   └── constants/              # Константы
│       ├── __init__.py
│       ├── messages.py         # Тексты сообщений бота
│       ├── limits.py           # Лимиты (размер файла, длительность)
│       └── status.py           # Статусы задач
│
├── tests/                      # Тесты
│   ├── __init__.py
│   ├── conftest.py             # Конфигурация pytest
│   ├── unit/                   # Юнит-тесты
│   │   ├── test_handlers/
│   │   ├── test_services/
│   │   └── test_models/
│   ├── integration/            # Интеграционные тесты
│   │   ├── test_queue.py
│   │   └── test_database.py
│   └── fixtures/               # Тестовые данные
│       ├── audio_files/
│       └── mock_responses/
│
├── scripts/                    # Скрипты для разработки
│   ├── setup_dev.sh            # Настройка dev окружения
│   ├── run_tests.sh            # Запуск тестов
│   └── deploy.sh               # Скрипт деплоя
│
├── docs/                       # Документация
│   ├── api.md                  # API контракты
│   ├── deployment.md           # Инструкции по деплою
│   └── development.md          # Руководство разработчика
│
└── migrations/                 # Миграции базы данных
    ├── __init__.py
    └── versions/
```

## Детальное описание папок

### `/src` - Основной код

**`main.py`** - Точка входа:
- Инициализация логгера
- Загрузка конфигурации
- Создание и запуск бота
- Обработка graceful shutdown

**`config.py`** - Конфигурация:
```python
class Config:
    TELEGRAM_BOT_TOKEN: str
    DATABASE_URL: str
    RABBITMQ_URL: str
    MAX_FILE_SIZE: int
    SUPPORTED_FORMATS: List[str]
```

**`bot.py`** - Основной класс бота:
- Регистрация хендлеров
- Настройка middleware
- Обработка webhook'ов

### `/src/handlers` - Обработчики сообщений

**`base.py`** - Базовый класс:
```python
class BaseHandler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
```

**`commands.py`** - Команды:
- `/start` - приветствие и инструкции
- `/help` - справка
- `/status` - статус обработки

**`audio.py`** - Обработка аудио:
- Валидация файла
- Проверка баланса
- Создание задачи в очереди

### `/src/services` - Бизнес-логика

**`file_validator.py`**:
```python
class FileValidator:
    def validate_audio(self, file_info: dict) -> ValidationResult
    def check_file_size(self, size: int) -> bool
    def check_duration(self, duration: int) -> bool
```

**`queue_client.py`**:
```python
class QueueClient:
    def send_task(self, task: Task) -> bool
    def get_task_status(self, task_id: str) -> TaskStatus
```

**`payment_service.py`**:
```python
class PaymentService:
    def check_balance(self, user_id: int) -> int
    def deduct_stars(self, user_id: int, amount: int) -> bool
    def process_payment(self, user_id: int, amount: int) -> PaymentResult
```

### `/src/models` - Модели данных

**`task.py`**:
```python
@dataclass
class Task:
    id: str
    user_id: int
    file_id: str
    file_name: str
    mime_type: str
    timestamp: datetime
    status: TaskStatus
    cost_stars: int
```

**`user.py`**:
```python
@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    balance_stars: int
    created_at: datetime
```

### `/src/database` - Работа с БД

**`models.py`** - SQLAlchemy модели:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    balance_stars = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**`repositories.py`** - Репозитории:
```python
class UserRepository:
    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]
    def create_user(self, telegram_id: int, username: str) -> User
    def update_balance(self, user_id: int, new_balance: int) -> bool
```

### `/src/utils` - Утилиты

**`logger.py`** - Настройка логирования:
```python
def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
```

**`exceptions.py`** - Кастомные исключения:
```python
class FileValidationError(Exception):
    pass

class InsufficientBalanceError(Exception):
    pass

class QueueError(Exception):
    pass
```

### `/src/constants` - Константы

**`messages.py`** - Тексты сообщений:
```python
WELCOME_MESSAGE = """
🎧 Добро пожаловать в LaterListener!

Отправьте аудиофайл, и я превращу его в текст.
Стоимость: 1 Star за минуту аудио.

Поддерживаемые форматы: MP3, M4A, WAV, OGG
Максимальный размер: 200 МБ
"""

FILE_ACCEPTED_MESSAGE = """
✅ Файл принят в обработку!

📊 Размер: {size} МБ
⏱️ Длительность: {duration} мин
💫 Стоимость: {cost} Stars

Ожидайте уведомления о готовности.
"""
```

**`limits.py`** - Лимиты:
```python
MAX_FILE_SIZE_MB = 200
MAX_DURATION_MINUTES = 120
SUPPORTED_MIME_TYPES = [
    "audio/mpeg",
    "audio/mp4", 
    "audio/wav",
    "audio/ogg"
]
COST_PER_MINUTE_STARS = 1
```

## Принципы организации

1. **Разделение ответственности**: Каждый модуль отвечает за свою область
2. **Dependency Injection**: Сервисы внедряются в хендлеры
3. **Конфигурация через переменные окружения**: Все настройки вынесены в config
4. **Логирование**: Каждый модуль имеет свой логгер
5. **Тестируемость**: Код структурирован для легкого тестирования
6. **Масштабируемость**: Легко добавлять новые хендлеры и сервисы

## Следующие шаги

1. Создать базовую структуру папок
2. Настроить конфигурацию и логирование
3. Реализовать базовые хендлеры команд
4. Добавить валидацию файлов
5. Интегрировать с очередью сообщений
6. Написать тесты
7. Настроить CI/CD 