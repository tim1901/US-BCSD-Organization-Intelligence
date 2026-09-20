"""Queue a one-time Slack historical backfill for the connected workspace.

Usage:
    python scripts/backfill_slack.py --list-channels
    python scripts/backfill_slack.py --channel C123456789
    python scripts/backfill_slack.py --all
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
    parser.add_argument(
        "--list-channels",
        action="store_true",
        help="list channels visible to the bot and exit",
    )
    args = parser.parse_args()

    client = SlackClient()
    try:
        if args.list_channels:
            for channel in client.channels():
                visibility = "private" if channel.get("is_private") else "public"
                print(f'{channel["id"]}\t#{channel.get("name", "")}\t{visibility}')
            return

        if not args.all and not args.channels:
            parser.error("Use --all, --channel, or --list-channels")

        service = SlackIngestionService(slack=client)
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
