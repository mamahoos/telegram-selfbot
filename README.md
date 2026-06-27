# Telegram SelfBot

Selfbot تلگرام با **user session** (Hydrogram) — نه Bot API. دستورات را به‌صورت پیام outgoing می‌فرستید؛ ربات همان پیام را edit می‌کند.

معماری: Clean Architecture، plugin-based، type-safe (mypy strict).

---

## فهرست

- [پیش‌نیازها](#پیش‌نیازها)
- [راه‌اندازی گام‌به‌گام](#راه‌اندازی-گام‌به‌گام)
- [تنظیم LLM](#تنظیم-llm)
- [فایل‌های پروفایل و لحن](#فایل‌های-پروفایل-و-لحن)
- [دستورات AI](#دستورات-ai)
- [سایر دستورات](#سایر-دستورات)
- [Docker](#docker)
- [Deploy روی سرور](#deploy-روی-سرور)
- [توسعه و تست](#توسعه-و-تست)
- [امنیت و Git](#امنیت-و-git)
- [معماری](#معماری)

---

## پیش‌نیازها

| مورد | نسخه / توضیح |
|------|----------------|
| Python | 3.11+ |
| Poetry | 2.x (یا `.venv` از قبل ساخته‌شده) |
| ffmpeg | برای `.gif`, `.vmsg`, `.tovoice` |
| rlottie | از طریق `rlottie-python` (TGS → GIF) |
| Telegram API | `API_ID` + `API_HASH` از [my.telegram.org](https://my.telegram.org/apps) |
| LLM (اختیاری) | API سازگار با OpenAI — برای `.ai` و discuss |

---

## راه‌اندازی گام‌به‌گام

### ۱. کلون و env

```bash
git clone <repo-url>
cd self-bot   # یا bots/self-bot در monorepo

cp .env.example .env
```

در `.env` حداقل این‌ها را پر کن:

```env
API_ID=12345678
API_HASH=your_api_hash
PHONE_NUMBER=+989XXXXXXXXX
SESSION_NAME=selfbot
```

### ۲. نصب وابستگی‌ها

```bash
poetry install
# یا: python -m venv .venv && .venv/bin/pip install -e .
```

### ۳. اولین login

```bash
poetry run selfbot
# یا: ./scripts/run.sh
```

Hydrogram کد SMS و در صورت نیاز رمز 2FA را می‌پرسد. session در `data/<SESSION_NAME>.session` ذخیره می‌شود.

### ۴. پروفایل (برای discuss / `.answer`)

```bash
cp data/profile.md.example data/profile.md
# فایل را با موضع‌ها و لحن خودت ویرایش کن — راهنمای کامل پایین
```

### ۵. LLM (برای `.ai` و discuss)

`LLM_API_KEY` و در صورت نیاز `LLM_API_BASE_URL` را در `.env` بگذار — [بخش LLM](#تنظیم-llm).

### ۶. تست

در هر چت، یک پیام بفرست:

```
.help
.id
```

---

## تنظیم LLM

هر دو plugin **`ai`** و **`discuss`** از یک client OpenAI-compatible استفاده می‌کنند.

### متغیرهای env

| متغیر | پیش‌فرض | توضیح |
|-------|---------|--------|
| `LLM_API_BASE_URL` | `http://127.0.0.1:3001/v1` | آدرس `/v1` (OpenAI-compatible) |
| `LLM_API_KEY` | *(خالی)* | اگر API key لازم است |
| `LLM_MODEL` | `auto` | نام مدل |
| `LLM_TIMEOUT_SECONDS` | `120` | timeout درخواست |
| `AI_MAX_TOKENS` | `2000` | سقف توکن `.ai` |

اگر `LLM_API_KEY` خالی باشد، client غیرفعال می‌ماند و دستورات AI پیام «LLM تنظیم نشده» می‌دهند.

### مثال: FreeLLMAPI روی localhost

```env
LLM_API_BASE_URL=http://127.0.0.1:3001/v1
LLM_API_KEY=your-key-if-needed
LLM_MODEL=auto
```

### مثال: Docker + LLM روی host

در `docker-compose.yml` مقدار `extra_hosts: host.docker.internal:host-gateway` تنظیم شده. از داخل container:

```env
LLM_API_BASE_URL=http://host.docker.internal:3001/v1
```

### مثال: OpenAI / OpenRouter / سایر

```env
LLM_API_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...
LLM_MODEL=anthropic/claude-3.5-sonnet
```

### فرمت خروجی `.ai`

مدل **Markdown** می‌نویسد؛ سرور آن را به Telegram HTML تبدیل می‌کند (الگوی Hermes Agent: Markdown in → formatted out). اگر parse خطا بدهد → plain text.

---

## فایل‌های پروفایل و لحن

این فایل‌ها **شخصی** هستند و در git commit نمی‌شوند. فقط templateها در repo هستند.

### ساختار پوشه `data/`

```
data/
├── .gitkeep
├── profile.md.example          ← template (در git)
├── profile.md                  ← اصلی — YOU (gitignore)
├── cognitive-profile.md        ← خلاصه §۰ — YOU (gitignore)
└── telegram-voice/
    ├── README.md               ← مستندات (در git)
    ├── .gitkeep
    ├── voice.compact.txt       ← نمونه لحن L001|… — YOU (gitignore)
    ├── scenario-map.md         ← نقشه سناریو → خطوط — YOU (gitignore)
    └── my-messages.txt         ← آرشیو خام — YOU (gitignore)
```

مسیرها با env قابل تغییرند:

```env
DISCUSS_PROFILE_PATH=data/profile.md
DISCUSS_COGNITIVE_PROFILE_PATH=data/cognitive-profile.md
DISCUSS_VOICE_PATH=data/telegram-voice/voice.compact.txt
```

### `profile.md` — فایل اصلی

فایل Markdown با sectionهای مشخص. loader بخش‌های زیر را جدا می‌کند:

| Section | کاربرد در pipeline |
|---------|-------------------|
| `## ۰. پروفایل شناختی` | شخصیت ذهنی — لایه ۲ (worldview draft) |
| `## هویت سیاسی-اقتصادی` | موضع کلی |
| `## ۱.` تا `## ۵.` | فلسفه، اقتصاد، سیاست، اجتماع، خارجی |
| `## ۶. لحن و سبک استدلال` | قوانین لحن — لایه ۳ (tone polish) |
| `## ۷.` | چک‌لیست مواضع |
| `## ۸.` | زمینه شخصی (لو نده) |
| `## ۹.` | جمله خلاصه برای prompt کوتاه |

شروع:

```bash
cp data/profile.md.example data/profile.md
```

سپس sectionها را پر کن. `.profile` خلاصه بارگذاری را نشان می‌دهد.

### `cognitive-profile.md` — نسخه فشرده §۰

خلاصه کوتاه از بخش شناختی برای کم‌کردن توکن. اگر فایل نباشد، loader خودش `## ۰.` را از `profile.md` می‌خواند.

```bash
# اختیاری — برای promptهای کوتاه‌تر
# محتوای §۰ profile.md را خلاصه کن و ذخیره کن
```

### `voice.compact.txt` — corpus لحن

فرمت هر خط:

```text
L001|متن نمونه پیام تو بدون metadata
L002|یک جمله کوتاه دیگر
```

- پیشوند `L` + سه رقم — شناسه خط
- جداکننده `|`
- بدون تاریخ، نام، URL (برای کم‌توکن بودن)

### سناریوها (تشخیص لحن)

در `.answer` لایه ۱ پیام طرف را تحلیل می‌کند و سناریو **A–G** را برمی‌گرداند:

| کد | موقعیت بحث |
|----|------------|
| **A** | utopia / دولت بی‌عمل / تعرفه / اقتصاد |
| **B** | تاریخ / اصل+اما / مثال موازی |
| **C** | اتهام چپ / رفع مانع ≠ مداخله |
| **D** | ضربه‌ای / سؤال / فشار |
| **E** | موافقت کوتاه |
| **F** | حقوق فردی / زن / پزشکی |
| **G** | Fallback — سناریو نامشخص |

بر اساس سنario، خطوط نمونه از `voice.compact.txt` بارگذاری می‌شود (مثلاً D → `L002`, `L004`, …). جزئیات در `data/telegram-voice/README.md`.

`scenario-map.md` مرجع انسانی است؛ mapping خطوط در کد (`discuss_profile_loader.py`) هم تعریف شده.

### چک‌لیست آماده‌سازی discuss

```bash
# حداقل
[ ] data/profile.md ساخته شده (§۰–§۶ حداقل)
[ ] LLM_API_KEY در .env

# توصیه‌شده برای لحن بهتر
[ ] data/cognitive-profile.md
[ ] data/telegram-voice/voice.compact.txt
[ ] data/telegram-voice/scenario-map.md (مرجع)
```

---

## دستورات AI

| دستور | LLM call | پروفایل | کاربرد |
|-------|----------|---------|--------|
| `.ai <سوال>` | ۱ | ❌ | پاسخ سریع با فرمت Telegram |
| `.ai` (reply) | ۱ | ❌ | پاسخ به پیام ریپلای‌شده |
| `.assist` / `.reply` / `.draft` | ۱ | ✅ | پیش‌نویس بحث با worldview |
| `.answer` | ۴ لایه + sanitize | ✅ | تحلیل طرف → پاسخ با لحن تو |
| `.profile` | — | — | وضعیت بارگذاری پروفایل |

### `.ai`

```
.ai یک کد پایتون بنویس که print("سلام") کند
```

یا روی پیام ریپلای: `.ai`

### `.answer` (pipeline چندلایه)

1. **لایه ۱** — تحلیل استدلال طرف (JSON: scenario, claims, strategy)
2. **لایه ۲** — پیش‌نویس بر اساس پروفایل ذهنی + worldview
3. **لایه ۳** — ویرایش لحن با §۶ + نمونه‌های voice
4. **پاک‌سازی** — حذف markdown/planning artifacts مدل

```
# روی پیام طرف ریپلای کن:
.answer
```

### `.assist`

```
.assist چطور به این نقد جواب بدم؟
# یا روی پیام ریپلای + .reply
```

---

## سایر دستورات

| Plugin | دستور | توضیح |
|--------|--------|--------|
| utility | `.id` | chat id و نوع چت |
| utility | `.date` | تاریخ شمسی (Finglish) |
| utility | `.json` | dump JSON پیام/چت |
| reactions | `.react` / `.r` | auto-reaction در چت |
| stickers | `.tosticker`, `.newpack`, `.addsticker` | pipeline استیکر |
| media | `.photo`, `.gif`, `.vmsg`, `.tovoice` | تبدیل media |
| stream | `.stream` / `.type` | تایپ تدریجی با edit |
| awk | `.awk`, `.awkx` | awk روی متن ریپلای |
| tag | `.tag` | mention همه اعضای گروه |
| system | `.help` | لیست دستورات |

---

## Docker

```bash
cp .env.example .env
# .env را ویرایش کن

docker compose up --build -d
docker compose logs -f selfbot
```

Volumeها:

| مسیر | محتوا |
|------|--------|
| `./data` | session + پروفایل + state |
| `./logs` | JSON logs |
| `./tmp` | فایل موقت media |

### اولین login در Docker

```bash
docker compose run --rm -it selfbot
# SMS + 2FA
docker compose up -d
```

Session در `./data/` روی host می‌ماند (نه داخل image).

---

## Deploy روی سرور

```bash
cp deploy.env.example deploy.env
# deploy.env را ویرایش کن — این فایل gitignore است

chmod +x deploy.sh scripts/run.sh
./deploy.sh
```

`deploy.env` (gitignore):

```env
DEPLOY_HOST=your.server.example.com
DEPLOY_USER=root
DEPLOY_REMOTE=/srv/tg-bots/self-bot
```

Credentials فقط از env به `.env` سرور می‌روند (از لپ‌تاپ sync نمی‌شوند):

```bash
API_ID='...' API_HASH='...' PHONE_NUMBER='+98...' LLM_API_KEY='...' ./deploy.sh
```

| Flag | کار |
|------|-----|
| `DEPLOY_NO_START=1` | فقط rsync + build |
| `SYNC_DATA=1` | sync `data/` (بدون `*.session*`) |

قبل از push:

```bash
chmod +x scripts/check-secrets.sh
./scripts/check-secrets.sh
```

اولین بار روی سرور:

```bash
ssh user@your-server
cd /srv/tg-bots/self-bot   # یا DEPLOY_REMOTE تو
docker compose run --rm -it selfbot
docker compose up -d
```

---

## توسعه و تست

```bash
poetry install
poetry run pytest
./scripts/lint.sh          # ruff + mypy
pre-commit install         # اختیاری
```

Release: tag `vX.Y.Z` → CI → GHCR image + tarball (`.github/workflows/release.yml`).

---

## امنیت و Git

**هرگز commit نکن:**

| دسته | فایل‌ها |
|------|---------|
| Secrets | `.env`, `deploy.env` |
| Session | `*.session*` |
| پروفایل شخصی | `data/profile.md`, `data/cognitive-profile.md` |
| corpus لحن | `voice.compact.txt`, `scenario-map.md`, `my-messages.txt` |
| Runtime | `logs/`, `tmp/` |
| Deploy شخصی | `scripts/deploy-pacman.sh`, `deploy.local.sh` |

**در repo هست:** `.env.example`, `deploy.env.example`, `data/profile.md.example`, `data/telegram-voice/README.md`

```bash
./scripts/check-secrets.sh   # قبل از git push
```

---

## معماری

```
src/app/
├── core/            # DI container, logging
├── config/          # pydantic-settings
├── domain/          # entities, contracts
├── application/     # services, command registry
├── infrastructure/  # Hydrogram, ffmpeg, LLM client
├── presentation/    # handlers, middleware
├── common/          # telegram_html, helpers
└── plugins/         # ai, discuss, media, …
```

اصول:

- handlerها نازک؛ منطق در `services/`
- بدون global state — DI از طریق `Container`
- LLM: `OpenAiChatClient` (httpx, OpenAI-compatible)
- discuss: `DiscussService` + `discuss_profile_loader` + `discuss_output_sanitizer`
- ai: `AiService` + `telegram_html` (Markdown → HTML)

---

## License

MIT
