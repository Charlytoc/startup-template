"""Tool: persist a text artifact for the currently-running ``TaskExecution``."""

from __future__ import annotations

import logging

from pydantic import ValidationError

from core.agent.base import AgentTool, AgentToolConfig
from core.models import Artifact, CyberIdentity, IntegrationAccount, TaskExecution
from core.schemas.agent_tools import CreateTextArtifactArgs

logger = logging.getLogger(__name__)


def make_create_text_artifact_tool(*, task_execution: TaskExecution) -> AgentToolConfig:
    """Return a ``create_text_artifact`` tool bound to the current task execution."""

    tool = AgentTool(
        type="function",
        name="create_text_artifact",
        description=(
            "Create a durable text artifact for this run. Use this for captions, notes, drafts, "
            "briefs, summaries, or other text outputs that should be saved beyond the chat turn."
        ),
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "minLength": 1,
                    "description": "The text content to persist.",
                },
                "label": {
                    "type": "string",
                    "maxLength": 200,
                    "default": "",
                    "description": "Optional human-readable label for the artifact.",
                },
                "extension": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 20,
                    "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]*$",
                    "default": "txt",
                    "description": "File-style extension for the text artifact, e.g. txt, md, html, json.",
                },
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    )

    def execute(text: str, label: str = "", extension: str = "txt") -> str:
        try:
            args = CreateTextArtifactArgs(text=text, label=label, extension=extension)
        except ValidationError as exc:
            return f"Error: {exc.errors()[0]['msg']}"

        inputs = task_execution.get_inputs()

        identity = None
        identity_config = inputs.identity_config
        if identity_config is not None:
            identity = CyberIdentity.objects.get(
                id=identity_config.identity,
                workspace=task_execution.workspace,
            )

        integration_account = None
        integration_account_id = (
            getattr(inputs.channel, "integration_account_id", None)
            if inputs.channel is not None
            else None
        )
        if integration_account_id is not None:
            integration_account = IntegrationAccount.objects.get(
                id=integration_account_id,
                workspace=task_execution.workspace,
            )

        artifact = Artifact.objects.create(
            workspace=task_execution.workspace,
            task_execution=task_execution,
            identity=identity,
            integration_account=integration_account,
            kind=Artifact.Kind.TEXT,
            label=args.label,
            metadata={"text": args.text, "extension": args.extension},
        )
        logger.info(
            "create_text_artifact: created artifact=%s task_execution=%s",
            artifact.id,
            task_execution.id,
        )
        return f"Created text artifact {artifact.id}."

    return AgentToolConfig(tool=tool, function=execute)
