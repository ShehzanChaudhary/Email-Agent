# Email Agent

An automated mailbox watcher that polls a Gmail inbox over IMAP, detects newly-arrived mail within a rolling time window, and hands each message off to an agent handler for processing. Built as a foundation for a future ReAct-style agent that will read, understand, and act on emails using an LLM via OpenRouter.

## ✅ Current Progress

### Working
- **IMAP polling (`src/adapters/email_reader.py`)**
  - Connects to Gmail (or any IMAP server) using `imaplib`, logs in, and selects the configured folder.
  - Uses `SINCE` to narrow the search to roughly the last day, then filters precisely by each message's `INTERNALDATE` against a cutoff of `now - POLL_INTERVAL_SECONDS` — so effectively only mail received since the last poll is picked up.
  - Fetches messages with `BODY.PEEK[]`, which reads content **without marking the email as read** on the server.
  - Tracks already-handled UIDs in memory so the same message isn't processed twice; UIDs are dropped from tracking once they age out of the candidate window (they can't come back around as "recent").
  - Decodes RFC 2047-encoded headers (e.g. `=?UTF-8?B?...?=`) into plain text.
  - Extracts the email body, preferring `text/plain` and falling back to a tag-stripped version of `text/html`.
  - Extracts attachment **filenames** (not the file contents themselves).
  - On a handler failure for a given email, logs the error and skips marking it processed, so it's retried on the next poll cycle.

- **Polling loop (`main.py`)**
  - `python main.py` → polls forever every `POLL_INTERVAL_SECONDS`, catching and logging exceptions per cycle so one bad cycle doesn't crash the process.
  - `python main.py --once` → runs a single poll pass and exits (useful for testing).
  - Graceful shutdown on `Ctrl+C` (`STATUS: Stopped by user`).

- **Configuration (`config/config.py`)**
  - Loads all settings from environment variables via `python-dotenv`, with sensible defaults for optional values.
  - Fails fast with a clear error if `EMAIL_ADDRESS` / `EMAIL_PASSWORD` are missing when the IMAP connection is attempted.

- **OpenRouter client (`src/adapters/openrouter.py`)**
  - Wraps the OpenAI SDK pointed at OpenRouter's OpenAI-compatible endpoint.
  - `chat()` sends a list of `Message` objects, supports optional JSON-mode responses, and retries failed requests with exponential backoff + jitter.
  - Returns a safe fallback string and `0` tokens if all retries fail, instead of raising.
  - **Not yet wired into the email-handling flow** — it exists as a standalone service.

- **Data models (`src/model.py`)**
  - `Message` — a single chat turn (`role`, `content`) shaped for the OpenRouter API.
  - `EmailMessage` — a parsed-down email (`uid`, `sender`, `subject`, `body`, `date`, `attachments`).

- **Utility (`src/func_runtime.py`)**
  - `@log_execution_time` decorator — logs how long a function took to run; works for both sync and async functions.

- **Logger (`src/adapters/logger.py`)**
  - Console-only logger, `INFO` level by default, timestamps in **IST (UTC+5:30)** regardless of system timezone.
  - Custom log format: `timestamp,ms name LEVEL message`.
  - Suppresses noisy third-party loggers (`requests`, `urllib3.connectionpool`, `azure.core...http_logging_policy`) down to `WARNING`.

### Placeholder (not yet implemented)
- **`src/agent_trigger.py`** — currently just logs that the agent was triggered (uid, sender, subject, body length). This is the hook point where the real ReAct agent (LLM-driven intent detection + reply/action) will eventually live.
- **LLM-driven processing** — `OpenRouterService` is built and functional on its own, but nothing in `trigger_agent` calls it yet.
- **Attachment content handling** — only filenames are currently extracted; attachment bodies aren't downloaded or read.

## 📁 Project Structure

```
Email-Agent/
├── config/
│   └── config.py              # Env-based settings (Config class)
├── src/
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── email_reader.py    # IMAP polling, parsing, dedup — IMAPEmailReader
│   │   ├── logger.py          # IST-timestamped console logger
│   │   └── openrouter.py      # OpenRouterService — LLM chat client w/ retries
│   ├── agent_trigger.py       # trigger_agent() — placeholder handler
│   ├── func_runtime.py        # log_execution_time decorator
│   └── model.py                # Message, EmailMessage dataclasses
├── main.py                     # Entry point — poll_forever() / --once mode
├── requirements.txt
└── .gitignore
```

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```
Required packages (based on imports): `python-dotenv`, `openai`.

### 2. Configure environment variables
Create a `.env` file in the project root:
```dotenv
# Mailbox (IMAP)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your16charapppassword
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_FOLDER=INBOX
POLL_INTERVAL_SECONDS=30

# LLM (OpenRouter)
OPENROUTER_API_KEY=your-openrouter-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODEL=openai/gpt-4o-mini
EMAIL_AGENT_MAX_ITERATIONS=6
```

**Important (Gmail users):** `EMAIL_PASSWORD` must be a **16-character Gmail App Password**, not your normal Gmail password. 2-Step Verification must be enabled on the account, then generate one at:
`https://myaccount.google.com/apppasswords`

### 3. Run the agent
```bash
python main.py            # poll forever
python main.py --once     # single poll cycle, then exit
```

On successful startup:
```
STATUS: Watching your-email@gmail.com (INBOX) every 30s
```
### 4. Example Output
<img width="1626" height="326" alt="image" src="https://github.com/user-attachments/assets/5abeffbb-a927-40ed-abbd-e86df5b223e7" />


## 🧪 Verified Behavior
- [x] IMAP connection + login with App Password
- [x] Continuous polling loop, resilient to per-cycle exceptions
- [x] New emails detected and read without being marked "Seen"
- [x] No duplicate processing across poll cycles
- [x] Clean shutdown on manual interrupt

## 🚧 Next Steps
- [ ] Wire `OpenRouterService.chat()` into `trigger_agent()` to actually generate a response/action from email content
- [ ] Design the ReAct loop (uses `EMAIL_AGENT_MAX_ITERATIONS`) for multi-step reasoning/tool use
- [ ] Decide what "acting" on an email means — auto-reply, label, forward, create a task, etc.
- [ ] Attachment content handling — currently only filenames are extracted; attachment bytes aren't saved or read
- [ ] Consider file-based log persistence (currently console-only, lost on process restart)

## 📝 Notes
- `.env` values must be plain `KEY=value` pairs — no Python expressions. e.g. `IMAP_PORT=993`, not `IMAP_PORT=int(os.environ.get(...))`.
- The "lookback window" for detecting new mail is currently driven directly by `POLL_INTERVAL_SECONDS` (not a separate setting), so shortening the poll interval also shortens how far back each cycle looks.

---
*This README reflects the codebase as reviewed on 2026-09-04 and should be updated as the agent's decision-making logic is built out.*
