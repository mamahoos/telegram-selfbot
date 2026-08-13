# Telegram SelfBot

Production-grade Telegram **user-session** selfbot built with [Hydrogram](https://docs.hydrogram.org), Clean Architecture, and a plugin-based command system.

## Features

| Area | Commands | Description |
|------|----------|-------------|
| Utility | `.id`, `.date`, `.json` | Chat id, Jalali date, API JSON dumps |
| Reactions | `.react` / `.r` | Per-chat auto-reactions using chat-allowed emojis |
| Stickers | `.tosticker`, `.newpack`, `.addsticker` | WebP pipeline and sticker set management |
| Media | `.photo`, `.gif`, `.vmsg`, `.tovoice` | Media pranks: GIF video notes, audio as voice, … |
| Stream | `.stream` / `.type` | Type text progressively via message edits |
| Awk | `.awk`, `.awkx` | Simple awk program or full CLI on replied text |
| Tag | `.tag` | Mention all group members (chained messages when large) |
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
- ffmpeg (for video → GIF)
- rlottie (via `rlottie-python`, for TGS animated stickers → GIF)
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

Login is a separate, one-time step from running the bot. `docker compose up -d`
runs detached with no TTY, so it can never receive the phone-code/2FA prompt —
`docker compose run` allocates one automatically and attaches your terminal.

```bash
cp .env.example .env

# 1. Build the image
docker compose build

# 2. One-time interactive login (creates the session file, then exits)
docker compose run --rm selfbot python -m app.login

# 3. Run the bot detached, reusing the saved session
docker compose up -d
docker compose logs -f selfbot
```

Re-authenticating (new number, revoked session, etc.): delete the file under
`./volumes/sessions/`, then repeat step 2.

If you ever run `docker compose up` before logging in, the container exits
immediately with a clear log message instead of hanging — it checks for stdin
being a TTY before falling into a prompt no one can answer.

### Releases (GHCR)

Pushing a version tag (e.g. `v0.1.0`) runs [`.github/workflows/release.yml`](.github/workflows/release.yml):

1. Tests (ruff, mypy, pytest)
2. Builds and pushes `ghcr.io/<owner>/telegram-selfbot:<version>` to GitHub Container Registry
3. Creates a GitHub Release with a downloadable `telegram-selfbot-vX.Y.Z.tar.gz` image archive

```bash
git tag v0.1.0
git push origin v0.1.0
```

Pull the published image:

```bash
docker pull ghcr.io/mamahoos/telegram-selfbot:0.1.0
```

Make the package public once under **GitHub → Packages → telegram-selfbot → Package settings** if pulls require login.

Volumes:

- `./volumes/sessions` — Telegram session (auth credential; back this up, never commit it)
- `./data` — persisted app state (`state.json`)
- `./logs` — JSON logs
- `./tmp` — transient media files

## Deploying to a server

No deploy script — three `docker compose` commands, run over SSH.

```bash
# On the server
git clone https://github.com/mamahoos/telegram-selfbot.git
cd telegram-selfbot
cp .env.example .env
nano .env   # fill in API_ID, API_HASH, PHONE_NUMBER

docker compose build
```

Login needs a real terminal attached, so do it over `ssh -t` (not a background
job, not CI):

```bash
ssh -t your-server 'cd telegram-selfbot && docker compose run --rm selfbot python -m app.login'
```

Enter the phone code (and 2FA password if you have one) when prompted. This
writes the session file to `./volumes/sessions/` on the server and exits —
no bot logic runs yet.

Then start it detached, which is safe to do unattended from here on:

```bash
ssh your-server 'cd telegram-selfbot && docker compose up -d'
ssh your-server 'cd telegram-selfbot && docker compose logs -f selfbot'
```

`restart: unless-stopped` in `docker-compose.yml` means it survives reboots
and crashes without a systemd unit or process manager.

**Shipping a later change:**

```bash
ssh your-server 'cd telegram-selfbot && git pull && docker compose up -d --build'
```

This reuses the existing session — no login step needed again unless
`./volumes/sessions/*.session` is deleted or Telegram revokes it (in which
case repeat the login command above).

**Re-authenticating:** delete the file under `./volumes/sessions/` on the
server, then repeat the `app.login` step.

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
| `SESSION_DIR` | Where the `.session` file lives (default `volumes/sessions`) |
| `REACTION_*` | Cooldown, retries, fallback emoji list |
| `FFMPEG_*` | Binary path and timeout |
| `STICKER_MAX_DIMENSION` | WebP sticker size (default 512) |
| `STREAM_EDIT_DELAY_SECONDS` | Delay between stream edits (default 0.5) |
| `STREAM_EDIT_MAX_RETRIES` | Retries on edit failure (default 3) |

## Commands reference

Send commands as **outgoing messages** in any chat (they are edited in place):

- `.id` — show chat id and type
- `.date` — one-line Jalali date in Finglish (`Jomee, 26 Ordibehesht 1405`)
- `.json` — full chat API JSON (no reply) or replied message JSON (`from_user` included); sends a file if output exceeds the inline limit
- `.react` / `.r` — toggle random auto-reactions in the current chat
- `.tosticker` — reply to a photo → send as sticker
- `.newpack <title> [short_name] [emoji]` — create pack from replied image
- `.addsticker <pack_short_name> <emoji>` — add replied image to pack
- `.photo` — reply to sticker → send as photo
- `.gif` — reply to video, video sticker, or TGS sticker → send GIF
- `.vmsg` / `.gif2vm` — reply to GIF → send as round video message
- `.tovoice` / `.voice` — reply to audio/song → send as voice message (OGG Opus)
- `.stream <text>` / `.type <text>` — type text character-by-character (skips whitespace-only steps; default 0.5s between edits)
- `.awk {print NR, $0}` — simple mode: program after `.awk`, no quotes
- `.awkx -F: '{print $2}'` — advanced mode: full awk CLI (`-F`, `-f`, …) via shlex
- `.tag` — mention all members (`@username` or linked name, ` · ` separated); groups/supergroups only
- `.help` — list commands

## License

[MIT](./LICENSE)
