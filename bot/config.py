import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WORDLISTS_DIR = DATA_DIR / "wordlists"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
AUDIO_DIR = DATA_DIR / "audio"

DATA_DIR.mkdir(parents=True, exist_ok=True)
WORDLISTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    database_path: Path
    log_level: str
    new_words_per_day: int = 5
    review_words_per_session: int = 5
    daily_goal_minutes: int = 15


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "")
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not bot_token:
        raise ValueError("BOT_TOKEN is required. Copy .env.example to .env and fill values.")

    return Settings(
        bot_token=bot_token,
        deepseek_api_key=deepseek_api_key,
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        database_path=Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "english_tutor.db"))),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
