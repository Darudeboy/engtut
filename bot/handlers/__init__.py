from bot.handlers.dialogue import router as dialogue_router
from bot.handlers.grammar import router as grammar_router
from bot.handlers.listening import router as listening_router
from bot.handlers.menu import router as menu_router
from bot.handlers.onboarding import router as onboarding_router
from bot.handlers.progress import router as progress_router
from bot.handlers.reading import router as reading_router
from bot.handlers.vocabulary import router as vocabulary_router
from bot.handlers.writing import router as writing_router

__all__ = [
    "dialogue_router",
    "grammar_router",
    "listening_router",
    "menu_router",
    "onboarding_router",
    "progress_router",
    "reading_router",
    "vocabulary_router",
    "writing_router",
]
