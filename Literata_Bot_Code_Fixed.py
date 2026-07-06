"""
TARA THE CHAMELEON DISCORD BOT | DEVELOPED BY LITERATA CREATIVE TEAM CC2026 | Whoishezza. | itskirax
EMAIL TO NEWHEZZAMAULANA123@GMAIL.COM OR YOU CAN DM ME VIA DISCORD @Whoisezza._
"""

# ==============================================================================
# IMPORT LIBRARIES (Python Standard Library)
# ==============================================================================
import os
import sys
import asyncio
import re
import datetime
import random
import time
import math
from collections import defaultdict

# ==============================================================================
# THIRD PARTY LIBRARIES (external packages + their setup/initialization)
# ==============================================================================
import discord
import discord.ext.commands as commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import aiohttp
import urllib.parse
from discord.ext import tasks
from google import genai
import lyricsgenius
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import io
from PIL import Image, ImageDraw, ImageFont
from tara_brain import ask_tara

# --- Third-party client / service initialization ---
load_dotenv()
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY")
genius = lyricsgenius.Genius(GENIUS_API_KEY)
genius.verbose = False
genius.remove_section_headers = True

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    spotify_client = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
    )
else:
    spotify_client = None
    print("⚠️ SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET belum di-set di .env — Tara akan fallback ke tebak-judul (oEmbed) untuk link Spotify, dan TIDAK bisa import Playlist/Album Spotify secara penuh.")

# --- Discord bot instance & intents (tergantung dari discord/commands) ---

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='*', intents=intents)

# --- yt_dlp / FFmpeg third-party tool configuration ---

FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
YTDL_PLAYLIST_OPTIONS = {
    'format': 'bestaudio/best',
    'extract_flat': 'in_playlist',
    'quiet': True,
    'no_warnings': True,
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

FILTERS = {
    "normal": "-vn",
    "bassboost": "-vn -af bass=g=15,dynaudnorm=f=200",
    "8d": "-vn -af apulsator=hz=0.09",
    "nightcore": "-vn -af asetrate=48000*1.25,aresample=48000",
    "speedup": "-vn -af atempo=1.5",
    "pitchup": "-vn -af asetrate=48000*1.3,atempo=1/1.3,aresample=48000"
}

# ==============================================================================
# 3. GLOBAL CONFIGURATION & STATE (bot-specific constants/memory, not tied to one library)
# ==============================================================================

#MEMORY (RAM ONLY)
temp_vcs = {}
active_filters = {}
afk_users = {}
queues = {}
last_played_song = {}
user_xp = defaultdict(lambda: defaultdict(lambda: {"xp": 0, "level": 0, "last_message": 0.0}))

XP_COOLDOWN = 25      # jeda leveling per-detik menghindari spam
XP_MIN, XP_MAX = 15, 25, 30, 35, 40  # XP random yang didapat tiap kali chat (di luar masa cooldown)

# Ganti value None dengan ID Role asli di server Literata (misal: 123456789012345678)
LEVEL_ROLE_REWARDS = {
    5: 1362439447966388395,
    10: None,
    20: 1522902368616710265,
    30: None,
}

# ------------------------------------------------------------------------------
# NEW: STATE UNTUK VOTE-SKIP, PROGRESS LAGU (/nowplaying), & KARAOKE (/lyrics)
# ------------------------------------------------------------------------------
skip_votes = defaultdict(set)          # skip_votes[guild_id] = set of user_id yang udah vote skip lagu ini
song_start_time = {}                   # song_start_time[guild_id] = timestamp mulai lagu saat ini diputar
song_pause_offset = defaultdict(float) # total detik lagu di-pause (biar progress bar tetep akurat)
song_paused_at = {}                    # song_paused_at[guild_id] = timestamp waktu terakhir di-pause
karaoke_tasks = {}                     # karaoke_tasks[guild_id] = asyncio.Task loop update lirik karaoke

# NEW: STATE UNTUK /profile (RAM-only juga, sama kaya sistem leveling di atas)
user_bio = defaultdict(str)     
user_coins = defaultdict(int)   
loop_mode = defaultdict(lambda: "off")       
song_reactions = defaultdict(lambda: {"up": 0, "down": 0}) 

# ------------------------------------------------------------------------------
# SISTEM EVENT RUTIN TERJADWAL (malam curhat, movie night, turnamen, dll)
# RAM-only sama kayak fitur lain, jadi kalau bot restart jadwalnya harus di-/event create ulang.
# Zona waktu dipatok WIB (UTC+7) manual, ga pake zoneinfo biar ga tergantung tzdata OS.
# ------------------------------------------------------------------------------
WIB = datetime.timezone(datetime.timedelta(hours=7))
DAY_NAMES_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# scheduled_events[nama_key] = {
#   "title": str, "description": str, "day": int (0=Senin..6=Minggu), "time": "HH:MM",
#   "channel_id": int, "role_id": int|None, "guild_id": int,
#   "last_fired_date": "YYYY-MM-DD"|None, "last_reminder_date": "YYYY-MM-DD"|None,
#   "rsvp": set(),
# }
scheduled_events = {}

# SPAM TRACKER
spam_tracker = defaultdict(list)
SPAM_LIMIT = 5  # Maksimal 5 pesan
SPAM_TIME = 2   # dalam waktu 2 detik
SCAM_KEYWORDS = [
    "free nitro", "discord.gift", "steamcommunity-free",
    "steam-free", "hack discord", "click here to claim"
]

# CONFIGURATION / SETTING UTK FITUR CHANNEL & ROLE
VERIFICATION_CHANNEL_ID = """Taruh ID CHANNEL"""
RULES_CHANNEL_ID = """Taruh ID CHANNEL"""
VERIFICATION_MESSAGE_ID = """Taruh ID CHANNEL"""
UPDATE_CHANNEL_ID = """Taruh ID CHANNEL"""
VERIFIED_ROLE_ID = """Taruh ID CHANNEL"""
TARA_CHAT_CHANNEL_ID = """Taruh ID CHANNEL"""
HUB_VC_ID = """Taruh ID CHANNEL"""
STATUS_VC_ID = """Taruh ID CHANNEL"""
VERIFY_EMOJI = "✅"
ROLE_DEVELOPER_NAME = "Developer Literata"

# ==============================================================================
# helper functions/classes used by the command definitions below
# ==============================================================================
def get_ffmpeg_options(guild_id):
    filter_opt = active_filters.get(guild_id, FILTERS["normal"])
    return {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': filter_opt,
    }

# ------------------------------------------------------------------------------
# LEVELING HELPERS
# ------------------------------------------------------------------------------
def get_xp_needed(level):
    """Rumus XP yang dibutuhkan buat naik dari `level` ke level berikutnya (makin gede makin susah)."""
    return 5 * (level ** 2) + 50 * level + 100

def add_xp(guild_id, user_id, amount):
    """Nambahin XP ke satu user, otomatis naikin level kalau XP-nya udah cukup (bisa naik >1 level sekaligus)."""
    data = user_xp[guild_id][user_id]
    data["xp"] += amount
    leveled_up = False
    while data["xp"] >= get_xp_needed(data["level"]):
        data["xp"] -= get_xp_needed(data["level"])
        data["level"] += 1
        leveled_up = True
    return leveled_up, data["level"]

def _generate_rank_card_sync(avatar_bytes, username, level, rank_position, current_xp, xp_needed):
    """
    Fungsi BLOCKING (Pillow itu CPU-bound), makanya selalu dipanggil lewat
    asyncio.to_thread() di sisi caller-nya biar event loop bot ga ke-freeze.
    """
    W, H = 934, 282
    ACCENT = (30, 215, 96, 255)  # Hijau khas Tara

    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle([(0, 0), (W, H)], radius=30, fill=(24, 26, 27, 255))
    # Aksen hijau di sisi kiri
    draw.rounded_rectangle([(0, 0), (14, H)], radius=7, fill=ACCENT)

    # Avatar bulat
    avatar_size = 180
    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
    avatar_pos = (55, (H - avatar_size) // 2)
    base.paste(avatar_img, avatar_pos, mask)
    ring_box = [avatar_pos[0] - 4, avatar_pos[1] - 4, avatar_pos[0] + avatar_size + 4, avatar_pos[1] + avatar_size + 4]
    draw.ellipse(ring_box, outline=ACCENT, width=6)

    # Font (fallback ke default kalau font system nggak ketemu, biar tetap jalan di server manapun)
    try:
        font_big = ImageFont.truetype("arialbd.ttf", 46)
        font_med = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        try:
            font_big = ImageFont.load_default(size=46)
            font_med = ImageFont.load_default(size=26)
            font_small = ImageFont.load_default(size=20)
        except TypeError:
            font_big = font_med = font_small = ImageFont.load_default()

    text_x = avatar_pos[0] + avatar_size + 40
    draw.text((text_x, 55), username, font=font_big, fill=(255, 255, 255, 255))
    draw.text((text_x, 112), f"RANK #{rank_position}   •   LEVEL {level}", font=font_med, fill=(190, 190, 190, 255))

    # Progress bar XP
    bar_x, bar_y = text_x, 175
    bar_w, bar_h = W - bar_x - 55, 34
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], radius=17, fill=(55, 57, 59, 255))
    ratio = min(current_xp / xp_needed, 1.0) if xp_needed > 0 else 0
    fill_w = int(bar_w * ratio)
    if fill_w > 0:
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + max(fill_w, 34), bar_y + bar_h)], radius=17, fill=ACCENT)

    draw.text((bar_x, bar_y + bar_h + 8), f"{current_xp} / {xp_needed} XP", font=font_small, fill=(210, 210, 210, 255))

    buffer = io.BytesIO()
    base.convert("RGB").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

async def generate_rank_card(member: discord.Member, level, rank_position, current_xp, xp_needed):
    """Wrapper async: ambil avatar member lalu render kartu di thread terpisah."""
    avatar_bytes = await member.display_avatar.replace(size=256, format="png").read()
    buffer = await asyncio.to_thread(
        _generate_rank_card_sync,
        avatar_bytes,
        member.display_name,
        level,
        rank_position,
        current_xp,
        xp_needed,
    )
    return buffer

# ------------------------------------------------------------------------------
# HELPER UNTUK /profile (BADGE OTOMATIS)
# ------------------------------------------------------------------------------
def get_badges(member: discord.Member, level: int):
    """Kasih badge otomatis berdasarkan level & status member (booster/developer/dst)."""
    badges = []
    if ROLE_DEVELOPER_NAME in [r.name for r in member.roles]:
        badges.append("🛠️ Developer")
    if getattr(member, "premium_since", None):
        badges.append("💚 Booster")
    if level >= 30:
        badges.append("💎 Elite Member")
    elif level >= 20:
        badges.append("🥇 Veteran")
    elif level >= 10:
        badges.append("🥈 Aktif Banget")
    elif level >= 5:
        badges.append("🥉 Rajin Chat")
    if not badges:
        badges.append("🌱 Member Baru")
    return badges

# ------------------------------------------------------------------------------
# HELPER UNTUK PROGRESS LAGU (/nowplaying) & TRACKING WAKTU PUTAR
# ------------------------------------------------------------------------------
def get_elapsed_seconds(guild_id):
    """Hitung berapa detik lagu saat ini udah diputar, dikurangi total waktu di-pause."""
    if guild_id not in song_start_time:
        return 0
    if guild_id in song_paused_at:
        return max(0.0, song_paused_at[guild_id] - song_start_time[guild_id] - song_pause_offset[guild_id])
    return max(0.0, time.time() - song_start_time[guild_id] - song_pause_offset[guild_id])

def parse_duration_to_seconds(duration_str):
    """Ubah string durasi 'mm:ss' jadi total detik (int). Balikin 0 kalau formatnya aneh (misal 'In Queue')."""
    try:
        mins, secs = duration_str.split(":")
        return int(mins) * 60 + int(secs)
    except Exception:
        return 0

def build_progress_bar(elapsed, total, length=18):
    """Bikin progress bar visual pakai emoji buat dipasang di embed /nowplaying."""
    if total <= 0:
        return "▬" * length
    ratio = min(max(elapsed / total, 0), 1.0)
    filled = int(length * ratio)
    return ("🟩" * filled) + "⚪" + ("▬" * max(length - filled - 1, 0))

# ------------------------------------------------------------------------------
# HELPER UNTUK /lyrics MODE KARAOKE (LIRIK SINKRON)
# ------------------------------------------------------------------------------
LRCLIB_API = "https://lrclib.net/api/get"  # API publik gratis, nggak butuh API key
LRC_LINE_PATTERN = re.compile(r"\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\](.*)")

def parse_lrc(lrc_text):
    """Parse teks format LRC (`[mm:ss.xx] lirik`) jadi list [(detik, teks), ...] terurut waktu."""
    hasil = []
    for raw_line in lrc_text.splitlines():
        m = LRC_LINE_PATTERN.match(raw_line.strip())
        if not m:
            continue
        minute, second, ms, text = m.groups()
        total_secs = int(minute) * 60 + int(second) + (int(ms.ljust(3, "0")) / 1000 if ms else 0)
        text = text.strip()
        if text:
            hasil.append((total_secs, text))
    hasil.sort(key=lambda x: x[0])
    return hasil

