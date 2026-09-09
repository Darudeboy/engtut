# English Tutor Telegram Bot

Персональный AI-тьютор по английскому языку для начинающих (Pre-A1 / A0). Бот ведёт от пассивного понимания к активному использованию через микро-шаги.

## Возможности

- Онбординг с определением уровня и настройкой целей
- 📖 Чтение — короткие тексты с вопросами
- 🔤 Слова — порции 5+5+5, выбор темы и активное повторение по SM-2
- 📚 Грамматика — объяснение + выбор из вариантов
- ✍️ Письмо — 8 развивающихся этапов с ротацией тем и AI-проверкой
- 💬 Уровневые AI-диалоги с персональным разбором
- 🎧 Аудирование внутри Telegram: озвучка и вопросы по записи
- 🌟 Последовательная `/daily`-сессия: повторение → слова → чтение → грамматика
- 🎓 Экзамены повышения уровня: Pre-A1 → A1 → A2
- 🤖 AI-наставник: свободный чат, команды обычным текстом и память общения
- 💡 Персональные рекомендации после уроков и в напоминаниях
- 📊 Честные статусы слов, прогресс, streak, достижения, недельная сводка
- ⏰ Напоминания о занятиях

## Стек

- Python 3.11+
- aiogram 3.x
- DeepSeek API (OpenAI-compatible)
- SQLite локально, PostgreSQL в production
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
| `/exam` | Экзамен для повышения уровня |
| `/stats` | Статистика и достижения |
| `/forget` | Удалить историю общения с AI-наставником |
| `/help` | Справка |

## Бесплатный деплой на Render

Создайте **Web Service** из GitHub-репозитория и укажите:

- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m bot.webhook`
- Health Check Path: `/health`

Добавьте секреты в Render Environment:

- `BOT_TOKEN`
- `DEEPSEEK_API_KEY`
- `DATABASE_URL` — строка подключения Neon PostgreSQL

Render автоматически передаёт публичный адрес в `RENDER_EXTERNAL_URL`, поэтому
`WEBHOOK_BASE_URL` задавать не требуется. Локальный polling-запуск
`python -m bot.main` при этом продолжает работать.

### Постоянная история через Neon

1. Создайте бесплатный проект на <https://console.neon.tech/>.
2. Скопируйте connection string вида `postgresql://...`.
3. Добавьте его в Render Environment как `DATABASE_URL`.
4. Передеплойте сервис. В логах должна появиться строка
   `PostgreSQL database initialized`.

Когда `DATABASE_URL` задан, бот хранит пользователей, уроки, слова, streak и
достижения в Neon. Без него локальный запуск автоматически использует SQLite.

### Пробуждение бесплатного Render

Workflow `.github/workflows/keep-render-awake.yml` запрашивает `/health` каждые
10 минут. Он запускается автоматически после push в GitHub и доступен во вкладке
Actions. Планировщик GitHub может иногда запускаться с задержкой; Render всё равно
не гарантирует отсутствие cold start на бесплатном тарифе.

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
│   ├── webhook.py      # Webhook entrypoint для Render
│   ├── config.py
│   ├── handlers/       # Модули обучения
│   ├── services/       # DeepSeek, Dictionary, TTS, SM-2
│   ├── models/         # SQLite/PostgreSQL репозитории
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
| `DATABASE_URL` | Для Render | Строка подключения Neon/PostgreSQL |
| `WEBHOOK_BASE_URL` | Нет | Публичный URL вне Render |
| `WEBHOOK_PATH` | Нет | Путь webhook, по умолчанию `/webhook` |
| `WEBHOOK_SECRET` | Нет | Секрет проверки запросов Telegram |

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
