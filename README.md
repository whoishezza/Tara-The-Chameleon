<div align="center">

  <img src="./assets/literata-pixel-text.svg" alt="LITERATA" width="480"/>
  <br/>
  <img src="./assets/literata-chameleon.svg" alt="Literata Chameleon" width="220"/>

  # Tara — Literata Community Discord Bot

  Multipurpose Discord bot built for the **Literata ID** community — music, moderation, voice channel management, mini-games, and a bit of AI-powered personality.

  ![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
  ![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)
  ![License](https://img.shields.io/badge/license-MIT-brightgreen)
  ![Status](https://img.shields.io/badge/status-active-success)

</div>

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)
- [License](#license)

## About

Tara isn't just another utility bot — she's the resident chameleon of Literata ID, built to keep the server organized, entertained, and a little more alive. From spinning up music queues to managing temporary voice channels and chatting back with her own AI-driven persona, Tara handles the day-to-day so the community can focus on, well, being a community.

## Features

- 🎵 **Music** — play, queue, skip, and apply audio filters (bassboost, 8D, nightcore, and more) straight from voice channels.
- 🛡️ **Moderation** — kick, ban, timeout/mute, and anti-spam & anti-scam-link protection.
- 🔊 **Voice Channel Management** — auto-generated temporary VCs with owner controls (lock, unlock, limit, permit, rename).
- 🎮 **Mini-Games** — Truth or Dare, Roast, Ship/Compatibility, and a fun "Khodam" checker.
- 🎤 **Lyrics Lookup** — fetch song lyrics on demand via Genius.
- 🤖 **AI Persona (Tara)** — a Gemini-powered conversational personality that responds naturally when mentioned.
- ✅ **Server Utilities** — reaction-based verification, welcome messages, help & about-server commands.

## Project Structure

```
literata-bot/
├── Literata_Bot_Code_Fixed.py   # Main bot source
├── requirements.txt              # Python dependencies
├── .gitignore                    # Keeps .env and cache out of git
├── LICENSE.txt                   # MIT License
├── README.md                     # You are here
└── assets/
    ├── literata-pixel-text.svg   # Wordmark logo
    └── literata-chameleon.svg    # Mascot art
```

## Getting Started

### Prerequisites
- Python 3.11+
- [FFmpeg](https://ffmpeg.org/) installed and accessible in your system PATH
- A Discord bot application & token
- A [Genius API](https://genius.com/api-clients) client access token
- A Gemini API key

### Installation

```bash
git clone https://github.com/Whoishezza/literata-bot.git
cd literata-bot
pip install -r requirements.txt
```

### Configuration

Credentials are loaded from environment variables — create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
GENIUS_TOKEN=your_genius_access_token
GEMINI_API_KEY=your_gemini_api_key
```

> ⚠️ Never commit your `.env` file. It's already excluded via `.gitignore`.

### Run the bot

```bash
python Literata_Bot_Code_Fixed.py
```

## Tech Stack

`discord.py` · `yt-dlp` · `aiohttp` · `lyricsgenius` · `google-genai` · `python-dotenv` · `pillow`

## License

This project is licensed under the MIT License — see [LICENSE.txt](./LICENSE.txt) for details.

---

<div align="center">

Built and maintained by **Hezza** ([@Whoishezza](https://github.com/Whoishezza))
Geography Major @ Lambung Mangkurat University

📧 newhezzamaulana123@gmail.com · Discord: `whoisezza._`

</div>
