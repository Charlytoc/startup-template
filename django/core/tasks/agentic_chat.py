from datetime import datetime

from celery import shared_task

from core.agent.base import Agent, AgentConfig
from core.schemas.agentic_chat import ExchangeMessage
from core.services.redis_publisher import publish_to_bridge


DEFAULT_SYSTEM_PROMPT = """
You are a helpful AI assistant for a reusable mobile app template.
Be concise, practical, and friendly. Prefer short paragraphs and bullet points.
If information is uncertain, say so clearly.
"""


@shared_task
def run_agentic_chat(user_id: int, user_message: str):
    try:
        agent = Agent(
            config=AgentConfig(
                name="Template Assistant",
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                model="gpt-4.1-mini",
                temperature=0.4,
            )
        )
        summary = agent.start_agent_loop(
            messages=[ExchangeMessage(role="user", content=user_message)],
            tools=[],
        )
        assistant_message = summary.final_response or "I could not generate a response."
        payload = {
            "message": {
                "role": "assistant",
                "type": "text",
                "content": assistant_message,
                "created": datetime.now().isoformat(),
            },
            "timestamp": datetime.now().isoformat(),
        }
        publish_to_bridge(
            listener=f"user-{user_id}",
            event="agentic-chat-message",
            data=payload,
        )
        return {"status": "completed", "user_id": user_id, "message": assistant_message}
    except Exception as exc:
        return {"status": "error", "user_id": user_id, "error": str(exc)}