async def fetch_synced_lyrics(title, artist, duration_secs):
    """
    Coba ambil lirik SINKRON (per-detik, format LRC) dari lrclib.net.
    Balikin None kalau nggak ketemu, biar caller bisa fallback ke lirik biasa (Genius).
    """
    try:
        params = {"track_name": title or "", "artist_name": artist or "", "duration": int(duration_secs or 0)}
        async with aiohttp.ClientSession() as session:
            async with session.get(LRCLIB_API, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                synced = data.get("syncedLyrics")
                if not synced:
                    return None
                return parse_lrc(synced)
    except Exception:
        return None

async def run_karaoke(interaction, guild_id, lines, message):
    """
    Loop background yang update embed tiap ~2 detik, nunjukin baris lirik yang cocok
    dengan waktu lagu berjalan saat ini. Auto berhenti kalau lagu abis/ganti/di-stop,
    atau kalau udah lebih dari 10 menit (jaga-jaga biar ga infinite loop).
    """
    MAX_DURATION = 600
    start_loop = time.time()
    last_index = -2
    try:
        while time.time() - start_loop < MAX_DURATION:
            voice_client = interaction.guild.voice_client
            if not voice_client or not (voice_client.is_playing() or voice_client.is_paused()):
                break

            elapsed = get_elapsed_seconds(guild_id)
            idx = -1
            for i, (t, _) in enumerate(lines):
                if t <= elapsed:
                    idx = i
                else:
                    break

            if idx != last_index:
                last_index = idx
                current_line = lines[idx][1] if idx >= 0 else "🎵 *(Instrumental...)*"
                next_line = lines[idx + 1][1] if 0 <= idx + 1 < len(lines) else "..."
                embed = discord.Embed(
                    title="🎤 Mode Karaoke",
                    description=f"### ▶️ {current_line}\n-# ⏭️ {next_line}",
                    color=discord.Color.from_rgb(30, 215, 96)
                )
                embed.set_footer(text="Lirik auto-update ngikutin lagu | Tara Karaoke Mode")
                try:
                    await message.edit(embed=embed)
                except discord.NotFound:
                    break

            await asyncio.sleep(2)
    except asyncio.CancelledError:
        pass
    finally:
        karaoke_tasks.pop(guild_id, None)

def stop_karaoke_task(guild_id):
    """Hentiin task karaoke yang lagi jalan buat guild ini (dipanggil pas skip/stop/ganti lagu)."""
    task = karaoke_tasks.pop(guild_id, None)
    if task and not task.done():
        task.cancel()

# ------------------------------------------------------------------------------
# NEW: HELPER UI NOW PLAYING MODERN (progress bar bergaya slider ala Flavy Bot, dibikin pakai Pillow)
# ------------------------------------------------------------------------------
def _load_ui_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

def _generate_progress_image_sync(elapsed_secs, total_secs):
    """Bikin gambar slider progress (track abu-abu + isi hijau + knob bulat) mirip UI player modern."""
    W, H = 900, 90
    ACCENT = (30, 215, 96, 255)
    TRACK_BG = (70, 72, 74, 255)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bar_y, bar_h = 32, 10
    bar_x0, bar_x1 = 12, W - 12
    draw.rounded_rectangle([(bar_x0, bar_y), (bar_x1, bar_y + bar_h)], radius=5, fill=TRACK_BG)

    ratio = min(elapsed_secs / total_secs, 1.0) if total_secs > 0 else 0.0
    knob_x = bar_x0 + int((bar_x1 - bar_x0) * ratio)
    if knob_x > bar_x0:
        draw.rounded_rectangle([(bar_x0, bar_y), (knob_x, bar_y + bar_h)], radius=5, fill=ACCENT)

    knob_r = 10
    knob_cy = bar_y + bar_h // 2
    draw.ellipse(
        [knob_x - knob_r, knob_cy - knob_r, knob_x + knob_r, knob_cy + knob_r],
        fill=(255, 255, 255, 255), outline=ACCENT, width=3
    )

    font = _load_ui_font(24)

    def fmt(t):
        m, s = divmod(int(max(t, 0)), 60)
        return f"{m}:{s:02d}"

    draw.text((bar_x0, bar_y + bar_h + 14), fmt(elapsed_secs), font=font, fill=(210, 210, 210, 255))
    total_text = fmt(total_secs)
    bbox = draw.textbbox((0, 0), total_text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((bar_x1 - tw, bar_y + bar_h + 14), total_text, font=font, fill=(210, 210, 210, 255))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

async def generate_progress_image(elapsed_secs, total_secs):
    """Wrapper async: render slider progress di thread terpisah (Pillow itu blocking/CPU-bound)."""
    return await asyncio.to_thread(_generate_progress_image_sync, elapsed_secs, total_secs)

#SPOTIFY HELPER: Ambil metadata track/playlist/album Spotify lewat Spotify Web API.
#Spotify nggak ngasih audio streaming publik, jadi tiap track hasil Spotify tetap
#"dicariin" video yang cocok di YouTube pas giliran diputar (lewat process_next_song).
SPOTIFY_URL_PATTERN = re.compile(r"open\.spotify\.com/(?:intl-[a-zA-Z-]+/)?(track|album|playlist)/([a-zA-Z0-9]+)")

def _spotify_track_to_dict(track, fallback_thumbnail=None):
    if not track:
        return None
    artists = ", ".join(a.get('name', '') for a in track.get('artists', []) if a.get('name'))
    images = (track.get('album') or {}).get('images') or []
    thumbnail = images[0]['url'] if images else fallback_thumbnail
    return {
        'title': track.get('name') or 'Unknown Title',
        'artist': artists,
        'thumbnail': thumbnail,
        'webpage': (track.get('external_urls') or {}).get('spotify')
    }

def _fetch_spotify_tracks_sync(link_type, spotify_id):
    """Panggilan blocking ke Spotify Web API. Dijalankan lewat asyncio.to_thread agar tidak nge-block event loop bot."""
    MAX_TRACKS = 200  # batas aman biar nggak nyedot playlist raksasa (nanti dipotong lagi jadi 140 di /play)

    if link_type == "track":
        track = spotify_client.track(spotify_id)
        hasil = _spotify_track_to_dict(track)
        return [hasil] if hasil else []

    if link_type == "album":
        tracks = []
        album = spotify_client.album(spotify_id)
        album_art = album['images'][0]['url'] if album.get('images') else None
        results = spotify_client.album_tracks(spotify_id)
        while results:
            for item in results.get('items', []):
                converted = _spotify_track_to_dict(item, fallback_thumbnail=album_art)
                if converted:
                    tracks.append(converted)
                if len(tracks) >= MAX_TRACKS:
                    return tracks
            results = spotify_client.next(results) if results.get('next') else None
        return tracks

    if link_type == "playlist":
        tracks = []
        results = spotify_client.playlist_items(spotify_id, additional_types=['track'])
        while results:
            for item in results.get('items', []):
                converted = _spotify_track_to_dict(item.get('track'))
                if converted:
                    tracks.append(converted)
                if len(tracks) >= MAX_TRACKS:
                    return tracks
            results = spotify_client.next(results) if results.get('next') else None
        return tracks

    return []

async def expand_spotify_short_link(url: str) -> str:
    """
    NEW: Kalau url berupa short-link (spotify.link, atau redirect apapun), ikutin redirect-nya
    dulu buat dapetin URL asli open.spotify.com/track|album|playlist/... .
    Kalau gagal/timeout, balikin url apa adanya (biar tetap fallback ke oEmbed).
    """
    if "open.spotify.com" in url:
        return url
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                return str(resp.url)
    except Exception:
        return url

async def resolve_spotify_url(url):
    """
    Mengembalikan list of dict [{'title', 'artist', 'thumbnail', 'webpage'}, ...] untuk
    track/playlist/album Spotify. Mengembalikan None kalau Spotify client belum di-setup
    (SPOTIFY_CLIENT_ID/SECRET kosong) atau linknya gagal diproses, supaya pemanggil bisa
    fallback ke metode oEmbed (tebak judul doang).
    """
    if spotify_client is None:
        return None

    match = SPOTIFY_URL_PATTERN.search(url)
    if not match:
        # NEW: mungkin ini short-link (spotify.link dll), coba expand dulu sebelum nyerah
        expanded_url = await expand_spotify_short_link(url)
        match = SPOTIFY_URL_PATTERN.search(expanded_url)
        if not match:
            return None

    link_type, spotify_id = match.group(1), match.group(2)
    try:
        return await asyncio.to_thread(_fetch_spotify_tracks_sync, link_type, spotify_id)
    except Exception as e:
        print(f"❌ Gagal mengambil data Spotify: {e}")
        return None

#DISCORD UI
def resolve_flat_entry_url(entry, source_url=""):
    """
    NEW FIX (playlist import YouTube/SoundCloud):
    yt_dlp dengan 'extract_flat' (dipakai biar loading playlist gede tetep cepet) itu
    SERING cuma ngasih ID doang di field 'url' (bukan link penuh), khususnya buat YouTube.
    Kalau ID doang ini dikirim balik ke yt_dlp pas resolve ulang di process_next_song(),
    yt_dlp bakal nganggep itu SEARCH TERM (bukan URL valid, gara-gara 'default_search': 'auto')
    dan hasilnya sering gagal extract atau malah nyangkut ke lagu lain.
    Makanya di sini query DIPAKSA jadi URL penuh dulu sebelum masuk queue.
    """
    raw = entry.get('webpage_url') or entry.get('url') or ""
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw

    video_id = entry.get('id') or raw
    if "youtube.com" in source_url or "youtu.be" in source_url:
        return f"https://www.youtube.com/watch?v={video_id}"
    if "soundcloud.com" in source_url:
        # SoundCloud biasanya udah kasih webpage_url penuh di flat entry,
        # tapi kalau ternyata cuma ID doang, fallback nyari pakai judulnya
        # biar lagu tetep ketemu (walau lewat pencarian, bukan link exact).
        return f"ytsearch:{entry.get('title', video_id)}"
    return f"ytsearch:{entry.get('title', video_id)}"


def resolve_flat_entry_thumbnail(entry):
    """
    NEW FIX: entry hasil 'extract_flat' biasanya nyimpen gambar di list 'thumbnails'
    (bukan key 'thumbnail' tunggal), jadi thumbnail suka nggak muncul di embed queue.
    """
    if entry.get('thumbnail'):
        return entry.get('thumbnail')
    thumbs = entry.get('thumbnails') or []
    if thumbs:
        return thumbs[-1].get('url')
    return None


async def process_next_song(interaction, guild_id):
    voice_client = interaction.guild.voice_client
    if not voice_client:
        return

    # NEW: Bersihin state lagu sebelumnya (vote skip, timer progress, karaoke)
    stop_karaoke_task(guild_id)
    skip_votes[guild_id] = set()
    song_pause_offset[guild_id] = 0.0
    song_paused_at.pop(guild_id, None)

    # NEW: Mode "Loop Lagu Ini" -> masukin lagu yg baru aja abis diputar balik ke depan antrean.
    # Query di-resolve ULANG (bukan reuse stream url lama) soalnya link streaming YouTube/dll
    # itu ada masa berlakunya (signed URL), jadi kalau dipakai ulang bisa gagal/expired.
    if loop_mode.get(guild_id) == "song" and guild_id in last_played_song:
        prev_song = last_played_song[guild_id]
        requeue_song = dict(prev_song)
        requeue_song['is_resolved'] = False
        requeue_song['query'] = prev_song.get('query') or prev_song.get('webpage') or prev_song.get('title')
        queues.setdefault(guild_id, []).insert(0, requeue_song)

    if guild_id in queues and len(queues[guild_id]) > 0:
        next_song = queues[guild_id].pop(0)
        if not next_song.get('is_resolved'):
            try:
                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                    info = await asyncio.to_thread(ydl.extract_info, next_song['query'], download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    stream_url = info['url']
                    next_song['title'] = info.get('title', next_song['title'])
                    next_song['webpage'] = info.get('webpage_url', next_song['webpage'])
                    next_song['thumbnail'] = info.get('thumbnail', next_song['thumbnail'])

                    # FIX: Durasi dipaksa menjadi Integer sebelum divmod agar bebas dari bug 'float'
                    mins, secs = divmod(int(info.get('duration', 0)), 60)
                    next_song['duration'] = f"{mins}:{secs:02d}"
            except Exception as e:
                await interaction.channel.send(f"❌ Gagal memproses lagu berikutnya: `{next_song['title']}`. Melompati...")
                interaction.client.loop.create_task(process_next_song(interaction, guild_id))
                return
        else:
            stream_url = next_song['url']

        source = discord.FFmpegPCMAudio(stream_url, **get_ffmpeg_options(guild_id))
        voice_client.current_song = next_song['title']

        # NEW: Simpan info lagu & mulai hitung waktu buat /nowplaying, /lyrics karaoke, dan vote-skip
        last_played_song[guild_id] = next_song
        song_start_time[guild_id] = time.time()

        def after_playing(error):
            interaction.client.loop.create_task(process_next_song(interaction, guild_id))

        voice_client.play(source, after=after_playing)

        platform_name = next_song.get('platform', 'YouTube')
        if platform_name == "Spotify":
            embed_color, icon = discord.Color.from_rgb(30, 215, 96), "💚"
        elif platform_name == "SoundCloud":
            embed_color, icon = discord.Color.from_rgb(255, 85, 0), "☁️"
        else:
            embed_color, icon = discord.Color.from_rgb(231, 76, 60), "🔴"

        # NEW: UI Now Playing didesain ulang, terinspirasi tampilan modern (bullet list + slider progress bar)
        voice_channel_name = voice_client.channel.name if voice_client.channel else "Voice Channel"
        loop_label = "Lagu Ini 🔁" if loop_mode.get(guild_id) == "song" else "Off"

        embed_next = discord.Embed(
            title=f"{icon} Now Playing",
            description=(
                f"### {next_song['title']}\n"
                f"• Added by {next_song['user'].mention}\n"
                f"• 🔊 {voice_channel_name}"
            ),
            color=embed_color,
            url=next_song.get('webpage') or None
        )
        embed_next.add_field(
            name="\u200b",
            value=f"Queue Size: `{len(queues[guild_id])}` • Loop: `{loop_label}` • Platform: `{platform_name}`",
            inline=False
        )

        if next_song['thumbnail']:
            embed_next.set_thumbnail(url=next_song['thumbnail'])

        total_secs = parse_duration_to_seconds(next_song['duration'])
        progress_buf = await generate_progress_image(0, total_secs)
        progress_file = discord.File(fp=progress_buf, filename="tara_progress.png")
        embed_next.set_image(url="attachment://tara_progress.png")

        await interaction.channel.send(embed=embed_next, file=progress_file, view=MusicControls())
    else:
        if voice_client:
            voice_client.current_song = None
        last_played_song.pop(guild_id, None)
        song_start_time.pop(guild_id, None)

# ------------------------------------------------------------------------------
# NEW: LOGIKA VOTE-SKIP (dipakai bareng oleh tombol "Vote Skip" & slash command /skip)
# Tujuannya biar ga sembarang orang bisa skip lagu punya orang lain seenaknya.
# Moderator/Dev tetep bisa instant-skip kalau kepepet (misal lagu error/nyangkut).
# ------------------------------------------------------------------------------
async def process_skip_vote(interaction: discord.Interaction):
    """Return (skipped: bool, pesan: str)."""
    voice_client = interaction.guild.voice_client
    guild_id = interaction.guild.id

    if not voice_client or not (voice_client.is_playing() or voice_client.is_paused()):
        return False, "❌ Ga ada lagu yang lagi diputar mang!"

    if not interaction.user.voice or interaction.user.voice.channel != voice_client.channel:
        return False, "❌ Kamu harus ada di Voice Channel yang sama kaya Tara buat nge-vote skip!"

    # Moderator/Dev boleh instant-skip, sisanya harus lewat voting
    is_privileged = (
        interaction.user.guild_permissions.manage_channels
        or interaction.user.guild_permissions.administrator
        or ROLE_DEVELOPER_NAME in [r.name for r in interaction.user.roles]
    )
    if is_privileged:
        skip_votes[guild_id] = set()
        voice_client.stop()
        return True, "⏭️ Skip instan oleh Moderator/Dev!"

    listeners = [m for m in voice_client.channel.members if not m.bot]
    total_listeners = len(listeners) or 1
    needed = max(1, math.ceil(total_listeners / 2))

    votes = skip_votes[guild_id]
    if interaction.user.id in votes:
        return False, f"Kamu udah vote duluan tadi! (`{len(votes)}/{needed}` suara terkumpul)"

    votes.add(interaction.user.id)
    if len(votes) >= needed:
        skip_votes[guild_id] = set()
        voice_client.stop()
        return True, f"⏭️ Vote Skip berhasil (`{needed}/{needed}` suara)! Lagu dilewati~"
    else:
        return False, f"🗳️ Vote skip tercatat! (`{len(votes)}/{needed}` suara dibutuhkan buat skip lagu ini)"

class MusicControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.primary, emoji="⏯️", row=0)
    async def pause_resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild.id
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            song_paused_at[guild_id] = time.time()  # NEW: bekukan progress bar pas di-pause
            await interaction.response.send_message("⏸️ Musik Tara stop.", ephemeral=True)
        elif voice_client and voice_client.is_paused():
            voice_client.resume()
            if guild_id in song_paused_at:  # NEW: catat total durasi pause biar progress bar tetep akurat
                song_pause_offset[guild_id] += time.time() - song_paused_at.pop(guild_id)
            await interaction.response.send_message("▶️ Musik Tara lanjutin.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Tidak ada musik yang sedang diputar.", ephemeral=True)

    @discord.ui.button(label="Vote Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", row=0)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        skipped, pesan = await process_skip_vote(interaction)
        await interaction.response.send_message(pesan, ephemeral=not skipped)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild.id
        if guild_id in queues:
            queues[guild_id].clear()
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            stop_karaoke_task(guild_id)  # NEW: matiin karaoke kalau lagi jalan
            voice_client.stop()
            await interaction.response.send_message("🛑 Lagu dihentikan dan daftar antrian udah Tara hapus!", ephemeral=True)
        else:
            await interaction.response.send_message("Tara sedang tidak memutar lagu apapun...", ephemeral=True)

    # NEW: Tombol Loop (toggle "Off" <-> "Lagu Ini"), gantiin slot AutoPlay di referensi UI
    # (AutoPlay & Dashboard di screenshot referensi belum bisa dibikin krn butuh fitur/website
    # baru yang belum ada di Tara, jadi diganti fitur yang beneran jalan: Loop & reaksi lagu)
    @discord.ui.button(label="Loop: Off", style=discord.ButtonStyle.secondary, emoji="🔁", row=0)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        new_mode = "off" if loop_mode.get(guild_id) == "song" else "song"
        loop_mode[guild_id] = new_mode
        button.label = "Loop: Lagu Ini" if new_mode == "song" else "Loop: Off"
        await interaction.response.edit_message(view=self)

    # NEW: Reaksi Like/Dislike per lagu (tally-nya ditampilin di embed, mirip "Love this / Not for me")
    @discord.ui.button(label="Love this", style=discord.ButtonStyle.secondary, emoji="👍", row=1)
    async def like_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._react_song(interaction, "up")

    @discord.ui.button(label="Not for me", style=discord.ButtonStyle.secondary, emoji="👎", row=1)
    async def dislike_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._react_song(interaction, "down")

    async def _react_song(self, interaction: discord.Interaction, jenis: str):
        guild_id = interaction.guild.id
        song = last_played_song.get(guild_id)
        if not song:
            await interaction.response.send_message("❌ Ga ada lagu yang lagi diputar buat di-reaksi.", ephemeral=True)
            return

        key = song.get('webpage') or song.get('title')
        song_reactions[key][jenis] += 1
        tally = song_reactions[key]
        reaksi_text = f"👍 `{tally['up']}`   👎 `{tally['down']}`"

        if interaction.message.embeds:
            embed = interaction.message.embeds[0]
            found = False
            for i, f in enumerate(embed.fields):
                if f.name == "Reaksi":
                    embed.set_field_at(i, name="Reaksi", value=reaksi_text, inline=True)
                    found = True
                    break
            if not found:
                embed.add_field(name="Reaksi", value=reaksi_text, inline=True)
            await interaction.response.edit_message(embed=embed)
        else:
            await interaction.response.send_message("✅ Makasih feedback-nya!", ephemeral=True)

async def set_bot_status():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.CustomActivity(name=f"✨Literata ID Community✨")
    )
    for guild in bot.guilds:
        channel_status = guild.get_channel(STATUS_VC_ID)
        if channel_status and isinstance(channel_status, discord.VoiceChannel):
            try:
                nama_baru = f"👥 Total Member: {guild.member_count}"
                if channel_status.name != nama_baru:
                    await channel_status.edit(name=nama_baru)
            except Exception as e:
                print(f"❌ Gagal memperbarui nama channel status di {guild.name}: {e}")

@tasks.loop(minutes=5)
async def update_status():
    await set_bot_status()

async def check_vc_owner(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ Kamu harus berada di dalam Voice Channel dulu!", ephemeral=True)
        return None

    vc = interaction.user.voice.channel

    if vc.id not in temp_vcs or temp_vcs[vc.id] != interaction.user.id:
        await interaction.response.send_message("❌ Hush! Kamu bukan pemilik ruangan ini, jadi nggak bisa ngatur-ngatur!", ephemeral=True)
        return None
    return vc

# ==============================================================================
# 5. COMMAND DEFINITIONS (slash commands, command groups, and event listeners)
# ==============================================================================

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        afk_users.pop(message.author.id)
        await message.channel.send(f"Yeyy {message.author.mention} Uda bangun.")

    for user in message.mentions:
        if user.id in afk_users:
            await message.channel.send(f"💤 Shh...**{user.display_name}** Lagi AFK\n**Alasan:** {afk_users[user.id]}")
            return

    if "tara" in message.content.lower():
        async with message.channel.typing():
             await ask_tara(message.content) #Jawaban Tara nanti
        return

    konten_chat = message.content.lower()
    for scam_word in SCAM_KEYWORDS:
        if scam_word in konten_chat:
            await message.delete()
            await message.channel.send(f"🚨 **LITERATA SECURITY SYSTEM** 🚨\nHush {message.author.mention}! Jangan kirim link Scam/Phishing!", delete_after=5)
            return

    # ============= NEW: SISTEM XP & LEVELING (sementar hanya RAM only) =============
    if message.guild is not None and not message.content.startswith(bot.command_prefix):
        guild_id = message.guild.id
        user_id = message.author.id
        now_ts = time.time()
        xp_data = user_xp[guild_id][user_id]
        if now_ts - xp_data.get("last_message", 0) >= XP_COOLDOWN:
            xp_data["last_message"] = now_ts
            xp_gain = random.randint(XP_MIN, XP_MAX)
            leveled_up, new_level = add_xp(guild_id, user_id, xp_gain)
            if leveled_up:
                embed_levelup = discord.Embed(
                    description=f"🎉 Selamat {message.author.mention}, kamu naik ke **Level {new_level}**! 🦎✨",
                    color=discord.Color.from_rgb(30, 215, 96)
                )
                role_id = LEVEL_ROLE_REWARDS.get(new_level)
                if role_id:
                    role = message.guild.get_role(role_id)
                    if role:
                        try:
                            await message.author.add_roles(role, reason=f"Reward otomatis naik ke Level {new_level}")
                            embed_levelup.add_field(name="🎁 Role Reward", value=f"Kamu dapet role {role.mention}!", inline=False)
                        except Exception as e:
                            print(f"❌ Gagal kasih role reward level {new_level}: {e}")
                try:
                    await message.channel.send(embed=embed_levelup)
                except Exception:
                    pass

    if "pagi" in konten_chat or "morning" in konten_chat:
        await message.channel.send(f"Morningg! Udah pada mandi belom nih? wangi pengangguran nya masih kecium sampai sini tau... {message.author.mention}")
    elif "sepi" in konten_chat:
        await message.channel.send(f"Makanya pada open mic dong {message.author.mention}, jangan di pojokan mulu napa..")
    elif "malam" in konten_chat or "malem" in konten_chat:
        await message.channel.send(f"Hoamm, malam juga... Jangan begadang terus yaa...")
    elif "login" in konten_chat or "login valo" in konten_chat:
        await message.channel.send("Login? Gendong Tara dongg, biar tara cepet immo :3")
    elif "goblok" in konten_chat or "tolol" in konten_chat:
        await message.channel.send("Eh, kata Kak Hani, jangan maki-maki orang!")
    elif "bangsat" in konten_chat or "tai" in konten_chat:
        await message.channel.send("Lah marah-marah mulu loh ni orang...")
    elif "anjing" in konten_chat or "bangsat" in konten_chat:
        await message.channel.send("Astaghfirullah, min liat dia min...")
    elif "Tara versi berapa ya sekarang?" in konten_chat:
        await message.channel.send("Tara sudah update ke versi 2.5!!")

    if bot.user.mentioned_in(message) and not message.mention_everyone:
        respon_mention = [
            "Paan nge-tag Tara? Kangen ya?",
            "Hadirr! 🦎",
            "Lagi sibuk nyari serangga nih, bentar ya.",
            "Berisik ih, Tara lagi tidur...💤",
            "Pake `/help` aja kalau mau tau apa aja yang Tara bisa lakuin!",
            "Haii? Ada apa nih ngetag Tara ya? kalau ada perlu bisa lewat '/' yaa!"
        ]
        await message.channel.send(random.choice(respon_mention))
    user_id = message.author.id
    now = time.time()
    spam_tracker[user_id] = [t for t in spam_tracker[user_id] if now - t < SPAM_TIME]
    spam_tracker[user_id].append(now)

    if len(spam_tracker[user_id]) > SPAM_LIMIT:
        await message.delete()
        try:
            durasi = discord.utils.utcnow() + datetime.timedelta(minutes=5)
            await message.author.timeout(durasi, reason="Spamming Chat")
            await message.channel.send(f"🔇 **{message.author.mention} di-mute 5 menit karena Spamming.**", delete_after=15)
        except Exception:
            pass
        spam_tracker[user_id].clear()
        return
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"🤖 Tara Sudah Ready! Waiting for commands...")
    await set_bot_status()
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Berhasil menyinkronkan {len(synced)} global slash commands.")
    except Exception as e:
        print(f"❌ Gagal sinkronisasi command: {e}")
    if not update_status.is_running():
        update_status.start()
    if not event_scheduler_loop.is_running():  # NEW: mulai loop pengecekan jadwal event rutin
        event_scheduler_loop.start()

@bot.event
async def on_member_join(member):
    WELCOME_CHANNEL_ID = 1522218769387360266
    GIF_URL = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3lxYTc0eHJzZjByYTdvc3NmZ2gyOHlsNGF5bHZ3NXYydnhoejlkayZlcD12MV9naWZzX3NlYXJjaCZjdD1n/YhFzQw0j4lPNu/giphy.gif"
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🚀 Eh ada yang ngetok pintu, bentar ya Tara bukain!",
            description=f"Selamat datang {member.mention} di **Literata Community!!**!\n\nSemoga betah nongkrong di sini yaa!!.\n\n Jangan lupa baca rules di {member.guild.get_channel(RULES_CHANNEL_ID).mention} dan klik emoji ✅ di {member.guild.get_channel(VERIFICATION_CHANNEL_ID).mention} untuk verifikasi. \n\nSelamat bersenang-senang di server Literata Community! link permanent server: https://discord.gg/8v7J2k6y",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=GIF_URL)
        embed.set_footer(text=f"Anggota Literata ke-{len(member.guild.members)}", icon_url=member.guild.icon.url if member.guild.icon else None)
        await channel.send(content=f"Halo {member.mention}, selamat datang!", embed=embed)
    await set_bot_status()

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.message_id == VERIFICATION_MESSAGE_ID:
        if str(payload.emoji) == VERIFY_EMOJI:
            guild = bot.get_guild(payload.guild_id)
            if guild is None: return
            role = guild.get_role(VERIFIED_ROLE_ID)
            member = guild.get_member(payload.user_id)
            if member and role and not member.bot:
                await member.add_roles(role)
                try:
                    await member.send(f"🎉 Kamu baru saja tara verifikasi di **{guild.name}** dan mendapatkan role **{role.name}**!")
                except discord.Forbidden:
                    pass

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.message_id == VERIFICATION_MESSAGE_ID:
        if str(payload.emoji) == VERIFY_EMOJI:
            guild = bot.get_guild(payload.guild_id)
            if guild is None: return
            role = guild.get_role(VERIFIED_ROLE_ID)
            member = guild.get_member(payload.user_id)
            if member and role and not member.bot:
                await member.remove_roles(role)

