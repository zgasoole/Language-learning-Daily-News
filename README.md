# Language Learning Daily News (German-first)

Daily email language coach focused on **A1-A2 German**, with extension interfaces for French and Japanese.

## What this scaffold includes
- Daily RSS news ingestion
- Gemini rewrite into A1-A2 level (~200 words)
- Full Chinese translation of the rewritten news
- Sentence-by-sentence bilingual alignment (German left, Chinese right)
- 5 key-word detailed explanations
- 1 grammar point with textbook-style detailed explanation + external learning link
- TTS audio generation (default: `edge-tts`)
- Beautiful HTML email rendering
- SMTP sending (works in GitHub Actions)
- Local JSON state tracking for vocabulary/grammar progress
- Email-as-input feedback loop: one submission can update all 5 words + grammar
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

## Feedback flow (single submission)
- In the daily email, a feedback form is rendered.
- You can mark all 5 words + grammar status first.
- Click one submit button to generate one feedback email.
- Send that email from iPhone/Mac Mail app.
- `feedback_ingest.yml` reads it and updates:
  - `data/progress/vocabulary_status.json`
  - `data/progress/grammar_status.json`
  - `data/progress/feedback_log.json`
- If your mail client does not support form submission, use the fallback “single draft” link in the email.

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
