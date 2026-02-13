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

## Quick start
1. Create virtual environment and install deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create `.env` from `.env.example` and fill required values.
3. Dry run (no email, output HTML preview):
   ```bash
   python -m app.main --dry-run
   ```
4. Ingest feedback only:
   ```bash
   python -m app.main --feedback-only
   ```
5. Real run (send email):
   ```bash
   python -m app.main
   ```

## How feedback works
- In each daily email, every word has 3 actions: `完全不懂` / `隐约懂点` / `熟悉`.
- Clicking action opens a mail draft (`mailto:`) prefilled with a secure command.
- You send that draft from iPhone or Mac mail app.
- GitHub Action `feedback_ingest.yml` reads new feedback emails via IMAP and updates:
  - `data/progress/vocabulary_status.json`
  - `data/progress/grammar_status.json`
  - `data/progress/feedback_log.json`

## GitHub Actions secrets
Set these repository secrets:
- `GEMINI_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`
- `IMAP_HOST` (default `imap.gmail.com`)
- `IMAP_PORT` (default `993`)
- `IMAP_USER`
- `IMAP_PASSWORD`
- `FEEDBACK_EMAIL`
- `FEEDBACK_SUBJECT_PREFIX` (default `[LLDN]`)
- `FEEDBACK_TOKEN` (long random string)
- `FEEDBACK_ALLOWED_SENDERS` (comma-separated email list)

Optional:
- `TARGET_LANGUAGE` (default `de`)
- `CEFR_LEVEL` (default `A1`)
- `EDGE_TTS_VOICE`
- `DE_RSS_URLS`

## Notes
- German is fully wired for V1.
- French/Japanese language packs are pre-created as extension points.
- Japanese TTS provider can be swapped later without changing pipeline structure.
- Email clients do not reliably support inline checkbox submission; this project uses mailto command links as the cross-platform fallback.
