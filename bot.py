import os
import asyncio
import yt_dlp

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from youtubesearchpython import VideosSearch

from pytgcalls import GroupCallFactory


# ================= CONFIG =================

# ================= CONFIG =================

API_ID = 34848798

API_HASH = "210df233d07183ee955143092259dabb"

BOT_TOKEN = "8713743302:AAG4OVhU43PyoTvU5O5WSdfXZ1-jq5nPJc8"

SESSION_STRING = "BQITwB4ATkSfrgXp2qnil8weWS-7i_tFdD5pAN2sPX4BmZASg6oPYGdKt0IUQ7SjcqP-8UCW3RqsznyBYpAENw1ZJEkD5hAdd-epvTwVRkdei1Dfmw6FEh45Bm4If5XJZaq10Qot5aWa9yks9b0xQa7P9Ntb7EITWCk3OK1pszYifM_0Noe3VwSns7GhViOxm1PpWRtzb5vqY3mj9iqblOo62IQ8UGBZjYM7x7FbopQOKUOVmmSVEhr2KxK3chyda60EwjfE5PFltlBfGwZDVAm2pKQjeH_UBNxAnV2wgcEpzfWHGpYZisjUZqVi5Fag5IZ0PJhvwIjSMUwRiF3-_UAdu-NXpAAAAAGqkXGbAA"

DOWNLOAD_DIR = "downloads"

# =========================================

# =========================================

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

group_call = GroupCallFactory(
    client,
    GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON
).get_group_call()


# ================= SEARCH =================

def search_youtube(query):

    results = VideosSearch(query, limit=1).result()

    if not results["result"]:
        return None, None

    video = results["result"][0]

    return video["link"], video["title"]


# ================= DOWNLOAD =================

def download_audio(url):

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        return ydl.prepare_filename(info)


# ================= PLAY =================

@client.on(events.NewMessage(pattern=r"^/play (.+)"))
async def play_handler(event):

    query = event.pattern_match.group(1)

    msg = await event.reply("🔍 Searching...")

    try:

        if "youtube.com" in query or "youtu.be" in query:
            url = query
            title = "YouTube Audio"

        else:
            url, title = search_youtube(query)

            if not url:
                return await msg.edit("❌ Song not found")

        await msg.edit("⬇ Downloading...")

        loop = asyncio.get_event_loop()

        file_path = await loop.run_in_executor(
            None,
            download_audio,
            url
        )

        await msg.edit("📞 Joining VC...")

        await group_call.start(event.chat_id)

        group_call.input_filename = file_path

        await msg.edit(f"▶️ Playing:\n{title}")

    except Exception as e:
        await msg.edit(f"❌ Error:\n{str(e)}")


# ================= STOP =================

@client.on(events.NewMessage(pattern=r"^/stop$"))
async def stop_handler(event):

    try:

        await group_call.stop()

        await event.reply("⏹ Stopped")

    except Exception as e:
        await event.reply(str(e))


# ================= START =================

print("================================")
print(" VC MUSIC USERBOT STARTED ")
print("================================")

client.start()

client.run_until_disconnected()
