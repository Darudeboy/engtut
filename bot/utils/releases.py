from aiogram.types import BotCommand

CURRENT_RELEASE_ID = "2026.09-ai-coach"

CURRENT_RELEASE_TEXT = (
    "Что нового\n\n"
    "• AI-наставник отвечает на обычные сообщения вне упражнений.\n"
    "• Просьбы «давай грамматику» и «покажи прогресс» запускают нужный раздел.\n"
    "• Наставник учитывает уровень, цель, слабые темы и историю общения.\n"
    "• После уроков и в напоминаниях появляется персональный следующий шаг.\n"
    "• Чтение, письмо, диалоги и аудирование стали разнообразнее."
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
