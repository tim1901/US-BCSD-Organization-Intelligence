from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings


class SlackApiError(RuntimeError):
    def __init__(self, method: str, error: str, response: dict[str, Any] | None = None):
        super().__init__(f"Slack API {method} failed: {error}")
        self.method = method
        self.error = error
        self.response = response or {}


class SlackClient:
    """Small synchronous Slack Web API client with pagination and rate-limit handling."""

    base_url = "https://slack.com/api/"

    def __init__(self, token: str | None = None, user_token: str | None = None):
        self.token = token or settings.slack_bot_token
        self.user_token = user_token or settings.slack_user_token
        if not self.token:
            raise RuntimeError("SLACK_BOT_TOKEN is not configured")
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.user_client = (
            httpx.Client(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers={"Authorization": f"Bearer {self.user_token}"},
            )
            if self.user_token
            else None
        )

    def close(self) -> None:
        self.client.close()
        if self.user_client:
            self.user_client.close()

    def _call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        use_user_token: bool = False,
    ) -> dict[str, Any]:
        params = {key: value for key, value in (params or {}).items() if value is not None}
        client = self.user_client if use_user_token else self.client
        if client is None:
            raise RuntimeError(
                "SLACK_USER_TOKEN is required for conversations.replies on public/private channels"
            )
        attempts = 0
        while True:
            attempts += 1
            response = client.post(method, data=params)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                if attempts >= settings.slack_api_max_retries:
                    raise SlackApiError(method, "ratelimited", {"retry_after": retry_after})
                time.sleep(min(retry_after, 60))
                continue
            response.raise_for_status()
            payload = response.json()
            if payload.get("ok"):
                return payload
            error = str(payload.get("error", "unknown_error"))
            if error in {"ratelimited", "internal_error", "service_unavailable"} and attempts < settings.slack_api_max_retries:
                time.sleep(min(2 ** (attempts - 1), 30))
                continue
            raise SlackApiError(method, error, payload)

    def paginated(
        self,
        method: str,
        *,
        collection_key: str,
        params: dict[str, Any] | None = None,
        limit: int = 200,
        use_user_token: bool = False,
    ) -> list[dict[str, Any]]:
        cursor: str | None = None
        items: list[dict[str, Any]] = []
        while True:
            page_params = dict(params or {})
            page_params.update({"limit": limit, "cursor": cursor})
            payload = self._call(method, page_params, use_user_token=use_user_token)
            page = payload.get(collection_key, [])
            if isinstance(page, list):
                items.extend(page)
            cursor = (payload.get("response_metadata") or {}).get("next_cursor") or None
            if not cursor:
                break
        return items

    def users(self) -> list[dict[str, Any]]:
        return self.paginated("users.list", collection_key="members", limit=200)

    def channels(self) -> list[dict[str, Any]]:
        return self.paginated(
            "conversations.list",
            collection_key="channels",
            params={
                "types": "public_channel,private_channel",
                "exclude_archived": True,
            },
            limit=200,
        )

    def history(self, channel_id: str) -> list[dict[str, Any]]:
        return self.paginated(
            "conversations.history",
            collection_key="messages",
            params={"channel": channel_id, "include_all_metadata": True},
            limit=100,
        )

    def replies(self, channel_id: str, thread_ts: str) -> list[dict[str, Any]]:
        # Bot tokens with channels:history/groups:history can retrieve thread replies
        # when the bot is a member of the channel.
        return self.paginated(
            "conversations.replies",
            collection_key="messages",
            params={"channel": channel_id, "ts": thread_ts, "include_all_metadata": True},
            limit=100,
        )
