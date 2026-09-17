
import httpx
from app.core.config import settings
from app.models.domain import NormalizedInput

class SlackClient:
    def __init__(self, token: str | None = None):
        self.token = token or settings.slack_bot_token
        if not self.token:
            raise RuntimeError('SLACK_BOT_TOKEN is not configured')
        self.base_url='https://slack.com/api'

    def _headers(self): return {'Authorization': f'Bearer {self.token}'}

    def api(self, method: str, **params):
        response=httpx.get(f'{self.base_url}/{method}', headers=self._headers(), params=params, timeout=30)
        response.raise_for_status(); payload=response.json()
        if not payload.get('ok'):
            raise RuntimeError(payload.get('error','Slack API error'))
        return payload

    def conversations_history(self, channel_id: str, cursor: str | None = None, limit: int = 200):
        return self.api('conversations.history', channel=channel_id, cursor=cursor, limit=limit)

    def conversations_replies(self, channel_id: str, ts: str, cursor: str | None = None, limit: int = 200):
        return self.api('conversations.replies', channel=channel_id, ts=ts, cursor=cursor, limit=limit)

    def post_message(self, channel_id: str, text: str, thread_ts: str | None = None):
        payload={'channel':channel_id,'text':text}
        if thread_ts: payload['thread_ts']=thread_ts
        response=httpx.post(f'{self.base_url}/chat.postMessage', headers=self._headers(), json=payload, timeout=30)
        response.raise_for_status(); data=response.json()
        if not data.get('ok'): raise RuntimeError(data.get('error','Slack API error'))
        return data
