ACHIEVEMENTS = {
    "first_lesson": "🎉 Первый урок",
    "ten_words": "🔤 10 слов",
    "seven_day_streak": "🔥 7 дней подряд",
    "first_dialogue": "💬 Первый диалог",
    "writing_level_3": "✍️ Уровень письма 3",
    "writing_level_8": "🖋️ Продвинутое письмо",
    "level_a1": "🎓 Уровень A1",
    "level_a2": "🏅 Уровень A2",
}

GRAMMAR_TOPICS = [
    "to be",
    "pronouns",
    "articles",
    "present simple",
    "questions",
    "past simple",
    "future simple",
]

GRAMMAR_TOPICS_BY_LEVEL = {
    "Pre-A1": [
        "to be",
        "subject pronouns",
        "a and an",
        "have got",
        "basic present simple",
        "simple questions",
    ],
    "A1": [
        "present simple",
        "present continuous",
        "past simple",
        "be going to",
        "countable and uncountable nouns",
        "comparatives",
        "adverbs of frequency",
    ],
    "A2": [
        "present perfect for experience",
        "past continuous and past simple",
        "first conditional",
        "should, must and have to",
        "gerunds and infinitives",
        "relative clauses with who, which and that",
        "too, enough and so",
    ],
}

LEVEL_QUESTIONS = [
    {
        "question": "Что значит слово 'hello'?",
        "options": ["Пока", "Привет", "Спасибо"],
        "correct_index": 1,
    },
    {
        "question": "Выберите перевод: 'I am a student'",
        "options": ["Я учитель", "Я студент", "Я врач"],
        "correct_index": 1,
    },
    {
        "question": "Какой артикль перед 'apple'?",
        "options": ["a", "an", "the"],
        "correct_index": 1,
    },
    {
        "question": "Где правильный порядок слов?",
        "options": ["student I am", "I am student", "I am a student"],
        "correct_index": 2,
    },
    {
        "question": "Что значит 'book'?",
        "options": ["Книга", "Дом", "Вода"],
        "correct_index": 0,
    },
]

