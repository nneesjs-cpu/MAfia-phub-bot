import asyncio
import os
import glob
import shutil

# prefer yt_dlp (more updated); fallback to youtube_dl if yt_dlp not installed
try:
    from yt_dlp import YoutubeDL as YTDL
except Exception:
    import youtube_dl as YTDL

from pornhub_api import PornhubApi
from pornhub_api.backends.aiohttp import AioHttpBackend
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    Message
)
from youtube_dl.utils import DownloadError

from config import Config
from helpers import download_progress_hook
from sql import add_user, count_users, user_list, remove_user

# Ensure API_ID is int or None
API_ID = Config.API_ID
API_HASH = Config.API_HASH
BOT_TOKEN = Config.BOT_TOKEN

if API_ID is None or API_HASH is None or BOT_TOKEN is None:
    raise RuntimeError("Please set API_ID, API_HASH and BOT_TOKEN environment variables.")

app = Client(
    "pornhub_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="."
)

# Ensure downloads directory exists
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

btn1 = InlineKeyboardButton("Search Here", switch_inline_query_current_chat="")
btn2 = InlineKeyboardButton("Go Inline", switch_inline_query="")

active_list = set()

# filter to detect pornhub urls in messages
link_filter = filters.regex(r"(?i)(https?://)?(www\.)?pornhub\.(com|org|xxx)")

async def run_async(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)

@app.on_inline_query()
async def search(client, inline_query: InlineQuery):
    query = inline_query.query or ""
    if not query:
        await inline_query.answer([], switch_pm_text="Search Results", switch_pm_parameter="start")
        return

    backend = AioHttpBackend()
    api = PornhubApi(backend=backend)
    results = []
    try:
        src = await api.search.search(query)
    except ValueError:
        # no results
        results.append(InlineQueryResultArticle(
            title="No Such Videos Found!",
            description="Sorry! No Such Videos Were Found. Please Try Again",
            input_message_content=InputTextMessageContent(message_text="No Such Videos Found!")
        ))
        await inline_query.answer(results, switch_pm_text="Search Results", switch_pm_parameter="start")
        await backend.close()
        return
    except Exception:
        await inline_query.answer([], switch_pm_text="Search Results", switch_pm_parameter="start")
        await backend.close()
        return

    videos = getattr(src, "videos", []) or []
    await backend.close()

    for vid in videos:
        try:
            pornstars = ", ".join(v for v in vid.pornstars) if vid.pornstars else "N/A"
            categories = ", ".join(v for v in vid.categories) if vid.categories else "N/A"
            tags = ", #".join(v for v in vid.tags) if vid.tags else ""
        except Exception:
            pornstars = "N/A"
            categories = "N/A"
            tags = "N/A"

        msg = f"{vid.url}"
        results.append(InlineQueryResultArticle(
            title=vid.title,
            input_message_content=InputTextMessageContent(message_text=msg),
            description=f"Duration : {vid.duration}\nViews : {vid.views}\nRating : {vid.rating}",
            thumb_url=vid.thumb,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Watch online", url=vid.url),
                btn1
            ]]),
        ))

    await inline_query.answer(results, switch_pm_text="Search Results", switch_pm_parameter="start")


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user = message.from_user
    if user:
        add_user(user.id, user.username)
        await message.reply(
            f"Hello @{user.username if user.username else user.first_name},\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "I am the bot Who Search & download Pornhub Videos\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️Contains 18+ Content — Use at your own risk.\n"
            "━━━━━━━━━━━━━━━━━━━━