from aiogram.types import BotCommand

CURRENT_RELEASE_ID = "2026.09-italian"

CURRENT_RELEASE_TEXT = (
    "Что нового\n\n"
    "• Открыта новая программа: 🇮🇹 Итальянский язык.\n"
    "• Язык можно выбрать при первом запуске или кнопкой «🌐 Язык».\n"
    "• Для английского и итальянского отдельно хранятся уровень, слова, "
    "уроки, экзамены и история AI-наставника.\n"
    "• Итальянский доступен в чтении, словах, грамматике, письме, "
    "диалогах, аудировании и ежедневной сессии.\n"
    "• Напоминание теперь можно изменить в настройках."
)

BOT_COMMANDS = [
    BotCommand(command="start", description="Открыть главное меню"),
    BotCommand(command="daily", description="Ежедневная сессия"),
    BotCommand(command="exam", description="Экзамен на следующий уровень"),
    BotCommand(command="stats", description="Прогресс и достижения"),
    BotCommand(command="whatsnew", description="Что нового в боте"),
    BotCommand(command="forget", description="Удалить историю общения"),
    BotCommand(command="help", description="Помощь и возможности"),
]
