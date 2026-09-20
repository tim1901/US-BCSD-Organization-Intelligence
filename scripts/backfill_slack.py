"""Queue a one-time Slack historical backfill for the connected workspace.

Usage:
    python scripts/backfill_slack.py --all
    python scripts/backfill_slack.py --channel C123456789
"""

from __future__ import annotations

import argparse

from app.core.config import settings
from app.ingestion.slack import SlackIngestionService
from app.integrations.slack import SlackClient
from app.storage.supabase import close_pool


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="backfill all visible public/private channels")
    parser.add_argument("--channel", action="append", dest="channels", help="backfill a specific Slack channel ID")
    args = parser.parse_args()

    if not args.all and not args.channels:
        parser.error("Use --all or one or more --channel values")

    client = SlackClient()
    service = SlackIngestionService(slack=client)
    try:
        count = service.sync_workspace(
            all_channels=args.all,
            channel_ids=args.channels,
        )
        print(
            f"[SLACK] queued {count} channel backfill jobs for workspace "
            f"{settings.slack_workspace_id}"
        )
    finally:
        client.close()
        close_pool()


if __name__ == "__main__":
    main()
