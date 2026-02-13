from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.config import load_settings
from app.pipeline.daily_job import DailyJob
from app.pipeline.feedback_job import FeedbackJob
from app.pipeline.weekly_report_job import WeeklyReportJob


def _load_dotenv(project_root: Path) -> None:
    env_path = project_root / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run daily language-learning email jobs")
    parser.add_argument("--dry-run", action="store_true", help="Generate lesson/report HTML, do not send email")
    parser.add_argument("--feedback-only", action="store_true", help="Only ingest feedback emails")
    parser.add_argument("--weekly-report-only", action="store_true", help="Only send weekly report email")
    parser.add_argument(
        "--ingest-feedback",
        action="store_true",
        help="Ingest feedback first, then run requested email job",
    )
    return parser.parse_args()


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    _load_dotenv(project_root)

    args = parse_args()
    settings = load_settings()

    if args.feedback_only:
        feedback_job = FeedbackJob(settings=settings)
        feedback_job.run()
        return

    if args.ingest_feedback:
        feedback_job = FeedbackJob(settings=settings)
        feedback_job.run()

    dry_run = args.dry_run or settings.dry_run

    if args.weekly_report_only:
        weekly_job = WeeklyReportJob(settings=settings)
        weekly_job.run(dry_run=dry_run)
        return

    job = DailyJob(settings=settings)
    job.run(dry_run=dry_run)


if __name__ == "__main__":
    main()
