# Telegram SelfBot

Production-grade Telegram **user-session** selfbot built with [Hydrogram](https://docs.hydrogram.org), Clean Architecture, and a plugin-based command system.

## Features

| Area | Commands | Description |
|------|----------|-------------|
| Utility | `.id`, `.date`, `.info` | Chat metadata and message inspection |
| Reactions | `.react` / `.r` | Per-chat auto-reactions using chat-allowed emojis |
| Stickers | `.tosticker`, `.newpack`, `.addsticker` | WebP pipeline and sticker set management |
| Media | `.photo`, `.gif` | Sticker → image, video → optimized GIF (ffmpeg) |
| System | `.help` | Command discovery |

## Architecture

```
src/app/
├── core/            # DI container, structured logging
├── config/          # pydantic-settings (.env)
├── domain/          # entities, repository contracts
├── application/     # use cases, command registry, services
├── infrastructure/  # Hydrogram, ffmpeg, storage
├── presentation/    # handlers, middleware
└── plugins/         # feature modules (auto-discovered)
```

Design principles:

- **Clean Architecture** — domain does not depend on Hydrogram
- **Plugin system** — each feature registers commands independently
- **Strict typing** — mypy strict mode
- **Structured JSON logs** — rotating files under `logs/`
- **Temp file safety** — context-managed cleanup in `TempFileManager`

## Requirements

- Python 3.13
- Poetry 2.x
- ffmpeg (for `.gif`)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org/apps)

## Quick start

```bash
cp .env.example .env
# Edit .env with API_ID, API_HASH, PHONE_NUMBER

poetry install
poetry run selfbot
```

On first run Hydrogram will prompt for the login code sent to your Telegram account.

## Docker

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f selfbot
```

Volumes:

- `./data` — session + persisted state
- `./logs` — JSON logs
- `./tmp` — transient media files

## Development

```bash
poetry install
poetry run pytest
./scripts/lint.sh
pre-commit install
pre-commit run --all-files
```

## Configuration

See [`.env.example`](.env.example). All secrets are loaded from the environment — nothing is hardcoded.

| Variable | Purpose |
|----------|---------|
| `API_ID` / `API_HASH` | Telegram API application |
| `PHONE_NUMBER` | User account phone (international format) |
| `SESSION_NAME` | Session file basename |
| `REACTION_*` | Cooldown, retries, fallback emoji list |
| `FFMPEG_*` | Binary path and timeout |
| `STICKER_MAX_DIMENSION` | WebP sticker size (default 512) |

## Commands reference

Send commands as **outgoing messages** in any chat (they are edited in place):

- `.id` — show chat id and type
- `.date` — local date/time
- `.info` — metadata for a replied message
- `.react` / `.r` — toggle random auto-reactions in the current chat
- `.tosticker` — reply to a photo → send as sticker
- `.newpack <title> [short_name] [emoji]` — create pack from replied image
- `.addsticker <pack_short_name> <emoji>` — add replied image to pack
- `.photo` — reply to sticker → send as photo
- `.gif` — reply to video → send optimized GIF
- `.help` — list commands

## Security

- Never commit `.env` or `*.session` files
- No `eval` or dynamic code execution
- Commands only run on **your own outgoing** messages

## License

MIT (adjust as needed)
