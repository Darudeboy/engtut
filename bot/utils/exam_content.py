"""Curated level-up exams aligned with beginner CEFR skills."""

EXAMS = {
    "A1": {
        "source_level": "Pre-A1",
        "questions": [
            {
                "section": "vocabulary",
                "prompt": "Что означает слово “breakfast”?",
                "options": ["завтрак", "обед", "ужин"],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "Выбери перевод слова “usually”.",
                "options": ["никогда", "обычно", "сейчас"],
                "correct_index": 1,
            },
            {
                "section": "vocabulary",
                "prompt": "Как по-английски «дождь»?",
                "options": ["wind", "snow", "rain"],
                "correct_index": 2,
            },
            {
                "section": "vocabulary",
                "prompt": "Что означает “turn left”?",
                "options": ["повернуть налево", "идти прямо", "остановиться"],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "Выбери слово для «дорогой» о цене.",
                "options": ["cheap", "expensive", "small"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "She ___ a student.",
                "options": ["am", "is", "are"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "Tom ___ coffee every morning.",
                "options": ["drink", "drinks", "drinking"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "I have ___ orange.",
                "options": ["a", "an", "some"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "___ you swim?",
                "options": ["Can", "Are", "Do be"],
                "correct_index": 0,
            },
            {
                "section": "grammar",
                "prompt": "Yesterday we ___ at home.",
                "options": ["stay", "stayed", "stays"],
                "correct_index": 1,
            },
            {
                "section": "reading",
                "passage": (
                    "Anna lives in a small town. She works in a cafe from Monday "
                    "to Friday. She starts work at eight o’clock. After work, Anna "
                    "usually walks home and cooks dinner. On Saturdays she visits "
                    "her sister in the city."
                ),
                "prompt": "Where does Anna live?",
                "options": ["In a city", "In a small town", "Near a school"],
                "correct_index": 1,
            },
            {
                "section": "reading",
                "prompt": "Where does Anna work?",
                "options": ["In a cafe", "In a bank", "In a hotel"],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "prompt": "What time does she start work?",
                "options": ["At seven", "At eight", "At nine"],
                "correct_index": 1,
            },
            {
                "section": "reading",
                "prompt": "What does Anna usually do after work?",
                "options": ["Takes a bus", "Goes shopping", "Walks home"],
                "correct_index": 2,
            },
            {
                "section": "reading",
                "prompt": "Who does Anna visit on Saturdays?",
                "options": ["Her sister", "Her colleague", "Her friend"],
                "correct_index": 0,
            },
        ],
    },
    "A2": {
        "source_level": "A1",
        "questions": [
            {
                "section": "vocabulary",
                "prompt": "If you “miss the bus”, what happens?",
                "options": [
                    "You arrive too late for it",
                    "You buy a ticket",
                    "You drive the bus",
                ],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "What does “borrow” mean?",
                "options": [
                    "Give something forever",
                    "Use something and return it",
                    "Pay for something",
                ],
                "correct_index": 1,
            },
            {
                "section": "vocabulary",
                "prompt": "The train was “crowded”. It was ___.",
                "options": ["full of people", "very fast", "completely empty"],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "An “appointment” is ___.",
                "options": [
                    "a planned meeting",
                    "a type of medicine",
                    "a travel bag",
                ],
                "correct_index": 0,
            },
            {
                "section": "vocabulary",
                "prompt": "To “improve” your English means to ___.",
                "options": ["forget it", "make it better", "translate every word"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "I have never ___ to London.",
                "options": ["be", "been", "was"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "This book is ___ than the film.",
                "options": ["interesting", "more interesting", "most interesting"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "I ___ dinner when you called.",
                "options": ["cooked", "was cooking", "am cooking"],
                "correct_index": 1,
            },
            {
                "section": "grammar",
                "prompt": "We ___ visit our friends next weekend.",
                "options": ["are going to", "going", "have"],
                "correct_index": 0,
            },
            {
                "section": "grammar",
                "prompt": "There isn’t ___ milk in the fridge.",
                "options": ["many", "much", "a few"],
                "correct_index": 1,
            },
            {
                "section": "reading",
                "passage": (
                    "Last year, Mark drove to work every day, but the journey often "
                    "took more than an hour because of traffic. In March, he decided "
                    "to travel by train instead. The station is a ten-minute walk "
                    "from his home, and the train journey takes twenty-five minutes. "
                    "Mark now reads on the way and arrives less tired. Tickets are "
                    "slightly expensive, but he spends less money on petrol."
                ),
                "prompt": "Why did Mark stop driving to work?",
                "options": [
                    "His car was broken",
                    "The traffic made the journey long",
                    "He moved to another city",
                ],
                "correct_index": 1,
            },
            {
                "section": "reading",
                "prompt": "When did Mark start travelling by train?",
                "options": ["Last March", "Last week", "In December"],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "prompt": "How far is the station from Mark’s home?",
                "options": [
                    "A ten-minute walk",
                    "A twenty-five-minute walk",
                    "More than an hour away",
                ],
                "correct_index": 0,
            },
            {
                "section": "reading",
                "prompt": "What does Mark do on the train?",
                "options": ["He works", "He sleeps", "He reads"],
                "correct_index": 2,
            },
            {
                "section": "reading",
                "prompt": "Which statement is true?",
                "options": [
                    "Train tickets are free",
                    "Mark arrives more tired now",
                    "Mark spends less on petrol",
                ],
                "correct_index": 2,
            },
        ],
    },
}

SECTION_LABELS = {
    "vocabulary": "Лексика",
    "grammar": "Грамматика",
    "reading": "Чтение",
}
