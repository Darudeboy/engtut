# English Tutor Telegram Bot

Персональный AI-тьютор по английскому языку для начинающих (Pre-A1 / A0). Бот ведёт от пассивного понимания к активному использованию через микро-шаги.

## Возможности

- Онбординг с определением уровня и настройкой целей
- 📖 Чтение — короткие тексты с вопросами
- 🔤 Слова — карточки с интервальным повторением (SM-2)
- 📚 Грамматика — объяснение + выбор из вариантов
- ✍️ Письмо — 5 уровней сложности
- 💬 Диалоги с AI (DeepSeek)
- 🎧 Аудирование — ссылки на открытые ресурсы
- 📊 Прогресс, streak, достижения, недельная сводка
- ⏰ Напоминания о занятиях

## Стек

- Python 3.11+
- aiogram 3.x
- DeepSeek API (OpenAI-compatible)
- SQLite
- Free Dictionary API, Tatoeba, gTTS

## Быстрый старт (локально)

```bash
# 1. Клонировать / перейти в проект
cd english-tutor-bot

# 2. Создать виртуальное окружение
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
copy .env.example .env   # Windows
# cp .env.example .env   # Linux

# Заполнить в .env:
# BOT_TOKEN=...          (от @BotFather)
# DEEPSEEK_API_KEY=...   (от platform.deepseek.com)

# 5. Запустить бота
python -m bot.main
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и онбординг |
| `/daily` | Ежедневная сессия (10–15 мин) |
| `/stats` | Статистика и достижения |
| `/help` | Справка |

## Деплой на VPS (systemd)

```bash
# На сервере
git clone <repo-url> /root/english-tutor-bot
cd /root/english-tutor-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # заполнить токены

# Установить systemd unit
cp english-tutor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable english-tutor
systemctl start english-tutor
systemctl status english-tutor
```

Обновление:

```bash
cd /root/english-tutor-bot
git pull
systemctl restart english-tutor
```

## Структура проекта

```
english-tutor-bot/
├── bot/
│   ├── main.py
│   ├── config.py
│   ├── handlers/       # Модули обучения
│   ├── services/       # DeepSeek, Dictionary, TTS, SM-2
│   ├── models/         # SQLite репозитории
│   ├── prompts/        # Промпты для LLM
│   └── utils/          # Клавиатуры, состояния
├── data/
│   └── wordlists/      # Тематические словари (JSON)
├── requirements.txt
├── .env.example
└── english-tutor.service
```

## Переменные окружения

| Переменная | Обязательная | Описание |
|------------|--------------|----------|
| `BOT_TOKEN` | Да | Токен Telegram-бота |
| `DEEPSEEK_API_KEY` | Нет* | Ключ DeepSeek API |
| `DEEPSEEK_BASE_URL` | Нет | По умолчанию `https://api.deepseek.com/v1` |
| `DATABASE_PATH` | Нет | Путь к SQLite (по умолчанию `data/english_tutor.db`) |

\* Без DeepSeek API бот работает на fallback-контенте.

## Troubleshooting

- **Бот не отвечает** — проверьте `BOT_TOKEN` и что процесс запущен
- **Cannot connect to api.telegram.org** — Telegram API заблокирован. Включите VPN или добавьте в `.env`:
  ```
  BOT_PROXY=socks5://127.0.0.1:1080
  ```
  Для SOCKS5 установите: `pip install aiohttp-socks`
- **Ошибки DeepSeek** — проверьте `DEEPSEEK_API_KEY`; бот продолжит работу с заготовками
- **Нет озвучки** — gTTS требует интернет; проверьте доступ к сети
- **Логи systemd** — `journalctl -u english-tutor -f`

## Лицензия

Open-source. Все внешние источники данных — бесплатные.
