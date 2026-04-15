"""
Example tool: get_user_info

Returns basic profile information about the authenticated user.

Pattern for adding new tools:
    1. Define TOOL_SCHEMA (the JSON schema OpenAI sees).
    2. Write an `execute(**args)` function that does the actual work.
    3. Expose a `make_<tool_name>(user, ...)` factory that binds context
       (user, org, request, etc.) and returns an AgentToolConfig.

Usage in a task:
    from core.agent.tools.get_user_info import make_get_user_info_tool

    user = User.objects.get(id=user_id)
    tools = [make_get_user_info_tool(user=user)]
    summary = agent.start_agent_loop(messages=[...], tools=tools)
"""

from core.agent.base import AgentTool, AgentToolConfig

TOOL_SCHEMA = AgentTool(
    type="function",
    name="get_user_info",
    description=(
        "Returns the authenticated user's profile information: "
        "their email, first name, last name, and organization name. "
        "Use this when the user asks about their account or profile details."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
)


def make_get_user_info_tool(user, *, organization_name: str | None = None) -> AgentToolConfig:
    """
    Factory that binds `user` into the tool callable.
    The returned AgentToolConfig is ready to pass to agent.start_agent_loop().
    If ``organization_name`` is set (e.g. active org from ``X-Org-Id``), it overrides the user's FK org name.
    """

    def execute() -> dict:
        org_display = organization_name
        if org_display is None and user.organization_id:
            org_display = user.organization.name
        return {
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "organization": org_display,
        }

    return AgentToolConfig(tool=TOOL_SCHEMA, function=execute)
