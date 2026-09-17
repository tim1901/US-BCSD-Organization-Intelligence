class SlackDeliveryService:
    def __init__(self, slack_client, response_builder): self.slack=slack_client; self.response_builder=response_builder
    def reply(self, channel_id: str, thread_ts: str | None, answer: str, citations=None):
        text=self.response_builder.build(answer, citations)
        return self.slack.post_message(channel_id, text, thread_ts=thread_ts)
