import os
import asyncio
import yt_dlp
import traceback
from telethon import TelegramClient, events, Button

# ================= CREDENTIALS =================
API_ID = 34848798
API_HASH = "210df233d07183ee955143092259dabb"
BOT_TOKEN = "8713743302:AAG4OVhU43PyoTvU5O5WSdfXZ1-jq5nPJc8"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = TelegramClient("ragini_music_bot", API_ID, API_HASH)

# ================= YT-DLP OPTIONS WITH COOKIES =================
def get_ydl_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "default_search": "ytsearch",
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
    }

# ================= SEARCH =================
def search_songs(query, limit=6):
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            results = []
            for entry in info.get("entries", []):
                if entry:
                    results.append({
                        "title": entry.get("title", "Unknown"),
                        "url": f"https://youtube.com/watch?v={entry['id']}",
                        "duration": entry.get("duration_string", "N/A"),
                        "channel": entry.get("uploader", "Unknown"),
                        "views": entry.get("view_count", "N/A"),
                    })
            return results
    except Exception as e:
        print(f"Search Error: {e}")
        return []

# ================= DOWNLOAD =================
async def download_audio_and_thumb(url, title):
    try:
        print(f"⬇️ Downloading: {title}")
        def _download():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "writethumbnail": True,
                "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                thumb = filename.rsplit(".", 1)[0] + ".webp"
                return filename, thumb if os.path.exists(thumb) else None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _download)
    except Exception as e:
        print(f"❌ Download Error: {e}")
        traceback.print_exc()
        return None, None

# ================= START =================
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    cookie_status = "✅ Cookies Loaded" if os.path.exists("cookies.txt") else "⚠️ cookies.txt not found (may get blocked)"
    await event.reply(f"""
╔════════════════════════════╗
       🌸 **RAGINI MUSIC** 🌸
╚════════════════════════════╝

**Ultra Premium Music Bot**

{cookie_status}

**Command:** `/play song name`

Made with 💖
    """)

# ================= /PLAY & BUTTON HANDLER (same as before) =================
@bot.on(events.NewMessage(pattern=r"/play(?:\s+(.+))?"))
async def play(event):
    query = event.pattern_match.group(1)
    if not query:
        return await event.reply("**Usage:** `/play song name`")

    msg = await event.reply("🌸 **Searching in Ragini Music...** ✨")

    results = search_songs(query)

    if not results:
        return await msg.edit("❌ **No results found!**\nTry different spelling.")

    buttons = []
    for i, song in enumerate(results):
        short = (song["title"][:35] + "…") if len(song["title"]) > 35 else song["title"]
        buttons.append([Button.inline(f"🎵 {short}", f"dl_{i}")])

    await msg.edit(
        f"**🌸 RAGINI MUSIC 🌸**\n\n**Results for:** `{query}`\n\n**Select song:**",
        buttons=buttons
    )

    if not hasattr(bot, "cache"):
        bot.cache = {}
    bot.cache[msg.id] = results

@bot.on(events.CallbackQuery())
async def callback(event):
    data = event.data.decode()
    if not data.startswith("dl_"):
        return

    index = int(data.split("_")[1])
    results = bot.cache.get(event.message_id)
    if not results or index >= len(results):
        return await event.answer("Search expired!", alert=True)

    song = results[index]
    status = await event.edit("⬇️ **Downloading...**")

    try:
        file_path, thumb_path = await download_audio_and_thumb(song["url"], song["title"])
        if not file_path:
            return await status.edit("❌ Download failed!")

        await status.edit("📤 **Uploading...**")

        caption = f"""
**🌸 RAGINI MUSIC 🌸**

**🎵 Title:** `{song['title']}`
**⏱ Duration:** `{song['duration']}`
**📺 Channel:** `{song['channel']}`

**Enjoy 💕**
        """.strip()

        await bot.send_file(
            event.chat_id,
            file=file_path,
            caption=caption,
            thumb=thumb_path,
            force_document=False
        )

        await status.delete()

        # Cleanup
        for f in [file_path, thumb_path]:
            if f and os.path.exists(f):
                os.remove(f)

    except Exception as e:
        await status.edit("❌ Download failed. Try again.")

# ================= RUN =================
async def main():
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ RAGINI MUSIC BOT STARTED!")
    print("Put cookies.txt in same folder for best results")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
