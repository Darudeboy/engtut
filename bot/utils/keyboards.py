from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU_BUTTONS = [
    ["📖 Чтение", "🔤 Слова"],
    ["📚 Грамматика", "✍️ Письмо"],
    ["💬 Диалог", "🎧 Аудирование"],
    ["📊 Мой прогресс", "⚙️ Настройки"],
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in MAIN_MENU_BUTTONS],
        resize_keyboard=True,
    )


def options_keyboard(options: list[str], prefix: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=option, callback_data=f"{prefix}:{idx}")]
        for idx, option in enumerate(options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="Нет", callback_data=f"{prefix}:no"),
            ]
        ]
    )


def skip_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Пропустить ⏭", callback_data=f"{prefix}:skip")]]
    )


def dialogue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💡 Подсказка", callback_data="dialogue:hint")],
            [InlineKeyboardButton(text="🏁 Завершить диалог", callback_data="dialogue:finish")],
        ]
    )


def scenario_keyboard() -> InlineKeyboardMarkup:
    scenarios = [
        ("👋 Знакомство", "introduction"),
        ("☕ Заказ кофе", "coffee"),
        ("🎫 Покупка билета", "ticket"),
        ("💬 Small talk", "small_talk"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"dialogue:scenario:{code}")]
            for label, code in scenarios
        ]
    )


def reminder_keyboard() -> InlineKeyboardMarkup:
    times = ["08:00", "12:00", "18:00", "20:00"]
    rows = [[InlineKeyboardButton(text=t, callback_data=f"onboard:reminder:{t}")] for t in times]
    rows.append([InlineKeyboardButton(text="Без напоминаний", callback_data="onboard:reminder:none")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def goal_keyboard() -> InlineKeyboardMarkup:
    goals = [
        ("✈️ Путешествия", "travel"),
        ("💼 Работа", "work"),
        ("🎨 Хобби", "hobby"),
        ("📝 Экзамен", "exam"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"onboard:goal:{code}")]
            for label, code in goals
        ]
    )


def review_quality_keyboard(word_id: int) -> InlineKeyboardMarkup:
    labels = ["😕 Сложно", "😐 Норм", "😊 Легко"]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"vocab:review:{word_id}:{quality}",
                )
                for label, quality in zip(labels, [1, 3, 5])
            ]
        ]
    )
