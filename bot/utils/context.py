from dataclasses import dataclass, field

from bot.config import Settings

_app_context: "AppContext | None" = None


def set_app_context(ctx: "AppContext") -> None:
    global _app_context
    _app_context = ctx


def get_app_context() -> "AppContext":
    if _app_context is None:
        raise RuntimeError("App context is not initialized")
    return _app_context
from bot.models.database import Database
from bot.models.progress import ProgressRepository
from bot.models.user import UserRepository
from bot.models.vocabulary import VocabularyRepository
from bot.services.deepseek import DeepSeekService
from bot.services.dictionary import DictionaryService
from bot.services.tatoeba import TatoebaService
from bot.services.tts import TTSService


@dataclass
class AppContext:
    settings: Settings
    db: Database
    users: UserRepository
    progress: ProgressRepository
    vocabulary: VocabularyRepository
    deepseek: DeepSeekService
    dictionary: DictionaryService
    tatoeba: TatoebaService
    tts: TTSService
    user_sessions: dict[int, dict] = field(default_factory=dict)

    @classmethod
    def build(cls, settings: Settings) -> "AppContext":
        db = Database(settings.database_path)
        return cls(
            settings=settings,
            db=db,
            users=UserRepository(db),
            progress=ProgressRepository(db),
            vocabulary=VocabularyRepository(db),
            deepseek=DeepSeekService(settings),
            dictionary=DictionaryService(),
            tatoeba=TatoebaService(),
            tts=TTSService(),
        )
