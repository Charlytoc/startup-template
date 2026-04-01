import time
from datetime import datetime, timezone

from celery import shared_task
from celery.utils.log import get_task_logger

from core.agent.base import Agent, AgentConfig
from core.agent.tools.get_user_info import make_get_user_info_tool
from core.models import User
from core.models.agent_session_log import AgentSessionLog
from core.schemas.agentic_chat import ExchangeMessage
from core.services.redis_publisher import publish_to_bridge

logger = get_task_logger(__name__)

DEFAULT_SYSTEM_PROMPT = """
You are a helpful AI assistant for a reusable mobile app template.
Be concise, practical, and friendly. Prefer short paragraphs and bullet points.
If information is uncertain, say so clearly.
"""

MODEL = "gpt-5.4-mini"
PROVIDER = "openai"


@shared_task(bind=True)
def run_agentic_chat(self, user_id: int, user_message: str):
    user = User.objects.select_related("organization").get(id=user_id)
    tools = [make_get_user_info_tool(user=user)]
    log = AgentSessionLog.objects.create(
        user_id=user_id,
        celery_task_id=self.request.id,
        model=MODEL,
        provider=PROVIDER,
        instructions=DEFAULT_SYSTEM_PROMPT.strip(),
        tools=[t.tool.model_dump() for t in tools],
        inputs=[{"role": "user", "content": user_message}],
        status=AgentSessionLog.Status.PENDING,
    )

    started = time.monotonic()

    try:
        agent = Agent(
            config=AgentConfig(
                name="Template Assistant",
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                model=MODEL,
            )
        )
        summary = agent.start_agent_loop(
            messages=[ExchangeMessage(role="user", content=user_message)],
            tools=tools,
        )

        assistant_message = summary.final_response or "I could not generate a response."
        duration = time.monotonic() - started

        log.status = AgentSessionLog.Status.ERROR if summary.error else AgentSessionLog.Status.COMPLETED
        log.iterations = summary.iterations
        log.tool_calls_count = summary.tool_calls_count
        log.total_duration = round(duration, 3)
        log.ended_at = datetime.now(timezone.utc)
        log.outputs = {
            "final_response": assistant_message,
            "messages": [m.model_dump() for m in summary.messages],
        }
        if summary.error:
            log.error_message = summary.error
        log.save()

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
        duration = time.monotonic() - started
        log.status = AgentSessionLog.Status.ERROR
        log.error_message = str(exc)
        log.total_duration = round(duration, 3)
        log.ended_at = datetime.now(timezone.utc)
        log.save()
        logger.error(f"run_agentic_chat failed for user {user_id}: {exc}")
        return {"status": "error", "user_id": user_id, "error": str(exc)}
