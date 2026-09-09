from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU_BUTTONS = [
    ["📖 Чтение", "🔤 Слова"],
    ["📚 Грамматика", "✍️ Письмо"],
    ["💬 Диалог", "🎧 Аудирование"],
    ["🎓 Экзамен", "📊 Мой прогресс"],
    ["🌐 Язык", "⚙️ Настройки"],
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in MAIN_MENU_BUTTONS],
        resize_keyboard=True,
    )


def options_keyboard(
    options: list[str],
    prefix: str,
    token: str | None = None,
) -> InlineKeyboardMarkup:
    callback_prefix = f"{prefix}:{token}" if token else prefix
    buttons = [
        [
            InlineKeyboardButton(
                text=option,
                callback_data=f"{callback_prefix}:{idx}",
            )
        ]
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


def scenario_keyboard(
    scenarios: list[tuple[str, str]] | None = None,
) -> InlineKeyboardMarkup:
    scenarios = scenarios or [
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


def reminder_keyboard(
    callback_prefix: str = "onboard:reminder",
) -> InlineKeyboardMarkup:
    times = ["08:00", "12:00", "18:00", "20:00"]
    rows = [
        [
            InlineKeyboardButton(
                text=t,
                callback_data=f"{callback_prefix}:{t}",
            )
        ]
        for t in times
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="Без напоминаний",
                callback_data=f"{callback_prefix}:none",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏰ Изменить напоминание",
                    callback_data="settings:reminder",
                )
            ]
        ]
    )


def language_keyboard(
    current_language: str,
    callback_prefix: str = "language:select",
) -> InlineKeyboardMarkup:
    languages = [
        ("🇬🇧 Английский", "english"),
        ("🇮🇹 Итальянский", "italian"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'✅ ' if code == current_language else ''}{label}",
                    callback_data=f"{callback_prefix}:{code}",
                )
            ]
            for label, code in languages
        ]
    )


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
    labels = ["Не вспомнил", "С трудом", "Легко"]
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


def review_reveal_keyboard(word_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Показать перевод",
                    callback_data=f"vocab:reveal:{word_id}",
                )
            ]
        ]
    )


def vocabulary_menu_keyboard(
    due_count: int,
    learned_today: int,
    max_new_words: int,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if due_count:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"Повторить слова ({due_count})",
                    callback_data="vocab:start_review",
                )
            ]
        )
    if learned_today < max_new_words:
        label = "Учить 5 новых" if learned_today == 0 else "Ещё 5 новых"
        rows.extend(
            [
                [
                    InlineKeyboardButton(
                        text=label,
                        callback_data="vocab:new:auto",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Выбрать тему",
                        callback_data="vocab:themes",
                    )
                ],
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="Статистика слов", callback_data="vocab:stats"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vocabulary_theme_keyboard(
    themes: list[tuple[str, str]],
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"vocab:new:{theme}",
            )
        ]
        for theme, label in themes
    ]
    rows.append(
        [InlineKeyboardButton(text="Назад", callback_data="vocab:menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