WRITING_STAGES = {
    1: [
        {
            "id": "gap_lives",
            "title": "Одно слово",
            "prompt": "Tom ___ in London. (живёт)",
            "answer": "lives",
        },
        {
            "id": "gap_are",
            "title": "Одно слово",
            "prompt": "We ___ friends. (являемся)",
            "answer": "are",
        },
        {
            "id": "gap_has",
            "title": "Одно слово",
            "prompt": "Anna ___ a cat. (имеет)",
            "answer": "has",
        },
    ],
    2: [
        {
            "id": "word_coffee",
            "title": "Перевод слова",
            "prompt": "Как будет «кофе» по-английски?",
            "answer": "coffee",
        },
        {
            "id": "word_weather",
            "title": "Перевод слова",
            "prompt": "Как будет «погода» по-английски?",
            "answer": "weather",
        },
        {
            "id": "word_together",
            "title": "Перевод слова",
            "prompt": "Как будет «вместе» по-английски?",
            "answer": "together",
        },
    ],
    3: [
        {
            "id": "phrase_student",
            "title": "Перевод фразы",
            "prompt": "Переведи: «Я студент».",
            "answer": "I am a student",
        },
        {
            "id": "phrase_like_tea",
            "title": "Перевод фразы",
            "prompt": "Переведи: «Мне нравится чай».",
            "answer": "I like tea",
        },
        {
            "id": "phrase_live_city",
            "title": "Перевод фразы",
            "prompt": "Переведи: «Мы живём в городе».",
            "answer": "We live in the city",
        },
    ],
    4: [
        {
            "id": "order_student",
            "title": "Собери предложение",
            "prompt": "student / I / am / a",
            "answer": "I am a student",
        },
        {
            "id": "order_work",
            "title": "Собери предложение",
            "prompt": "every / works / day / he",
            "answer": "He works every day",
        },
        {
            "id": "order_question",
            "title": "Собери вопрос",
            "prompt": "do / where / live / you",
            "answer": "Where do you live",
        },
    ],
    5: [
        {
            "id": "personal_home",
            "title": "Личное предложение",
            "prompt": "Where do you live? Напиши 1–2 предложения.",
            "reference": "I live in a small city. My home is near a park.",
            "requirements": "Ответить, где живёшь; 1–2 понятных предложения.",
            "min_words": 4,
            "free": True,
        },
        {
            "id": "personal_hobby",
            "title": "Личное предложение",
            "prompt": "What do you like doing in your free time? Напиши 1–2 предложения.",
            "reference": "I like reading books and walking in the park.",
            "requirements": "Назвать хотя бы одно занятие; 1–2 предложения.",
            "min_words": 5,
            "free": True,
        },
        {
            "id": "personal_family",
            "title": "Личное предложение",
            "prompt": "Tell me about your family. Напиши 1–2 предложения.",
            "reference": "I have a small family. I live with my wife and son.",
            "requirements": "Сообщить хотя бы один факт о семье; 1–2 предложения.",
            "min_words": 6,
            "free": True,
        },
    ],
    6: [
        {
            "id": "routine",
            "title": "Связный ответ",
            "prompt": "Describe your usual morning. Напиши 2–3 предложения.",
            "reference": "I get up at seven. I have breakfast and go to work.",
            "requirements": "Описать минимум два утренних действия; 2–3 предложения.",
            "min_words": 10,
            "free": True,
        },
        {
            "id": "last_weekend",
            "title": "Связный ответ",
            "prompt": "What did you do last weekend? Напиши 2–3 предложения.",
            "reference": "I visited my friends on Saturday. We watched a film together.",
            "requirements": "Использовать прошедшее время и назвать два действия.",
            "min_words": 10,
            "free": True,
        },
        {
            "id": "future_plans",
            "title": "Связный ответ",
            "prompt": "What are you going to do next weekend? Напиши 2–3 предложения.",
            "reference": "I am going to visit my parents. We are going to cook dinner.",
            "requirements": "Описать планы на будущее; 2–3 предложения.",
            "min_words": 10,
            "free": True,
        },
    ],
    7: [
        {
            "id": "message_late",
            "title": "Практическое сообщение",
            "prompt": "Напиши другу, что опоздаешь на 20 минут, и извинись. 3–4 предложения.",
            "reference": "Hi! I’m sorry, but I’m going to be 20 minutes late. Please wait for me.",
            "requirements": "Поздороваться, извиниться и указать время опоздания.",
            "min_words": 14,
            "free": True,
        },
        {
            "id": "hotel_request",
            "title": "Практическое сообщение",
            "prompt": "Напиши в отель: попроси тихий номер и уточни время заселения. 3–4 предложения.",
            "reference": "Hello. I would like a quiet room, please. What time can I check in?",
            "requirements": "Попросить тихий номер и задать вопрос о заселении.",
            "min_words": 14,
            "free": True,
        },
        {
            "id": "invite_friend",
            "title": "Практическое сообщение",
            "prompt": "Пригласи друга в кафе в субботу и предложи время. 3–4 предложения.",
            "reference": "Hi! Would you like to go to a cafe on Saturday? We can meet at six.",
            "requirements": "Пригласить, назвать день и предложить время.",
            "min_words": 14,
            "free": True,
        },
    ],
    8: [
        {
            "id": "opinion_city",
            "title": "Мнение с аргументом",
            "prompt": "Is your city a good place to live? Напиши 4–6 предложений и используй because.",
            "reference": "My city is a good place to live because it is quiet and green.",
            "requirements": "Высказать мнение, дать причину с because; 4–6 предложений.",
            "min_words": 24,
            "free": True,
        },
        {
            "id": "story_trip",
            "title": "Короткая история",
            "prompt": "Расскажи о запомнившейся поездке. Напиши 4–6 предложений.",
            "reference": "Last summer I went to the sea with my family. We stayed there for a week.",
            "requirements": "Указать когда, куда и что произошло; использовать прошедшее время.",
            "min_words": 24,
            "free": True,
        },
        {
            "id": "compare_transport",
            "title": "Сравнение",
            "prompt": "Что лучше: машина или общественный транспорт? Напиши 4–6 предложений.",
            "reference": "Public transport is cheaper than a car, but a car is more comfortable.",
            "requirements": "Сравнить два варианта и объяснить свой выбор.",
            "min_words": 24,
            "free": True,
        },
    ],
}

LISTENING_RESOURCES = [
    {
        "title": "VOA Learning English",
        "url": "https://learningenglish.voanews.com/",
        "description": "Новости и уроки на упрощённом английском.",
    },
    {
        "title": "BBC Learning English - 6 Minute English",
        "url": "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english",
        "description": "Короткие подкасты для начинающих.",
    },
]
