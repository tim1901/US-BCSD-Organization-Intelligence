class ConversationContext:
    def build(self, messages: list[dict], limit: int=30) -> dict:
        return {'messages':messages[-limit:]}
