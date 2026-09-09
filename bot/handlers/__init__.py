from bot.handlers.dialogue import router as dialogue_router
from bot.handlers.exam import router as exam_router
from bot.handlers.grammar import router as grammar_router
from bot.handlers.listening import router as listening_router
from bot.handlers.menu import router as menu_router
from bot.handlers.onboarding import router as onboarding_router
from bot.handlers.progress import router as progress_router
from bot.handlers.reading import router as reading_router
from bot.handlers.release_notes import router as release_notes_router
from bot.handlers.tutor import privacy_router, router as tutor_router
from bot.handlers.vocabulary import router as vocabulary_router
from bot.handlers.writing import router as writing_router

__all__ = [
    "dialogue_router",
    "exam_router",
    "grammar_router",
    "listening_router",
    "menu_router",
    "onboarding_router",
    "progress_router",
    "privacy_router",
    "reading_router",
    "release_notes_router",
    "tutor_router",
    "vocabulary_router",
    "writing_router",
]