#FUNCTION DISINI UNTUK COMMAND BASIC (/hai, /ping, /clear, /setup-verify, /setup rules, dst.)
# ------------------------------------------------------------------------------
# BASIC / UTILITY COMMANDS (/hai, /ping, /clear)
# ------------------------------------------------------------------------------

@bot.tree.command(name="hai", description="Bot akan menyapamu dengan ramah")
async def halo(interaction: discord.Interaction):
    await interaction.response.send_message(f"Awoo! {interaction.user.mention}! Tara Hadir!!!")

@bot.tree.command(name="ping", description="Cek kecepatan respon bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong {latency}ms")

@bot.tree.command(name="clear", description="Menghapus sejumlah pesan di channel ini")
@app_commands.default_permissions(administrator=True)
async def clear(interaction: discord.Interaction, jumlah: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=jumlah)
    await interaction.followup.send(f"🧹 Berhasil menghapus {len(deleted)} pesan!", ephemeral=True)

# ------------------------------------------------------------------------------
# SERVER SETUP COMMANDS (Khusus Admin: pesan verifikasi & rules otomatis)
# ------------------------------------------------------------------------------

@bot.tree.command(name="setup-verify", description="Membuat pesan verifikasi otomatis dari bot (Khusus Admin)")
@app_commands.default_permissions(administrator=True)
async def setup_verify(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = interaction.guild.get_channel(VERIFICATION_CHANNEL_ID)
    if not channel:
        await interaction.followup.send("❌ Channel verifikasi tidak ditemukan!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🚪 Gerbang Masuk Literata Community",
        description=(
            "**Halo, calon warga Literata!** 👋\n\n"
            "Kamu udah sampai di depan pintu — cuma satu langkah kecil lagi buat resmi "
            "jadi bagian dari komunitas ini. Gampang banget, kok!\n\n"
            "Klik reaksi **✅** tepat di bawah pesan ini, dan *voilà* — semua channel "
            "bakal terbuka buat kamu jelajahi. Tara udah nunggu di dalam~ 🦎💚"
        ),
        color=discord.Color.from_rgb(46, 204, 113)
    )
    embed.add_field(
        name="✅ Langkah Verifikasi",
        value="Klik reaksi di bawah pesan ini",
        inline=True
    )
    embed.add_field(
        name="🔓 Hasilnya",
        value="Akses ke seluruh channel server",
        inline=True
    )
    embed.set_footer(text="Butuh bantuan? Panggil aja Admin/Mod yang lagi online 🌿")
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    pesan_verif = await channel.send(embed=embed)
    await pesan_verif.add_reaction("✅")
    await interaction.followup.send(f"✅ Sukses dikirim ke {channel.mention}! ID Pesan: `{pesan_verif.id}`", ephemeral=True)

@bot.tree.command(name="setup-rules", description="Membuat pesan peraturan server otomatis (Khusus Admin)")
@app_commands.default_permissions(administrator=True)
async def setup_rules(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = interaction.guild.get_channel(RULES_CHANNEL_ID)
    if not channel:
        await interaction.followup.send("❌ Channel rules tidak ditemukan!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🦎 Panduan Nyaman Literata Community",
        description=(
            "Halo, member baru~ Sebelum kamu mulai jelajah tiap sudut server ini, "
            "yuk kenalan dulu sama beberapa *ground rules* kita. Tenang aja, ini bukan "
            "buku undang-undang negara yang bikin pusing — cuma beberapa kesepakatan simpel biar "
            "Literata tetep jadi tempat yang nyaman buat semua orang. 💚"
        ),
        color=discord.Color.from_rgb(30, 215, 96)
    )

    embed.add_field(
        name="1️⃣ Saling Menghargai",
        value=">>> Beda pendapat itu wajar, tapi nggak perlu jadi drama. No SARA, no bullying, no ujaran kebencian. Perlakuan orang lain sesuai kamu pengen diperlakukan gimana.",
        inline=False
    )
    embed.add_field(
        name="2️⃣ Konten & Channel yang Pas",
        value=">>> Setiap channel punya 'rumahnya' sendiri — pakai sesuai fungsinya ya, biar obrolan nggak numpuk berantakan dan gampang dicari lagi nanti.",
        inline=False
    )
    embed.add_field(
        name="3️⃣ Bijak Ber-Promosi & Anti-Spam",
        value=">>> Boleh sesekali share sesuatu yang seru, tapi hindari spam link/promosi bertubi-tubi tanpa izin admin. Nggak enak kan kalau chat jadi lautan iklan?",
        inline=False
    )
    embed.add_field(
        name="4️⃣ Zona Aman dari NSFW",
        value=">>> Konten dewasa, gore, atau apapun yang nggak pantas dilihat semua umur — dilarang keras, tanpa terkecuali.",
        inline=False
    )
    embed.add_field(
        name="5️⃣ Jadi Diri Sendiri & Have Fun!",
        value=">>> jangan takut buat ngobrol disini, gada sirkel sirkelan ya, tapi kalau behaviour kamu bikin orang ga nyaman jangan lupa buat introspeksi diri..",
        inline=False
    )
    embed.add_field(
        name="6️⃣ Admin Selalu Benar.",
        value=">>> Selama semua di atas dijaga, silakan berekspresi bebas — bercanda, curhat, mabar, atau sekadar nimbrung obrolan gajelas.",
        inline=False
    )

    embed.set_footer(text="Aturan ini bisa berkembang seiring waktu — dan kalau ada yang kurang jelas, admin/mod selalu siap dihubungi kok 🌿")
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    await channel.send(embed=embed)
    await interaction.followup.send(f"✅ Peraturan sukses dikirim ke {channel.mention}!", ephemeral=True)

# ------------------------------------------------------------------------------
# MUSIC & VOICE COMMANDS (/join, /leave, /play, /filter, /skip, /stop, /queue, /nowplaying, /lyrics)
# ------------------------------------------------------------------------------

@bot.tree.command(name="join", description="Bot akan join ke voice channel")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect(self_deaf=True)
        await interaction.response.send_message(f"Berhasil join ke {channel.name}!")
    else:
        await interaction.response.send_message("Kamu harus masuk ke voice channel dulu!!", ephemeral=True)

@bot.tree.command(name="leave", description="Mengeluarkan bot dari voice channel")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Berhasil keluar dari Voice Channel!")
    else:
        await interaction.response.send_message("Tara lagi ga di voice channel mana pun..", ephemeral=True)

@bot.tree.command(name="play", description="Memutar musik dari YouTube, Spotify, SoundCloud, atau judul lagu")
@app_commands.describe(query="Masukkan Judul Lagu, Nama Artis, atau paste link URL.")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer(thinking=True)

    voice_client = interaction.guild.voice_client
    if not voice_client:
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            voice_client = await channel.connect(self_deaf=True)
        else:
            await interaction.followup.send("❌ Tarik Tara ke voice channel dulu lewat `/join`!")
            return

    guild_id = interaction.guild.id
    if guild_id not in queues:
        queues[guild_id] = []

    current_platform = "YouTube"
    pesan_platform = ""
    query = url

    spotify_match = SPOTIFY_URL_PATTERN.search(url) #<===== UNTUK SAAT INI BAGIAN SPOTIFY HANYA BISA DETECT DAN SEARCH LEWAT YT DIKARENAKAN WEB API SPOTIFY ITU BAYAR WKWKWKW
    try:
        if spotify_match or "spotify.link" in url:
            current_platform = "Spotify"
            pesan_platform = "💚 *Tara Mendeteksi tautan Spotify...*\n"

            spotify_tracks = await resolve_spotify_url(url)

            if spotify_tracks is None:
                fallback_title = url
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://open.spotify.com/oembed?url={url}") as response:
                        if response.status == 200:
                            data = await response.json()
                            fallback_title = data.get('title', url)
                await interaction.channel.send(
                    "⚠️ Tara belum punya akses penuh ke Spotify API "
                    "(`SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` belum di-set di `.env`), "
                    "jadi Tara cuma bisa nebak 1 judul lagunya, bukan seluruh Playlist/Album."
                )
                spotify_tracks = [{'title': fallback_title, 'artist': '', 'thumbnail': None, 'webpage': url}]

            if len(spotify_tracks) == 0:
                await interaction.followup.send("❌ Playlist/Album Spotify kosong atau bersifat privat.")
                return

            if len(spotify_tracks) > 140:
                spotify_tracks = spotify_tracks[:140]
                await interaction.channel.send("⚠️ **Playlist Kegedean woi!:** Tara motong queue ke `140` lagu pertama ya...")

            if len(spotify_tracks) > 1:
                await interaction.followup.send(f"📂 **Tara Mendeteksi Playlist/Album Spotify:** `{len(spotify_tracks)}` lagu ditambahkan ke queue...")

            for track in spotify_tracks:
                search_text = f"{track.get('artist', '')} - {track.get('title', '')}".strip(" -")
                song_data = {
                    'query': f"ytsearch:{search_text}",
                    'title': track.get('title') or "Unknown Title",
                    'thumbnail': track.get('thumbnail'),
                    'webpage': track.get('webpage') or url,
                    'duration': "In Queue",
                    'user': interaction.user,
                    'platform': current_platform,
                    'is_resolved': False
                }
                queues[guild_id].append(song_data)

            if not voice_client.is_playing() and not voice_client.is_paused():
                if pesan_platform:
                    await interaction.channel.send(pesan_platform)
                if len(spotify_tracks) == 1:
                    await interaction.followup.send("🎶 Memulai pemutaran audio...", ephemeral=True)
                await process_next_song(interaction, guild_id)
            elif len(spotify_tracks) == 1:
                await interaction.followup.send(f"{pesan_platform}📥 **Berhasil ditambahkan ke antrean:**\n`{spotify_tracks[0]['title']}`")
            return

        # ================= SOUNDCLOUD =================
        elif "soundcloud.com" in url:
            current_platform = "SoundCloud"
            pesan_platform = "☁️ *Lalala~...Memproses audio langsung dari SoundCloud...*\n"
            query = url

        # ================= PENCARIAN TEKS BIASA (YOUTUBE) =================
        elif not url.startswith("http://") and not url.startswith("https://"):
            current_platform = "YouTube Search"
            query = f"ytsearch:{url}"

        # ================= EKSTRAKSI YOUTUBE / SOUNDCLOUD LEWAT yt_dlp =================
        is_playlist = "list=" in url or "/sets/" in url or "playlist" in url
        opt_pilihan = YTDL_PLAYLIST_OPTIONS if is_playlist else YTDL_OPTIONS

        with yt_dlp.YoutubeDL(opt_pilihan) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, query, download=False)

        if not info:
            await interaction.followup.send("❌ Media tidak ditemukan atau gagal Tara ekstrak.")
            return
#==========================================================================-
#        UNTUK PLAYLIST DARI SOUNDCLOUD ERROR TAPI DARI YT WORK KOK
#===========================================================================
        if 'entries' in info and is_playlist:
            playlist_entries = list(info['entries'])
            total_songs = len(playlist_entries)
            if total_songs == 0:
                await interaction.followup.send("❌ Playlist kosong atau bersifat privat.")
                return
            if total_songs > 140:
                playlist_entries = playlist_entries[:140]
                await interaction.channel.send("⚠️ **Playlist Kegedean woi!:** Tara motong queue ke `140` lagu pertama ya...")
            await interaction.followup.send(f"📂 **Tara Mendeteksi Playlist Baru:** `{len(playlist_entries)}` menambahkan ke queue...")
            for entry in playlist_entries:
                if not entry: continue
                playable_query = resolve_flat_entry_url(entry, url)
                song_data = {
                    'query': playable_query,
                    'title': entry.get('title', 'Unknown Title'),
                    'thumbnail': resolve_flat_entry_thumbnail(entry),
                    'webpage': entry.get('webpage_url') or playable_query,
                    'duration': "In Queue",
                    'user': interaction.user,
                    'platform': current_platform,
                    'is_resolved': False
                }
                queues[guild_id].append(song_data)
            if not voice_client.is_playing() and not voice_client.is_paused():
                await process_next_song(interaction, guild_id)
            return
        if 'entries' in info:
            info = info['entries'][0]
        mins, secs = divmod(int(info.get('duration', 0)), 60)
        duration_str = f"{mins}:{secs:02d}"
        song_data = {
            'query': info.get('webpage_url') or info.get('url') or f"ytsearch:{info.get('title')}",
            'url': info['url'],
            'title': info.get('title') or "Unknown Title",
            'thumbnail': info.get('thumbnail'),
            'webpage': info.get('webpage_url', '#'),
            'duration': duration_str,
            'user': interaction.user,
            'platform': current_platform,
            'is_resolved': True
        }

        if voice_client.is_playing() or voice_client.is_paused():
            queues[guild_id].append(song_data)
            await interaction.followup.send(f"{pesan_platform}📥 **Berhasil ditambahkan ke antrean:**\n`{song_data['title']}`")
        else:
            queues[guild_id].append(song_data)
            if pesan_platform:
                await interaction.channel.send(pesan_platform)
            await interaction.followup.send("🎶 Memulai pemutaran audio...", ephemeral=True)
            await process_next_song(interaction, guild_id)

    except Exception as e:
        await interaction.followup.send(f"❌ Gagal memutar audio. Error: {e}")

@bot.tree.command(name="filter", description="🎛️ Tambahkan efek audio pada musik (Berlaku untuk lagu berikutnya)")
@app_commands.choices(efek=[
    app_commands.Choice(name="🎵 Normal (Matikan Filter)", value="normal"),
    app_commands.Choice(name="🎧 Bassboost (Jedag Jedug)", value="bassboost"),
    app_commands.Choice(name="🌌 8D Audio (Muter-muter)", value="8d"),
    app_commands.Choice(name="🚀 Nightcore (EDM Typeshi)", value="nightcore"),
    app_commands.Choice(name="⏩ Speed Up (Lebih Cepat)", value="speedup"),
    app_commands.Choice(name="🐿️ Pitch Up (Suara Chipmunk)", value="pitchup")
])
async def set_filter(interaction: discord.Interaction, efek: app_commands.Choice[str]):
    active_filters[interaction.guild.id] = FILTERS[efek.value]

    embed = discord.Embed(
        title="🎛️ Filter Audio Diperbarui!",
        description=f"Efek aktif saat ini: **{efek.name}**\n\n*(Catatan: Filter baru akan terasa efeknya saat lagu berikutnya diputar, atau silakan `/skip` lagu saat ini)*",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@play.autocomplete('url')
async def play_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not current.strip():
        return []
    if current.startswith(('http://', 'https://')):
        return [app_commands.Choice(name=f"Tautan Langsung: {current[:80]}...", value=current)]

    try:
        OPTIONS_AUTO = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(OPTIONS_AUTO) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, f"ytsearch30:{current}", download=False)
            choices = []

            if info and 'entries' in info:
                for entry in info['entries']:
                    if not entry: continue
                    title = entry.get('title', 'Unknown Title')
                    video_url = entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                    label_tampil = f"🎵 {title[:90]}"
                    choices.append(app_commands.Choice(name=label_tampil, value=video_url))

            return choices[:25]
    except Exception:
        return []

@bot.tree.command(name="skip", description="Vote skip lagu yang sedang diputar (butuh 50% suara pendengar di VC)")
async def skip(interaction: discord.Interaction):
    skipped, pesan = await process_skip_vote(interaction)
    await interaction.response.send_message(pesan)

@bot.tree.command(name="stop", description="Menghentikan musik dan menghapus semua antrean")
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in queues: queues[guild_id].clear()
    voice_client = interaction.guild.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        stop_karaoke_task(guild_id)
        voice_client.stop()
        await interaction.response.send_message("🛑 Music distop dan antrean dikosongkan!")
    else:
        await interaction.response.send_message("❌ Tara sedang tidak memutar lagu apapun...")

@bot.tree.command(name="queue", description="Melihat daftar antrean lagu saat ini")
async def queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    voice_client = interaction.guild.voice_client
    embed = discord.Embed(title="📋 Antrean Musik Server", color=discord.Color.blurple())

    if voice_client and hasattr(voice_client, 'current_song') and voice_client.current_song:
        embed.add_field(name="🎵 Sedang Diputar", value=voice_client.current_song, inline=False)
    else:
        embed.add_field(name="🎵 Sedang Diputar", value="Tidak ada lagu", inline=False)

    daftar_antrean = ""
    if guild_id in queues and queues[guild_id]:
        for i, song in enumerate(queues[guild_id], start=1):
            daftar_antrean += f"**{i}.** {song['title']} (`{song['platform']}`)\n"
            if i == 15:
                daftar_antrean += f"*...dan {len(queues[guild_id]) - 15} lagu lainnya.*"
                break
    else:
        daftar_antrean = "Queue kosong. Gunakan `/play` untuk menambah lagu!"
    embed.add_field(name="⏳ Lagu Berikutnya...", value=daftar_antrean, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="nowplaying", description="🎶 Lihat lagu yang lagi diputar lengkap sama progress bar visualnya")
async def nowplaying(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    voice_client = interaction.guild.voice_client

    if not voice_client or guild_id not in last_played_song or not (voice_client.is_playing() or voice_client.is_paused()):
        await interaction.followup.send("❌ Ga ada lagu yang lagi diputar mang! Coba `/play` dulu.")
        return

    song = last_played_song[guild_id]
    total_secs = parse_duration_to_seconds(song.get('duration', '0:00'))
    elapsed_secs = int(get_elapsed_seconds(guild_id))
    if total_secs:
        elapsed_secs = min(elapsed_secs, total_secs)

    platform_name = song.get('platform', 'YouTube')
    if platform_name == "Spotify":
        embed_color, icon = discord.Color.from_rgb(30, 215, 96), "💚"
    elif platform_name == "SoundCloud":
        embed_color, icon = discord.Color.from_rgb(255, 85, 0), "☁️"
    else:
        embed_color, icon = discord.Color.from_rgb(231, 76, 60), "🔴"

    status_icon = "⏸️" if voice_client.is_paused() else "▶️"
    voice_channel_name = voice_client.channel.name if voice_client.channel else "Voice Channel"
    loop_label = "Lagu Ini 🔁" if loop_mode.get(guild_id) == "song" else "Off"

    embed = discord.Embed(
        title=f"{icon} {status_icon} Now Playing",
        description=(
            f"### {song['title']}\n"
            + (f"• Added by {song['user'].mention}\n" if song.get('user') else "")
            + f"• 🔊 {voice_channel_name}"
        ),
        color=embed_color,
        url=song.get('webpage') or None
    )
    embed.add_field(
        name="\u200b",
        value=f"Queue Size: `{len(queues.get(guild_id, []))}` • Loop: `{loop_label}` • Platform: `{platform_name}`",
        inline=False
    )

    key = song.get('webpage') or song.get('title')
    if key in song_reactions:
        tally = song_reactions[key]
        embed.add_field(name="Reaksi", value=f"👍 `{tally['up']}`   👎 `{tally['down']}`", inline=True)

    if song.get('thumbnail'):
        embed.set_thumbnail(url=song['thumbnail'])

    progress_buf = await generate_progress_image(elapsed_secs, total_secs)
    progress_file = discord.File(fp=progress_buf, filename="tara_progress.png")
    embed.set_image(url="attachment://tara_progress.png")

    embed.set_footer(text="Gunakan tombol di bawah Now Playing buat vote-skip/pause | Tara Music")
    await interaction.followup.send(embed=embed, file=progress_file)

@bot.tree.command(name="lyrics", description="Mencari lirik lagu dari lagu yang sedang diputar atau lewat judul")
@app_commands.describe(
    judul="Masukkan judul lagu secara spesifik (opsional, jika kosong akan mencari lagu aktif)",
    karaoke="Aktifkan mode karaoke: lirik auto-update ngikutin lagu yang lagi diputar di VC"
)
async def lyrics(interaction: discord.Interaction, judul: str = None, karaoke: bool = False):
    await interaction.response.defer()

    guild_id = interaction.guild.id

    # ============= NEW: MODE KARAOKE (LIRIK AUTO-SYNC) =============
    if karaoke:
        voice_client = interaction.guild.voice_client
        if not voice_client or not (voice_client.is_playing() or voice_client.is_paused()) or guild_id not in last_played_song:
            await interaction.followup.send("❌ Mode karaoke butuh lagu yang lagi Tara puter di VC dulu nih! Coba `/play` dulu ya.")
            return

        song_info = last_played_song[guild_id]
        song_title = song_info.get('title', '')
        total_secs = parse_duration_to_seconds(song_info.get('duration', '0:00'))

        lines = await fetch_synced_lyrics(song_title, "", total_secs)
        estimasi = False

        if not lines:
            # Fallback: lirik biasa dari Genius, disebar merata sepanjang durasi (ESTIMASI, bukan sinkron asli)
            judul_bersih_ka = re.sub(r'\(.*?\)|\[.*?\]|official|video|music|lyric|audio', '', song_title, flags=re.IGNORECASE).strip()
            try:
                loop = asyncio.get_event_loop()
                song = await loop.run_in_executor(None, lambda: genius.search_song(judul_bersih_ka))
            except Exception:
                song = None

            if not song or not song.lyrics:
                await interaction.followup.send(f"❌ Waduh, lirik sinkron buat **'{song_title}'** ga ketemu, lirik biasa dari Genius juga ga ada... 😭")
                return

            raw_lines = [l.strip() for l in song.lyrics.split('\n') if l.strip()]
            raw_lines = [l for l in raw_lines if "Lyrics" not in l and not re.search(r'\d+Embed$', l)]
            if not raw_lines:
                await interaction.followup.send("❌ Lirik ketemu tapi isinya kosong/aneh, coba lagu lain ya.")
                return

            step = max((total_secs / max(len(raw_lines), 1)) if total_secs else 4, 3)
            lines = [(i * step, line) for i, line in enumerate(raw_lines)]
            estimasi = True

        stop_karaoke_task(guild_id)  # NEW: matiin task karaoke lama kalau ada

        embed_awal = discord.Embed(
            title="🎤 Mode Karaoke Diaktifkan!",
            description=(
                f"Nyanyiin **{song_title}** bareng-bareng yuk! Lirik bakal auto-update tiap beberapa detik.\n\n"
                + ("*(⚠️ Lirik sinkron asli ga ketemu, ini timing estimasi doang ya, bisa aja meleset!)*" if estimasi
                   else "*(✅ Pakai lirik sinkron asli, seharusnya pas sama lagunya!)*")
            ),
            color=discord.Color.from_rgb(30, 215, 96)
        )
        msg = await interaction.followup.send(embed=embed_awal)
        task = interaction.client.loop.create_task(run_karaoke(interaction, guild_id, lines, msg))
        karaoke_tasks[guild_id] = task
        return

    # ============= MODE BIASA (LIRIK STATIS) =============
    target_judul = judul

    if not target_judul:
        vc = interaction.guild.voice_client
        if vc and vc.is_playing() and guild_id in last_played_song:
            target_judul = last_played_song[guild_id]['title']
        else:
            await interaction.followup.send("❌ Gak ada lagu yang lagi diputar mang! Coba ketik judul lagunya manual, misal: `/lyrics judul: Komang`")
            return

    judul_bersih = re.sub(r'\(.*?\)|\[.*?\]|official|video|music|lyric|audio', '', target_judul, flags=re.IGNORECASE).strip()

    try:
        loop = asyncio.get_event_loop()
        song = await loop.run_in_executor(None, lambda: genius.search_song(judul_bersih))

        if not song or not song.lyrics:
            await interaction.followup.send(f"❌ Aduh mang, Tara cari kemana-mana lirik buat lagu **'{judul_bersih}'** di Genius gak ketemu... 😭")
            return

        raw_lirik = song.lyrics
        lirik_lines = raw_lirik.split('\n')
        if len(lirik_lines) > 1 and "Lyrics" in lirik_lines[0]:
            lirik_lines = lirik_lines[1:]

        lirik_bersih = '\n'.join(lirik_lines)
        lirik_bersih = re.sub(r'\d+Embed$', '', lirik_bersih).strip()

        if len(lirik_bersih) > 2000:
            set_1 = lirik_bersih[:2000]
            set_2 = lirik_bersih[2000:]
            potongan_akhir = set_1.rfind('\n')
            if potongan_akhir != -1:
                set_2 = set_1[potongan_akhir:] + set_2
                set_1 = set_1[:potongan_akhir]
            embed1 = discord.Embed(
                title=f"🎤 Lirik: {song.title}",
                description=f"Oleh: **{song.artist}**\n\n{set_1}",
                color=discord.Color.from_rgb(30, 215, 96)
            )
            if song.song_art_image_thumbnail_url:
                embed1.set_thumbnail(url=song.song_art_image_thumbnail_url)
            embed1.set_footer(text="Bagian 1/2 | Literata Music", icon_url=interaction.user.display_avatar.url)
            await interaction.followup.send(embed=embed1)
            embed2 = discord.Embed(
                description=set_2,
                color=discord.Color.from_rgb(30, 215, 96)
            )
            embed2.set_footer(text="Bagian 2/2 | Genius Database", icon_url=interaction.user.display_avatar.url)
            await interaction.followup.send(embed=embed2)

        else:
            embed = discord.Embed(
                title=f"🎤 Lirik: {song.title}",
                description=f"Oleh: **{song.artist}**\n\n{lirik_bersih}",
                color=discord.Color.from_rgb(30, 215, 96)
            )
            if song.song_art_image_thumbnail_url:
                embed.set_thumbnail(url=song.song_art_image_thumbnail_url)
            embed.set_footer(text="Database: Genius API | Literata Music Team", icon_url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Haduh kepala Tara pusing mang pas nyari liriknya... (Error: {e})")

# ------------------------------------------------------------------------------
# DEVELOPER-ONLY COMMANDS
# ------------------------------------------------------------------------------

@bot.tree.command(name="logoff", description="Mematikan bot secara instan (Khusus Developer Literata)")
async def logoff(interaction: discord.Interaction):
    user_roles = [role.name for role in interaction.user.roles]
    if ROLE_DEVELOPER_NAME in user_roles:
        await interaction.response.send_message("Dadah... Tara uda ngantuk...", ephemeral=True)
        await bot.close()
        sys.exit()
    else:
        await interaction.response.send_message(f"❌ Gamau. Yang bisa nyuruh Tara tidur cuman **{ROLE_DEVELOPER_NAME}**.", ephemeral=True)

# ------------------------------------------------------------------------------
# MODERATION COMMANDS (Khusus Admin/Mod: kick, ban, timeout, mute, unmute)
# ------------------------------------------------------------------------------

# COMMAND MODERASI: KICK
@bot.tree.command(name="kick", description="Mengeluarkan (kick) warga nakal dari server")
@app_commands.default_permissions(kick_members=True) # Hanya user dengan izin Kick Members yang bisa pakai
async def kick(interaction: discord.Interaction, member: discord.Member, alasan: str = "Melanggar peraturan server"):
    await interaction.response.defer(ephemeral=True)

    if member.top_role >= interaction.user.top_role:
        await interaction.followup.send("❌ Kamu tidak bisa nge-kick warga yang rolenya setara atau lebih tinggi dari kamu!", ephemeral=True)
        return

    try:
        try:
            await member.send(f"⚠️ Maaf ya, kamu telah **di-kick** dari server **{interaction.guild.name}**.\n**Alasan:** {alasan}")
        except discord.Forbidden:
            pass
        await member.kick(reason=alasan)

        embed = discord.Embed(title="👢 Member Berhasil Tara Kick!", color=discord.Color.orange())
        embed.add_field(name="👤 Ex-Member", value=member.mention, inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Alasan", value=f"`{alasan}`", inline=False)

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Proses kick sukses!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Gagal melakukan kick. Error: {e}", ephemeral=True)

# COMMAND MODERASI: BAN
@bot.tree.command(name="ban", description="Memblokir (ban) warga dari server secara permanen")
@app_commands.default_permissions(ban_members=True) # Hanya user dengan izin Ban Members yang bisa pakai
async def ban(interaction: discord.Interaction, member: discord.Member, alasan: str = "Melanggar peraturan berat"):
    await interaction.response.defer(ephemeral=True)
    if member.top_role >= interaction.user.top_role:
        await interaction.followup.send("❌ Eeitss, tidak bisa. Emangnya kamu bisa ngatur-ngatur?", ephemeral=True)
        return
    try:
        try:
            await member.send(f"🚨 Maaf ya, kamu telah Tara **BAN PERMANEN** dari server **{interaction.guild.name}**.\n**Alasan:** {alasan}")
        except discord.Forbidden:
            pass

        await member.ban(reason=alasan, delete_message_days=1) # Menghapus pesan chat pelaku 1 hari ke belakang

        embed = discord.Embed(title="🔨 Member Berhasil Tara Ban!", color=discord.Color.red())
        embed.add_field(name="👤 Member", value=member.mention, inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Alasan", value=f"`{alasan}`", inline=False)

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Proses ban sukses!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Gagal melakukan ban. Error: {e}", ephemeral=True)

# COMMAND MODERASI: TIMEOUT (MUTE CUSTOM WAKTU)
@bot.tree.command(name="timeout", description="Memberikan timeout (mute total text & voice) berdasarkan menit")
@app_commands.default_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, menit: int, alasan: str = "Perlakuan tidak pantas / spam"):
    await interaction.response.defer(ephemeral=True)

    if member.top_role >= interaction.user.top_role:
        await interaction.followup.send("❌ Eeitss gabisa kamu gapunya hak sama sekali...", ephemeral=True)
        return

    try:
        durasi = datetime.timedelta(minutes=menit)
        await member.timeout(durasi, reason=alasan)

        embed = discord.Embed(title="⏳ Member Sudah Tara Timeout!", color=discord.Color.gold())
        embed.add_field(name="👤 Target", value=member.mention, inline=True)
        embed.add_field(name="⏱️ Durasi", value=f"`{menit} Menit`", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=False)
        embed.add_field(name="📄 Alasan", value=f"`{alasan}`", inline=False)

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Proses timeout sukses!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Gagal menerapkan timeout. Error: {e}", ephemeral=True)

# COMMAND MODERASI: MUTE (SHORTCUT TIMEOUT 1 JAM)
@bot.tree.command(name="mute", description="Shortcut instan untuk membungkam warga selama 1 jam")
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, alasan: str = "Berisik / Spamming"):
    await interaction.response.defer(ephemeral=True)

    if member.top_role >= interaction.user.top_role:
        await interaction.followup.send("❌ Gagal, role target lebih tinggi/setara denganmu.", ephemeral=True)
        return

    try:
        durasi_default = datetime.timedelta(hours=1) # Mengunci text & voice selama 1 jam penuh
        await member.timeout(durasi_default, reason=alasan)

        embed = discord.Embed(title="🔇 Tara mute dulu yaa!", color=discord.Color.dark_grey())
        embed.add_field(name="👤 Target", value=member.mention, inline=True)
        embed.add_field(name="⏱️ Durasi", value="`1 Jam (Otomatis)`", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=False)
        embed.add_field(name="📄 Alasan", value=f"`{alasan}`", inline=False)

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Tara udah mute dia!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Yahh, Tara gagal nge-mute... Error: {e}", ephemeral=True)

# COMMAND MODERASI: UNMUTE
@bot.tree.command(name="unmute", description="Membebaskan warga dari hukuman mute/timeout sebelum waktunya habis")
@app_commands.default_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)

    try:
        await member.timeout(None)

        embed = discord.Embed(title="🔊 Hukuman Dicabut (Unmuted)!", color=discord.Color.green())
        embed.add_field(name="👤 Member", value=member.mention, inline=True)
        embed.add_field(name="🛡️ Bebas Oleh", value=interaction.user.mention, inline=True)

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Member telah bisa berbicara kembali!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Gagal mencabut status hukuman. Error: {e}", ephemeral=True)


# ------------------------------------------------------------------------------
# INFO & COMMUNITY COMMANDS (/changelog, /invite) ROLE DEV OR HIGHER
# ------------------------------------------------------------------------------

@bot.tree.command(name="changelog", description="Cek apa aja yang baru dari Tara! (Update & Fitur Baru)")
@app_commands.describe(versi="Pilih versi update yang mau dilihat (Kosongkan untuk versi terbaru)")
@app_commands.choices(versi=[
    app_commands.Choice(name="Versi 2.5 (Update AI, leveling, Event Maker, Karaoke.)", value="2.5"),
    app_commands.Choice(name="Versi 1.5 (Update Fitur Hiburan)", value="1.5"),
])
async def changelog(interaction: discord.Interaction, versi: app_commands.Choice[str] = None):
    changelog_data = {
        "2.5": {
            "title": "🚀 Update V2.0 — De!",
            "date": "Juli 2026",
            "tagline": "*Tara baru aja dapat update terbaru dari Developer Team!*",
            "changes": [
                ("🧠 AI Responsif", 
                    "Karena Otak Tara udah di-upgrade pakai mesin *Gemini 2.5 Flash*! Ngobrol makin nyambung, mikir secepat kilat! (jangan keseringan. Dev nya masih kurang duit buat beli API yang pro)"
                ),
                (
                    "🎵 UI Player Modern", 
                    "Tampilan `/nowplaying` disulap jadi estetik pakai *slider progress bar*, tombol *Loop*, sama *Like/Dislike*.!"
                ),
                (
                    "🎤 Mode Karaoke (Lirik Sinkron)", 
                    "Bosan baca lirik panjang-panjang? Fitur `/lyrics` sekarang punya mode Karaoke! Liriknya bakal jalan otomatis ngikutin detikan lagunya!"
                ),
                (
                    "🏆 Sistem Level, Rank & Profile Card", 
                    "Makin sering aktif chat, level kamu bakal naik. Pamerin kartu identitas kece kamu pakai `/rank`, atur bio keren di `/profile`, dan kumpulin *badges* eksklusif otomatis!"
                ),
                (
                    "📅 Event Maker (Biar Ga Wacana)", 
                    "Bikin jadwal nobar film, turnamen mabar, atau malam curhat lebih gampang pakai `/event`. Warga bisa langsung RSVP biar kumpulnya ga sekadar janji manis doang!"
                ),
                (
                    "🔊 Bos di Voice Channel Sendiri", 
                    "Pakai `/vc_rename` buat ganti nama tongkrongan VC sementara kamu sesuka hati (tapi cuma bisa 2x dalam 10 menit ya, biar sistem Discord ga meledak!)."
                )
            ],
            "color": discord.Color.from_rgb(30, 215, 96),
            "badge": "🟢 LATEST"
        },
        "1.5": {
            "title": "✨ Update V1.5 — Nongkrong Makin Rame!",
            "date": "Juni 2026",
            "tagline": "*Fokus rilis kali ini: bikin tongkrongan makin seru & beresin PR bug lama.*",
            "changes": [
                ("🎲 Fitur Hiburan Baru", "Ada `/hiburan cekkodam` buat nerawang khodam gaib, `/hiburan roast` buat nge-bully temen (dengan cinta), sampai main *Truth or Dare* bareng anak Literata."),
                ("🐛 Basmi Kutu (Bug Fixes)", "Udah beresin beberapa error disaat muter lagu, biar Tara nggak tiba-tiba pusing dan mogok kerja."),
            ],
            "color": discord.Color.from_rgb(52, 152, 219),
            "badge": "🗂️ ARCHIVE"
        }
    }
    target_version = versi.value if versi else "2.5"
    data = changelog_data[target_version]

    embed = discord.Embed(
        title=data["title"],
        description=f"{data['tagline']}\n*Dirilis pada: {data['date']}*",
        color=data["color"]
    )
    embed.set_author(name=f"{data['badge']}  •  Literata Changelog")
    for field_title, field_desc in data["changes"]:
        embed.add_field(name=field_title, value=field_desc, inline=False)

    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(
        text="Developed by @whoisezza._ | Literata Dev Team | OC By @hiimkirax",
        icon_url=interaction.user.display_avatar.url
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="invite", description="Mendapatkan tautan undangan permanen server Literata")
async def invite(interaction: discord.Interaction):
    LINK_PERMANEN = "https://discord.gg/2WgUCM9N7s"
    view = discord.ui.View()
    tombol_link = discord.ui.Button(
        label="Gabung di Literata Community!",
        style=discord.ButtonStyle.link,
        url=LINK_PERMANEN
    )
    view.add_item(tombol_link)
    embed = discord.Embed(
        title="💚 Literata Link Server! 🦎",
        description=(
            "Mau ajak temen, gebetan, atau kerabat kamu buat nongkrong bareng di sini?\n"
            "Gunakan tombol di bawah ini ya! Tautan ini bersifat **permanen~~**."
        ),
        color=discord.Color.from_rgb(46, 204, 113)
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text="Official Literata Community Invite Link | Powered by Tara The Chameleon Bot")
    await interaction.response.send_message(embed=embed, view=view)

# ------------------------------------------------------------------------------
# VOICE CHANNEL HUB (auto create/delete VC pribadi via Hub VC + /vc command group)
# ------------------------------------------------------------------------------

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == HUB_VC_ID:
        guild = member.guild
        kategori = after.channel.category
        nama_channel = f"🔊 {member.display_name} Room"
        try:
            channel_baru = await guild.create_voice_channel(name=nama_channel, category=kategori)
            temp_vcs[channel_baru.id] = member.id
            await member.move_to(channel_baru)
        except Exception as e:
            print(f"❌ Tara gagal bikin VC: {e}")
    if before.channel and before.channel.id != HUB_VC_ID:
        if before.channel.id in temp_vcs and len(before.channel.members) == 0:
            try:
                await before.channel.delete()
                del temp_vcs[before.channel.id]
            except Exception as e:
                print(f"❌ Tara gagal menghapus VC: {e}")

# UNTUK TARA MEMODIFIKASI VC DAN AUTO CREATE VC
vc_group = app_commands.Group(name="vc", description="Manajemen Voice Channel Pribadi kamu")

# 🔸 Command: /vc limit (Mengatur jumlah maksimal orang)
@vc_group.command(name="limit", description="Atur batas maksimal member di Voice Channel kamu")
async def vc_limit(interaction: discord.Interaction, jumlah: int):
    vc = await check_vc_owner(interaction)
    if vc:
        if jumlah < 0 or jumlah > 99:
            await interaction.response.send_message("❌ Limit hanya bisa diatur dari angka 0 (tanpa batas) sampai 99.", ephemeral=True)
            return
        await vc.edit(user_limit=jumlah)
        await interaction.response.send_message(f"✅ Batas maksimal ruangan diubah menjadi **{jumlah}** orang.", ephemeral=True)

# Command: /vc lock (Mengunci Room)
@vc_group.command(name="lock", description="Kunci ruangan agar orang lain tidak bisa masuk sembarangan")
async def vc_lock(interaction: discord.Interaction):
    vc = await check_vc_owner(interaction)
    if vc:
        overwrite = vc.overwrites_for(interaction.guild.default_role)
        overwrite.connect = False
        await vc.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 **Ruangan berhasil Tara kunci!** Gunakan `/vc permit @user` untuk mengizinkan temanmu masuk.", ephemeral=True)

# Command: /vc unlock (Membuka kembali Room)
@vc_group.command(name="unlock", description="Buka kembali ruangan kamu untuk umum")
async def vc_unlock(interaction: discord.Interaction):
    vc = await check_vc_owner(interaction)
    if vc:
        overwrite = vc.overwrites_for(interaction.guild.default_role)
        overwrite.connect = None
        await vc.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 **Ruangan berhasil Tara buka!** Sekarang semua member bisa masuk.", ephemeral=True)

# Command: /vc permit (Memberi akses teman ke room yang dikunci)
@vc_group.command(name="permit", description="Izinkan seorang teman masuk ke ruanganmu yang terkunci")
async def vc_permit(interaction: discord.Interaction, user: discord.Member):
    vc = await check_vc_owner(interaction)
    if vc:
        overwrite = discord.PermissionOverwrite(connect=True)
        await vc.set_permissions(user, overwrite=overwrite)

        await interaction.response.send_message(f"✅ **{user.mention}** sekarang punya akses VVIP untuk bergabung ke ruanganmu!", ephemeral=True)

@bot.tree.command(name="vc_rename", description="Ganti nama Voice Channel tempat kamu nongkrong sekarang!")
@app_commands.describe(nama_baru="Masukkan nama Voice Channel yang baru")
async def vc_rename(interaction: discord.Interaction, nama_baru: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ Yahh, kamu harus masuk ke Voice Channel dulu sebelum nyuruh Tara ganti namanya!", ephemeral=True)
        return

    vc_channel = interaction.user.voice.channel
    if not vc_channel.permissions_for(interaction.guild.me).manage_channels:
        await interaction.response.send_message("❌ Aduh, Tara nggak dikasih akses buat ganti nama channel ini. Bilangin admin suruh kasih Tara izin `Manage Channels` dong!", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)

    try:
        nama_lama = vc_channel.name
        await vc_channel.edit(name=nama_baru)
        embed = discord.Embed(
            title="🎤 Nama Voice Channel Diperbarui!",
            description=f"Tara berhasil mengganti nama VC dari **{nama_lama}** menjadi **{nama_baru}** 🦎✨",
            color=discord.Color.from_rgb(30, 215, 96) # Warna Hijau Tara
        )
        await interaction.followup.send(embed=embed)

    except discord.errors.RateLimited:
        await interaction.followup.send("⏳ **Waduh sabar bang!** Discord ngebatasin ganti nama channel cuma boleh **2 kali dalam 10 menit**. Tunggu bentar lagi ya!")
    except Exception as e:
        await interaction.followup.send(f"❌ Yah gagal mang... kepala Tara pusing (Error: {e})")
bot.tree.add_command(vc_group)

# ------------------------------------------------------------------------------
# HIBURAN / MINI-GAMES COMMAND GROUP (/hiburan cekkhodam, ship, tod, roast, puji)
# ------------------------------------------------------------------------------

hiburan = app_commands.Group(name="minigame", description="Kumpulan mini-games dan seru-seruan bareng Tara")

# 1. Cek Khodam (Gacha)
@hiburan.command(name="cekkhodam", description="Cek khodam apa yang bersemayam di dalam dirimu hari ini")
async def cekkodam(interaction: discord.Interaction):
    list_khodam = [
        "Knalpot Supra", "Macan Cisewu", "Kucing Oren", "Sapu Lidi",
        "Seblak Ceker", "Naga Indosiar", "Kipas Angin Wadesdos",
        "Rawa Rontek", "Tuyul Nyasar", "Kosong (Lagi cuti)",
        "Kuda Plenger", "Icikiwir", "Permen Sugus", "Ipon Kupi",
        "Nasi Padang", "Roti O lempuyangan", "Buahlil", "Pesut Mahakam",
        "Pria Monokotil", "Blukutuk Kapal Selam"
    ]
    khodam = random.choice(list_khodam)
    mbed = discord.Embed(
        title="🔮 Hasil Penerawangan Khodam",
        description=f"*🦎 Tara menerawang jauh ke alam gaib...*\n\nWah, ternyata khodam yang bersemayam di dalam diri {interaction.user.mention} hari ini adalah:\n\n✨ **{khodam}** ✨",
        color=discord.Color.from_rgb(30, 215, 96)
    )
    mbed.set_thumbnail(url=interaction.user.display_avatar.url)
    mbed.set_footer(text="Jangan lupa dikasih sesajen ya khodamnya mang! | Tara Cek Kodam")
    await interaction.response.send_message(embed=mbed)

# 2. Biro Jodoh (Ship)
@hiburan.command(name="ship", description="Cek persentase kecocokan jodoh antara dua warga")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    if user1 == user2:
        await interaction.response.send_message("Masa nge-ship diri sendiri sih? Self love banget nih ye...", ephemeral=True)
        return

    persen = random.randint(0, 100)
    kotak_isi = int(persen / 10)
    kotak_kosong = 10 - kotak_isi
    progress_bar = ("💖" * kotak_isi) + ("🖤" * kotak_kosong)
    if persen < 25:
        komentar = "Waduh... mending kalian jadian... jadi musuh aja deh. 💀 -1000 Aura!"
        warna = discord.Color.dark_gray()
    elif persen < 50:
        komentar = "Hmm... bisa sih, tapi kayaknya bakal sering gelut rebutan remot TV. Yakin nih? 🤔"
        warna = discord.Color.orange()
    elif persen < 80:
        komentar = "Cieee lumayan cocok nih! Gas kencengin lagi peletnya mang! 🚀💖"
        warna = discord.Color.from_rgb(255, 105, 180)
    elif persen < 95:
        komentar = "Udah pas banget ini mah! Tara tungguin undangan nikahnya di meja ya! 💌✨"
        warna = discord.Color.red()
    else:
        komentar = "ANJAY SO SWEET BANGET! 😭💕 UDAH MINIMAL BESOK LANGSUNG KE KUA AJA SANA!!"
        warna = discord.Color.from_rgb(255, 20, 147) # Deep Pink
    embed = discord.Embed(
        title="💘 BIRO JODOH TARA 💘",
        description=f"*Tara ngusap-ngusap bola kristal...*\n\nMari kita lihat persentase kecocokan antara **{user1.display_name}** dan **{user2.display_name}**!",
        color=warna
    )
    embed.set_author(name=user1.display_name, icon_url=user1.display_avatar.url)
    embed.set_thumbnail(url=user2.display_avatar.url)
    embed.add_field(name="Tingkat Kecocokan:", value=f"{progress_bar} **{persen}%**", inline=False)
    embed.add_field(name="Kata Tara:", value=f"*{komentar}*", inline=False)
    embed.set_footer(text=f"Di-ship oleh {interaction.user.display_name} | Pelet Tara", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(content=f"Cieee {user1.mention} 💘 {user2.mention} dapet salam dari Tara nih!", embed=embed)

# 3. Truth or Dare
@hiburan.command(name="tod", description="Main Truth or Dare buat main di Voice Channel")
@app_commands.choices(pilihan=[
    app_commands.Choice(name="Truth (Kejujuran)", value="truth"),
    app_commands.Choice(name="Dare (Tantangan)", value="dare")
])
async def tod(interaction: discord.Interaction, pilihan: app_commands.Choice[str]):
    if pilihan.value == "truth":
        list_q = [
            "Siapa orang di server ini yang paling pengen kamu kick?",
            "Kapan terakhir kali kamu nangis dan kenapa?",
            "Apa chat paling memalukan yang pernah kamu kirim ke orang?",
            "Jujur, kamu pernah naksir seseorang di server Literata nggak?"
            "Siapa member yang paling kamu benci di server Literata dan alasannya apa?"
            "Jujur, kamu redflag dari segi apa? gaperlu spesifik yang penting jujur."
            "Kamu lebih memilih berada di hubungan toxic tapi lama atau mesra tapi bentar karena perkara kondisi?"
        ]
        await interaction.response.send_message(f"💬 **TRUTH untuk {interaction.user.mention}:**\n*{random.choice(list_q)}*")
    else:
        list_d = [
            "Nyanyi lagu Balonku pakai huruf O semua!",
            "Tag satu orang random di server ini dan bilang 'I Love You, Sayang.'.",
            "Tag satu orang di server dan ketik 'aku suka furry'.",
            "Ganti foto profil (Avatar) kamu jadi foto kamu yang paling konyol di galeri selama 4 jam."
            "Main valo tapi pick agent yang kamu benci banget buat dimainin."
            "Akui satu keputusan konyol di hidup kamu serta berikan alasan nya."
        ]
        await interaction.response.send_message(f"🔥 **DARE untuk {interaction.user.mention}:**\n*{random.choice(list_d)}*")

# 4. Roasting
@hiburan.command(name="roast", description="Suruh Tara nge-roast temanmu (Bercanda ya!)")
async def roast(interaction: discord.Interaction, target: discord.Member):
    list_roast = [
        f"{target.mention}, kamu itu ibarat wifi lemot, ada tapi bikin emosi.",
        f"Muka {target.mention} tuh unik ya, cocok banget buat jadi orang orangan sawah.",
        f"Setiap kali {target.mention} ngetik, rasanya server ini butuh fitur 'Mute Permanen'.",
        f"{target.mention} kalau disuruh milih otak atau uang, pasti milih uang. Soalnya otak dia emang udah gak dipake."
        f"Woi.. {target.mention} "
    ]
    await interaction.response.send_message(random.choice(list_roast))

# 5. Puji (Support)
@hiburan.command(name="puji", description="Puji temanmu biar dia tersenyum hari ini")
async def puji(interaction: discord.Interaction, target: discord.Member):
    list_puji = [
        f"Setiap lihat nama {target.mention} online, rasanya dunia jadi lebih cerah deh. ✨",
        f"{target.mention} itu orangnya asik banget, pantes banyak temennya...",
        f"Semangat terus ya {target.mention}! Kamu hebat udah bertahan dan selalu kuat sejauh ini. 💚",
        f"Server Literata gak akan se-seru ini tanpa kehadiran {target.mention}. Love you! 🫶"
    ]
    await interaction.response.send_message(random.choice(list_puji))
bot.tree.add_command(hiburan)

# ==============================================================================
# NEW: LEVELING & RANK COMMANDS
# ==============================================================================
@bot.tree.command(name="rank", description="🏆 Lihat kartu rank & progress XP kamu (atau member lain)")
async def rank(interaction: discord.Interaction, user: discord.Member = None):
    await interaction.response.defer()
    target = user or interaction.user
    if target.bot:
        await interaction.followup.send("❌ Bot nggak ikutan naik level yaa mang!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    data = user_xp[guild_id][target.id]
    level = data["level"]
    current_xp = data["xp"]
    xp_needed = get_xp_needed(level)

    # Hitung posisi rank berdasarkan level lalu XP (descending)
    sorted_members = sorted(
        user_xp[guild_id].items(),
        key=lambda item: (item[1]["level"], item[1]["xp"]),
        reverse=True
    )
    rank_position = next((i + 1 for i, (uid, _) in enumerate(sorted_members) if uid == target.id), len(sorted_members) or 1)

    try:
        buffer = await generate_rank_card(target, level, rank_position, current_xp, xp_needed)
        file = discord.File(fp=buffer, filename="tara_rank_card.png")
        await interaction.followup.send(file=file)
    except Exception as e:
        await interaction.followup.send(f"❌ Aduh, Tara gagal bikin kartu rank-nya: `{e}`")

#===============================================================================================
# COMMAND GROUP DIBAWAH ADALAH SISTEM LEVELING /leadeboard

leaderboard = app_commands.Group(name="leaderboard", description="Papan peringkat member Literata")

@leaderboard.command(name="level", description="Lihat 10 member paling aktif (Level & XP tertinggi) di server ini")
async def leaderboard_level(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    data_guild = user_xp.get(guild_id, {})
    if not data_guild:
        await interaction.response.send_message("Belum ada aktivitas chat yang Tara catat nih di server ini!", ephemeral=True)
        return

    sorted_members = sorted(data_guild.items(), key=lambda item: (item[1]["level"], item[1]["xp"]), reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉"]
    desc_lines = []
    for idx, (uid, stats) in enumerate(sorted_members):
        member = interaction.guild.get_member(uid)
        nama = member.display_name if member else f"Member ID {uid}"
        prefix = medals[idx] if idx < 3 else f"`#{idx + 1}`"
        desc_lines.append(f"{prefix} **{nama}** — Level `{stats['level']}` ({stats['xp']} XP)")

    embed = discord.Embed(
        title="🏆 Leaderboard Level Literata",
        description="\n".join(desc_lines),
        color=discord.Color.from_rgb(30, 215, 96)
    )
    embed.set_footer(text="Terus aktif chat biar naik peringkat! | Tara Leveling System")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    await interaction.response.send_message(embed=embed)

bot.tree.add_command(leaderboard)

# ==============================================================================
# NEW: KARTU PROFIL (/profile & /setbio)
# ==============================================================================
@bot.tree.command(name="setbio", description="✍️ Atur bio singkat buat kartu /profile kamu")
@app_commands.describe(bio="Bio singkat kamu (maksimal 100 karakter)")
async def setbio(interaction: discord.Interaction, bio: str):
    if len(bio) > 100:
        await interaction.response.send_message("❌ Bio kepanjangan mang, maksimal 100 karakter ya!", ephemeral=True)
        return
    user_bio[interaction.user.id] = bio
    await interaction.response.send_message(f"✅ Bio kamu berhasil diupdate jadi:\n> *{bio}*", ephemeral=True)

@bot.tree.command(name="profile", description="🪪 Lihat kartu profil kamu (bio, badge, level, koin) yang bisa di-screenshot")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    if target.bot:
        await interaction.response.send_message("❌ Bot ga punya kartu profil jer, cuma manusia yang punya!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    data = user_xp[guild_id][target.id]
    level = data["level"]
    xp_needed = get_xp_needed(level)
    badges = get_badges(target, level)
    bio = user_bio.get(target.id) or "*Belum ada bio nih, atur pakai `/setbio` yuk!*"
    koin = user_coins.get(target.id, 0)

    embed = discord.Embed(
        title=f"🪪 Kartu Profil {target.display_name}",
        description=f"> {bio}",
        color=discord.Color.from_rgb(30, 215, 96)
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="📈 Level", value=f"`{level}` ({data['xp']}/{xp_needed} XP)", inline=True)
    embed.add_field(name="💰 Koin", value=f"`{koin}` koin", inline=True)
    embed.add_field(name="🏅 Badge", value=" ".join(badges), inline=False)
    embed.set_footer(text=f"Diminta oleh {interaction.user.display_name} | Kartu Profil Literata", icon_url=interaction.user.display_avatar.url)
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    await interaction.response.send_message(embed=embed)

# =======================================================================================
# SISTEM EVENT RUTIN TERJADWAL (malam curhat, movie night, turnamen, spill the tea, dll)
# Admin bisa bikin jadwal bebas (nama, hari, jam, channel, role ping) lewat /event create,
# terus Tara otomatis ngepost pengumuman + reminder 30 menit sebelumnya tiap minggu.
# =======================================================================================
class EventRSVPView(discord.ui.View):
    def __init__(self, event_key: str):
        super().__init__(timeout=None)
        self.event_key = event_key

    @discord.ui.button(label="Aku Ikut! 🙋", style=discord.ButtonStyle.success, custom_id="event_rsvp_button")
    async def rsvp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ev = scheduled_events.get(self.event_key)
        if not ev:
            await interaction.response.send_message("Event ini kayaknya udah nggak ada di jadwal lagi.", ephemeral=True)
            return
        rsvp_set = ev.setdefault("rsvp", set())
        if interaction.user.id in rsvp_set:
            rsvp_set.discard(interaction.user.id)
            await interaction.response.send_message("Oke, kamu Tara coret dari daftar ikutan yaa~", ephemeral=True)
        else:
            rsvp_set.add(interaction.user.id)
            await interaction.response.send_message(f"✅ Sip, kamu tercatat ikutan **{ev['title']}**! ({len(rsvp_set)} orang udah konfirmasi)", ephemeral=True)

def _next_occurrence_text(ev):
    """Bikin teks 'Senin, 20:00 WIB (3 hari lagi)' buat ditampilin di /event list."""
    now_wib = datetime.datetime.now(WIB)
    days_ahead = (ev["day"] - now_wib.weekday()) % 7
    jam, menit = map(int, ev["time"].split(":"))
    target = (now_wib + datetime.timedelta(days=days_ahead)).replace(hour=jam, minute=menit, second=0, microsecond=0)
    if target <= now_wib:
        target += datetime.timedelta(days=7)
        days_ahead = 7
    if days_ahead == 0:
        sisa = "Hari ini"
    elif days_ahead == 1:
        sisa = "Besok"
    else:
        sisa = f"{days_ahead} hari lagi"
    return f"{DAY_NAMES_ID[ev['day']]}, {ev['time']} WIB ({sisa})"

async def send_event_announcement(name, ev):
    channel = bot.get_channel(ev["channel_id"])
    if not channel:
        print(f"❌ Channel event '{name}' (ID {ev['channel_id']}) nggak ketemu, pengumuman di-skip.")
        return
    ev["rsvp"] = set()  # reset daftar RSVP tiap kali event mulai dari awal lagi
    ping_text = f"<@&{ev['role_id']}>" if ev.get("role_id") else ""
    embed = discord.Embed(
        title=f"🔔 {ev['title']} — Dimulai Sekarang!",
        description=ev["description"],
        color=discord.Color.from_rgb(30, 215, 96)
    )
    embed.set_footer(text="Klik tombol di bawah buat kasih tau Tara kalau kamu ikutan!")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    try:
        await channel.send(content=ping_text, embed=embed, view=EventRSVPView(name))
    except Exception as e:
        print(f"❌ Gagal ngirim pengumuman event '{name}': {e}")

async def send_event_reminder(name, ev):
    channel = bot.get_channel(ev["channel_id"])
    if not channel:
        return
    embed = discord.Embed(
        title=f"⏰ Reminder: {ev['title']} 30 menit lagi!",
        description=ev["description"],
        color=discord.Color.from_rgb(241, 196, 15)
    )
    try:
        await channel.send(embed=embed, view=EventRSVPView(name))
    except Exception as e:
        print(f"❌ Gagal ngirim reminder event '{name}': {e}")

@tasks.loop(minutes=1)
async def event_scheduler_loop():
    now_wib = datetime.datetime.now(WIB)
    today_str = now_wib.strftime("%Y-%m-%d")
    current_day = now_wib.weekday()
    current_hm = now_wib.strftime("%H:%M")

    for name, ev in list(scheduled_events.items()):
        if ev["day"] != current_day:
            continue
        try:
            jam, menit = map(int, ev["time"].split(":"))
        except Exception:
            continue
        event_dt_today = now_wib.replace(hour=jam, minute=menit, second=0, microsecond=0)
        reminder_hm = (event_dt_today - datetime.timedelta(minutes=30)).strftime("%H:%M")

        if current_hm == reminder_hm and ev.get("last_reminder_date") != today_str:
            ev["last_reminder_date"] = today_str
            await send_event_reminder(name, ev)

        if current_hm == ev["time"] and ev.get("last_fired_date") != today_str:
            ev["last_fired_date"] = today_str
            await send_event_announcement(name, ev)

DAY_CHOICES = [
    app_commands.Choice(name="Senin", value=0),
    app_commands.Choice(name="Selasa", value=1),
    app_commands.Choice(name="Rabu", value=2),
    app_commands.Choice(name="Kamis", value=3),
    app_commands.Choice(name="Jumat", value=4),
    app_commands.Choice(name="Sabtu", value=5),
    app_commands.Choice(name="Minggu", value=6),
]

event_group = app_commands.Group(name="event", description="Kelola event rutin mingguan Literata (malam curhat, movie night, dll)")

@event_group.command(name="create", description="Buat/atur jadwal event rutin mingguan (khusus Admin/Moderator)")
@app_commands.describe(
    nama="ID unik buat event ini, tanpa spasi (contoh: malam-curhat)",
    judul="Judul event yang ditampilkan (contoh: 🌙 Malam Curhat)",
    deskripsi="Deskripsi singkat event ini",
    hari="Hari event ini rutin diadakan tiap minggu",
    jam="Jam mulai, format 24 jam WIB (contoh: 20:00)",
    channel="Channel tempat pengumuman & reminder event di-post",
    role="Role yang di-ping pas event mulai (opsional)"
)
@app_commands.choices(hari=DAY_CHOICES)
async def event_create(interaction: discord.Interaction, nama: str, judul: str, deskripsi: str, hari: app_commands.Choice[int], jam: str, channel: discord.TextChannel, role: discord.Role = None):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ Cuma Admin/Moderator yang bisa atur jadwal event.", ephemeral=True)
        return
    if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", jam):
        await interaction.response.send_message("❌ Format jam salah, pakai format 24 jam kayak `20:00` ya.", ephemeral=True)
        return

    key = re.sub(r"\s+", "-", nama.strip().lower())
    scheduled_events[key] = {
        "title": judul,
        "description": deskripsi,
        "day": hari.value,
        "time": jam,
        "channel_id": channel.id,
        "role_id": role.id if role else None,
        "guild_id": interaction.guild.id,
        "last_fired_date": None,
        "last_reminder_date": None,
        "rsvp": set(),
    }
    await interaction.response.send_message(
        f"✅ Event **{judul}** (`{key}`) berhasil dijadwalin tiap **{DAY_CHOICES[hari.value].name}, jam {jam} WIB** di {channel.mention}!"
        + (f" Bakal ping {role.mention} tiap kali mulai." if role else "")
    )

@event_group.command(name="list", description="Lihat semua event rutin yang udah dijadwalkan")
async def event_list(interaction: discord.Interaction):
    if not scheduled_events:
        await interaction.response.send_message("Belum ada event rutin yang dijadwalkan. Admin bisa bikin lewat `/event create`.")
        return

    embed = discord.Embed(title="📅 Jadwal Event Rutin Literata", color=discord.Color.from_rgb(30, 215, 96))
    for key, ev in scheduled_events.items():
        embed.add_field(
            name=f"{ev['title']}  (`{key}`)",
            value=f"🗓️ {_next_occurrence_text(ev)}\n📍 <#{ev['channel_id']}>\n{ev['description']}",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

@event_group.command(name="delete", description="Hapus jadwal event rutin (khusus Admin/Moderator)")
@app_commands.describe(nama="ID event yang mau dihapus (cek lewat /event list)")
async def event_delete(interaction: discord.Interaction, nama: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ Cuma Admin/Moderator yang bisa hapus jadwal event.", ephemeral=True)
        return
    key = re.sub(r"\s+", "-", nama.strip().lower())
    if key in scheduled_events:
        judul_hapus = scheduled_events[key]["title"]
        del scheduled_events[key]
        await interaction.response.send_message(f"🗑️ Event **{judul_hapus}** (`{key}`) berhasil dihapus dari jadwal.")
    else:
        await interaction.response.send_message(f"❌ Event `{key}` nggak ketemu. Cek nama yang bener lewat `/event list`.", ephemeral=True)

bot.tree.add_command(event_group)

# ------------------------------------------------------------------------------
# HELP COMMAND (daftar semua command Tara berdasarkan kategori)
# ------------------------------------------------------------------------------

@bot.tree.command(name="help", description="Menampilkan daftar semua command Tara beserta fungsinya")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛠️ PUSAT BANTUAN TARA 🦎",
        description=(
            "Halo Halooo! Ada yang bisa Tara bantu? 💚\n"
            "Di bawah ini adalah daftar lengkap kemampuan hebat yang Tara miliki sekarang. "
            "Ketik garis miring `/` di chat lalu pilih perintah yang kamu mau yawww!"
        ),
        color=discord.Color.from_rgb(30, 215, 96) # Warna Hijau Khas Tara
    )
    embed.add_field(
        name="✨ Fitur AI Tara (Baru!)",
        value=(
            "Kamu nggak perlu perintah khusus buat ngobrol sama Tara! \n"
            "💬 **Cara Pakai:** Cukup ketik kata **'tara'** atau **'Tara'** di **text channel mana saja**, "
            "maka Tara bakal otomatis nimbrung obrolanmu pakai otak terbarunya (`gemini-2.5-flash`)"
        ),
        inline=False
    )
    embed.add_field(
        name="🎵 🎧 Music & DJ Tara",
        value=(
            "`/play [judul/link]` : Memutar musik dari YouTube, Spotify, dll.\n"
            "`/filter [efek]` : Kasih efek audio keren (*Bassboost, Nightcore, 8D Audio*, dll).\n"
            "`/skip` : **Vote skip** lagu (butuh 50% suara pendengar di VC, Mod/Dev bisa instan).\n"
            "`/stop` : Menghentikan musik dan membersihkan antrean.\n"
            "`/queue` : Melihat daftar antrean lagu saat ini.\n"
            "`/nowplaying` : Lihat lagu yang sedang diputar + progress bar visual (UI baru!).\n"
            "`/lyrics [judul] [karaoke]` : Cari lirik statis, atau aktifkan `karaoke:True` buat lirik auto-sync!\n"
            "*Tombol Now Playing juga ada Loop, dan reaksi 👍/👎 buat tiap lagu.*"
        ),
        inline=False
    )
    embed.add_field(
        name="🔊 🎤 Pengaturan Voice Channel",
        value=(
            "`/join` & `/leave` : Memanggil/mengeluarkan Tara dari VC.\n"
            "`/vc_rename [nama]` : Ganti nama VC tempat kamu nongkrong otomatis! *(Max 2x / 10 menit)*\n"
            "`/vc_lock`: Lock VC tempat kamu berada agar tidak diganggu!\n"
            "`/vc permit [user]` : Mengizinkan teman masuk saat VC pribadimu di-lock."
        ),
        inline=False
    )

    # 🎮 Kategori Hiburan & Sosial
    embed.add_field(
        name="🎮 🎲 Hiburan & Mini-Games",
        value=(
            "`/hiburan cekkodam` : Menerawang khodam gaib di dalam dirimu (+ Foto Profil).\n"
            "`/hiburan ship [@user1] [@user2]` : Cek persentase kecocokan jodoh (for fun only).\n"
            "`/hiburan tod` : Main Truth or Dare bareng member Literata yang lain!.\n"
            "`/hiburan roast [@user]` : Menyuruh Tara ngeledek temanmu sampai kena mental.\n"
            "`/hiburan puji [@user]` : Menyuruh Tara memuji temanmu setinggi langit.\n"
            "`/afk [alasan]` : Pasang status AFK biar Tara yang jawab kalau kamu di-tag."
        ),
        inline=False
    )

    # 🏆 Kategori Leveling & Rank (NEW)
    embed.add_field(
        name="🏆 📈 Leveling & Rank System",
        value=(
            "`/rank [@user]` : Nampilin kartu visual Level & progress XP kamu (atau member lain).\n"
            "`/leaderboard level` : Papan peringkat member paling aktif chat di server.\n"
            "`/profile [@user]` : Kartu profil (bio, badge, level, koin) yang bisa di-screenshot.\n"
            "`/setbio [teks]` : Atur bio singkat buat kartu profil kamu.\n"
            "*Tips: makin sering chat (dengan jeda), XP kamu makin nambah otomatis!*"
        ),
        inline=False
    )

    # 📅 Kategori Event Rutin (NEW)
    embed.add_field(
        name="📅 🗓️ Event Rutin Mingguan",
        value=(
            "`/event create` : Jadwalin event rutin mingguan (Malam Curhat, Movie Night, dll) — Admin only.\n"
            "`/event list` : Lihat semua event rutin & kapan jadwal berikutnya.\n"
            "`/event delete` : Hapus jadwal event rutin — Admin only.\n"
            "*Tara bakal otomatis ngepost pengumuman + reminder 30 menit sebelumnya, lengkap sama tombol RSVP!*"
        ),
        inline=False
    )

    # 🛡️ Kategori Moderasi (Admin)
    embed.add_field(
        name="🛡️ ⚙️ Moderasi Server (Khusus Staff)",
        value=(
            "`/kick` & `/ban` : Mengusir warga nakal dari server.\n"
            "`/timeout`, `/mute`, `/unmute` : Menghukum warga yang berisik/toxic.\n"
            "`/clear [jumlah]` : Menghapus pesan chat secara masal biar bersih.\n"
            "`/setup-verify` & `/setup-rules` : Memasang sistem keamanan server."
        ),
        inline=False
    )

    # 🤖 Kategori Utilitas & Dev
    embed.add_field(
        name="🤖 📊 Utilitas & Info Bot",
        value=(
            "`/hai` : Menyapa Tara biar disapa balik.\n"
            "`/ping` : Mengecek kecepatan respon (latensi) bot Tara.\n"
            "`/invite` : *(Khusus Dev)* Mengambil link invite permanen server Literata ID.\n"
            "`/changelog [versi]` : *(Khusus Dev)* Mengirimkan log update terbaru.\n"
            "`/logoff` : *(Khusus Dev)* Mematikan sistem bot Tara."
        ),
        inline=False
    )
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(
        text="Powered by Literata Dev Team ©2026 | @whoisezza._",
        icon_url=interaction.user.display_avatar.url
    )
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    await interaction.response.send_message(embed=embed)

# ------------------------------------------------------------------------------
# SERVER INFO COMMAND (/about-server [dev only]) 
# ------------------------------------------------------------------------------

@bot.tree.command(name="about-server", description="Meminta Tara menjelaskan tentang server Literata ID dengan tampilan estetik")
@app_commands.checks.has_permissions(administrator=True)
async def about_server(interaction: discord.Interaction):
    BANNER_URL = "https://tenor.com/bsvsy.gif" #<===== insert gif

    embed = discord.Embed(
        title="✨ 🦎 SELAMAT DATANG DI RUMAH LITERATA ID 🦎 ✨",
        description=(
            "***Halo warga baru! Tara di sini buat nemenin kamu~***\n\n"
            "Nama **Literata** sendiri lahir dari kata *\"literasi\"* — karena di sini, kita "
            "percaya kalau ngobrol, berkarya, dan main bareng itu semua bisa jadi bentuk belajar "
            "yang seru. Ini bukan cuma sekumpulan channel dan voice chat, tapi **rumah** buat kamu "
            "yang pengen lepas penat, cari circle baru, atau sekadar butuh temen ngobrol pas gabut. 💚"
        ),
        color=discord.Color.from_rgb(30, 215, 96) #<===== custom colour for embed
    )

    embed.add_field(
        name="🚀 Visi Kami",
        value=">>> Membangun ruang di mana **literasi, kreativitas, dan gaming** bisa hidup berdampingan — tempat setiap individu bebas berbagi, bertumbuh, dan jadi versi terbaik dirinya tanpa takut dihakimi.",
        inline=False
    )
    embed.add_field(
        name="📚 Literasi",
        value="Diskusi buku, film, ide receh, sampai obrolan berat — semua wadah pikiran kita ada di sini.",
        inline=True
    )
    embed.add_field(
        name="🎨 Kreativitas",
        value="Pamer karya, tukar ide, atau kolab bareng member lain yang sama-sama suka bikin sesuatu.",
        inline=True
    )
    embed.add_field(
        name="🎮 Gaming",
        value="Cari squad mabar, ngobrolin meta terbaru, atau sekadar nonton temen main — semua asik!",
        inline=True
    )
    embed.add_field(
        name="🌿 Vibe Sehari-hari",
        value=(
            "• **Nongkrong Santai:** Ngobrol tanpa topik berat.\n"
            "• **Music Society:** Request lagu kesukaanmu lewat Tara.\n"
            "• **Mini Games & Bot Fun:** Cek kodam, ship-shippan, sampai TOD!\n"
            "• **Circle Positif:** Nemuin temen mabar atau temen curhat."
        ),
        inline=False
    )
    embed.add_field(
        name="📜 Tara's Little Rules",
        value=(
            "Satu hal yang Tara minta: **Saling Respect yaw!** "
            "Jangan galak-galak sama member lain ya, biar Literata tetep adem kayak kulit bunglon kena embun pagi. 💚"
        ),
        inline=False
    )
    embed.set_image(url=BANNER_URL)
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    footer_text = "Handcrafted with 💚 by @whoisezza._ | Literata Dev Team © 2026"
    avatar_url = bot.user.display_avatar.url # Bisa diganti foto Bang Eja/Kak Kirax
    embed.set_footer(text=footer_text, icon_url=avatar_url)
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

    await interaction.response.send_message(embed=embed)

# ------------------------------------------------------------------------------
# LOCAL FILE PLAYBACK (/playmp3)
# ------------------------------------------------------------------------------

@bot.tree.command(name="playmp3", description="🎵 Putar file MP3/Audio langsung dari perangkatmu")
async def playmp3(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer()
    if not interaction.user.voice:
        await interaction.followup.send("❌ Kamu harus masuk ke Voice Channel dulu jer!", ephemeral=True)
        return

    vc = interaction.guild.voice_client
    if not vc:
        vc = await interaction.user.voice.channel.connect()
    if not file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
        await interaction.followup.send("❌ Tolong kirimkan file audio yang valid (contoh: .mp3, .wav)!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    lagu_baru = {
        'title': file.filename,
        'url': file.url,
        'webpage_url': file.url   # Disamakan agar tidak error jika dipanggil fungsi lain
    }

    queues[guild_id].append(lagu_baru)
    if not vc.is_playing() and not vc.is_paused():
        item = queues[guild_id].pop(0)

        try:
            source = discord.FFmpegPCMAudio(item['url'], **get_ffmpeg_options(guild_id))
            vc.play(source, after=lambda e: interaction.client.loop.create_task(process_next_song(interaction, guild_id)))
            embed = discord.Embed(
                title="▶️ Sedang Memutar File MP3",
                description=f"**{item['title']}**",
                color=discord.Color.from_rgb(30, 215, 96) # Warna Hijau Tara
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Gagal memutar file: {e}")
    else:
        embed = discord.Embed(
            title="✅ File Audio Masuk Antrean",
            description=f"**{file.filename}** telah ditambahkan ke antrean nomor **{len(queues[guild_id])}**.",
            color=discord.Color.from_rgb(30, 215, 96)
        )
        await interaction.followup.send(embed=embed)

# ==============================================================================
# 6. RUN BOT
# ==============================================================================
if __name__ == '__main__':
    load_dotenv()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") #<===== insert Token melalui .env

    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ ERROR: 'DISCORD_TOKEN' tidak ditemukan! Periksa kembali file .env atau token.env kamu.")
