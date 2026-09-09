import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Router
from aiogram.filters import Command
from aiogram.types import Message, TelegramObject

from bot.utils.context import get_app_context
from bot.utils.releases import CURRENT_RELEASE_ID, CURRENT_RELEASE_TEXT

logger = logging.getLogger(__name__)
router = Router()


class ReleaseNotesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and not _is_whatsnew_command(event):
            await _show_unseen_release(event)
        return await handler(event, data)


@router.message(Command("whatsnew"))
async def show_release_notes(message: Message) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    await ctx.db.get_or_create_user(user_id, message.from_user.username)
    await message.answer(CURRENT_RELEASE_TEXT, parse_mode=None)
    await ctx.db.mark_release_seen(user_id, CURRENT_RELEASE_ID)


async def _show_unseen_release(message: Message) -> None:
    ctx = get_app_context()
    user_id = message.from_user.id
    user = await ctx.db.fetchone(
        "SELECT onboarding_completed FROM users WHERE user_id = ?",
        (user_id,),
    )
    if not user or not bool(user["onboarding_completed"]):
        return
    if await ctx.db.has_seen_release(user_id, CURRENT_RELEASE_ID):
        return
    try:
        await message.answer(CURRENT_RELEASE_TEXT, parse_mode=None)
        await ctx.db.mark_release_seen(user_id, CURRENT_RELEASE_ID)
    except Exception as exc:
        logger.warning("Failed to show release notes to %s: %s", user_id, exc)


def _is_whatsnew_command(message: Message) -> bool:
    text = message.text or ""
    return text.split(maxsplit=1)[0].split("@", 1)[0].lower() == "/whatsnew"
