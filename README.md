# Language Learning Daily News (German-first)

Daily email language coach focused on **A1-A2 German**, with extension interfaces for French and Japanese.

## What this scaffold includes
- Daily RSS news ingestion
- Gemini rewrite into A1-A2 level (~200 words)
- Full Chinese translation of the rewritten news
- 5 key-word detailed explanations
- 1 grammar point from the news with mastery tracking hook
- TTS audio generation (default: `edge-tts`)
- Beautiful HTML email rendering
- SMTP sending (works in GitHub Actions)
- Local JSON state tracking for vocabulary/grammar progress
- Email-as-input feedback loop: click a button in email, send generated command email, workflow ingests and updates JSON
- Weekly statistics email

## Quick start
1. Create virtual environment and install deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create `.env` from `.env.example` and fill required values.
3. Dry run (daily, no email):
   ```bash
   python -m app.main --dry-run
   ```
4. Ingest feedback only:
   ```bash
   python -m app.main --feedback-only
   ```
5. Weekly report only:
   ```bash
   python -m app.main --weekly-report-only
   ```

## How feedback works
- In each daily email, every word has 3 actions: `完全不懂` / `隐约懂点` / `熟悉`.
- Clicking action opens a mail draft (`mailto:`) prefilled with a secure command.
- You send that draft from iPhone or Mac mail app.
- GitHub Action `feedback_ingest.yml` reads new feedback emails and updates:
  - `data/progress/vocabulary_status.json`
  - `data/progress/grammar_status.json`
  - `data/progress/feedback_log.json`

## Minimal GitHub Actions secrets
Required:
- `GEMINI_API_KEY`
- `GMAIL_ADDRESS`
- `GMAIL_APP_PASSWORD`
- `FEEDBACK_TOKEN`

Optional:
- `GEMINI_MODEL` (default `gemini-2.5-flash`)
- `GEMINI_FALLBACK_MODELS` (default `gemini-2.5-flash-lite,gemini-2.0-flash,gemini-flash-latest`)
- `EMAIL_TO` (default equals `GMAIL_ADDRESS`)
- `TARGET_LANGUAGE` (default `de`)
- `CEFR_LEVEL` (default `A1`)
- `EDGE_TTS_VOICE`
- `FEEDBACK_ALLOWED_SENDERS`
- `DE_RSS_URLS`
- `TTS_STRICT` (`1` means audio failure will fail the whole job, default `0`)

## Workflows
- `daily_news_mail.yml`: daily lesson email
- `feedback_ingest.yml`: feedback ingestion every 30 min
- `weekly_report.yml`: weekly statistics report (Sunday UTC)

## Notes
- If you previously set `GEMINI_MODEL=gemini-1.5-flash`, remove or update it.
- `edge-tts` is now pinned to `7.2.7` to match current service protocol changes.
- German is fully wired for V1.
- French/Japanese language packs are pre-created as extension points.
- Japanese TTS provider can be swapped later without changing pipeline structure.
- Email clients do not reliably support inline checkbox submission; this project uses mailto command links as the cross-platform fallback.
