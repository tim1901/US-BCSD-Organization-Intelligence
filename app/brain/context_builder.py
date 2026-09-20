from __future__ import annotations


class ContextBuilder:
    def build(
        self,
        *,
        question: str,
        memory_context: dict,
        conversation_context: dict | None = None,
    ) -> dict:
        return {
            "question": question,
            "memory": memory_context,
            "conversation": conversation_context or {},
        }
