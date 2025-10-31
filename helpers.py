import asyncio
import threading
from pyrogram.errors.exceptions import MessageNotModified, FloodWait

def humanbytes(size):
    """Convert bytes to human readable form."""
    if not size:
        return ""
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"

async def _edit_msg_async(message, to_edit):
    try:
        await message.edit(to_edit)
    except MessageNotModified:
        pass
    except FloodWait as e:
        # wait the required time
        await asyncio.sleep(e.x)
    except Exception:
        pass

def edit_msg_threadsafe(message, to_edit):
    """
    This helper is safe to call from another thread (e.g. youtube-dl hooks).
    It schedules the coroutine on the running event loop.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # no running loop in this thread
        loop = None

    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(_edit_msg_async(message, to_edit), loop)
    else:
        # fallback: start a short-lived loop in a thread
        def _run():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(_edit_msg_async(message, to_edit))
            new_loop.close()
        threading.Thread(target=_run).start()

def download_progress_hook(d, message):
    """
    Hook used by downloader (yt-dlp / youtube-dl).
    d is the progress dict. message is a pyrogram Message object to edit.
    """
    status = d.get("status")
    if status == "downloading":
        downloaded = d.get("downloaded_bytes") or d.get("_speed_bytes") or 0
        current = d.get("_downloaded_bytes_str") or humanbytes(int(d.get("downloaded_bytes", 0)))
        total = d.get("_total_bytes_str") or d.get("_total_bytes_estimate_str") or "N/A"
        file_name = d.get("filename") or d.get("info_dict", {}).get("title", "N/A")
        eta = d.get("_eta_str", d.get("eta", "N/A"))
        percent = d.get("_percent_str") or f"{d.get('progress', 'N/A')}"
        speed = d.get("_speed_str") or d.get("_speed", "N/A")
        to_edit = (
            f"<b><u>Downloading File</u></b>\n"
            f"<b>File Name :</b> <code>{file_name}</code>\n"
            f"<b>File Size :</b> <code>{total}</code>\n"
            f"<b>Speed :</b> <code>{speed}</code>\n"
            f"<b>ETA :</b> <code>{eta}</code>\n"
            f"<b>Progress :</b> <code>{percent}</code>\n"
        )
        edit_msg_threadsafe(message, to_edit)
    elif status == "finished":
        # finished downloading
        to_edit = "<b>Download finished, uploading...</b>"
        edit_msg_threadsafe(message, to_edit)