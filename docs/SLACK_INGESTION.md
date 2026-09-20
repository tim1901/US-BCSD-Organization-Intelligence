# Slack Ingestion

This project uses Slack's Web API for historical backfill and Slack Events API over HTTP for ongoing message ingestion. Slack documents the Web API as the mechanism for historical data and the Events API as the mechanism for real-time events. 

## 1. Slack app configuration

Keep DMs excluded by default.

OAuth scopes required by this ingestion path:

- `channels:read`
- `channels:history`
- `groups:read`
- `groups:history`
- `users:read`

In Slack App Settings → Event Subscriptions:

1. Enable Events.
2. Set the Request URL to:

`https://us-bcsd-intelligence-web.onrender.com/api/slack/events`

3. Add these bot events:
   - `message.channels`
   - `message.groups`
4. Save the configuration.

`message.channels` covers public channel messages and requires `channels:history`; `message.groups` covers private channel messages and requires `groups:history`.

The Slack Events API expects the application to acknowledge the event quickly and then process it asynchronously. This application stores the event and queues a worker job.

## 2. Confirm the app can see channels

Run this from the Render Worker Shell:

```bash
python scripts/backfill_slack.py --list-channels
```

Only channels visible to the bot will be listed. For private channels, the bot must have access to the conversation.

## 3. Start with one channel

Do not start with the entire workspace. First choose one low-risk channel and run:

```bash
python scripts/backfill_slack.py --channel C123456789
```

The command discovers users/channels and queues a historical backfill job. The Render worker then:

1. Fetches channel history.
2. Groups root messages and threads.
3. Fetches thread replies.
4. Stores Slack conversations and messages.
5. Creates source records with provenance.
6. Extracts candidate organizational knowledge with Gemini.
7. Generates embeddings.
8. Writes the extracted memory to PostgreSQL/pgvector.

## 4. Run the full historical backfill

After the single-channel test succeeds:

```bash
python scripts/backfill_slack.py --all
```

Slack's current documentation notes that `conversations.history` and `conversations.replies` can be subject to tighter rate limits for some non-Marketplace apps, including a 1-request-per-minute limit and a maximum of 15 objects per request for affected installations. A large historical workspace can therefore take substantial time. Start small and observe worker behavior before backfilling everything.

## 5. Ongoing ingestion

Once Event Subscriptions are configured, new public/private channel messages are delivered to:

`POST /api/slack/events`

The API route verifies Slack's signature, stores the event idempotently, and creates an `ingest_slack_event` job. The worker reconstructs the affected thread from Slack and updates organizational memory.

This means the HTTP request path remains lightweight and the Gemini/database work stays in the Render worker.

## 6. Safety defaults

- DMs are not ingested.
- Private-channel events are accepted only through the private-channel event path.
- Slack source records retain channel/thread identifiers for provenance.
- The organization database remains the canonical memory store.
- Gemini organizational calls remain stateless; the database stores the resulting memory.
