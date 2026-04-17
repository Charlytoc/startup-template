# Coworkers AI — Startup Vision

## The Big Idea

**Agents-as-a-Service for Organizations.**

Virtual workers powered by AI that operate inside your organization's workflows — autonomously, on a schedule, or on-demand. Each agent is hyper-specialized in a role, has its own identity, memory, and tools, and can collaborate with other agents to complete complex tasks.

The platform is not just a chatbot. It is a workforce.

---

## Core Concept: The Virtual Worker

A **CyberIdentity** is the base entity — a virtual worker with:
- A name, personality, and appearance
- An **IdentityType** (what kind of worker it is — e.g. AI Influencer vs AI Community Manager; separate from IAM **Role**)
- Memory (what it has learned and experienced)
- Tools (what it can act on)
- Connected accounts (where it operates)

Workers can be assigned to a **Workspace**, which belongs to an **Organization**. Multiple workers can collaborate on shared accounts or tasks.

At the **product/UI** level, each identity type can surface a **different experience** (e.g. AI Influencer → Instagram-style grid and post pipeline; other types get their own layouts when we build them).

---

## Agent Roles (Examples)

### AI Influencer
- Creates and publishes posts on social media accounts (Instagram, TikTok, X)
- Maintains a consistent visual identity and tone of voice
- Can receive tasks from other agents (e.g., AI Marketer)
- Operates on a schedule (e.g., post every day at 7am and 10pm)

### AI Community Manager
- Monitors comments, DMs, and mentions
- Responds to followers in the brand's tone
- Escalates sensitive issues to human reviewers
- Reports engagement trends to the AI Market Analyst

### AI Marketer
- Creates ad copy and viral content strategies
- Can create and assign tasks to AI Influencers
- Suggests content calendars based on trends
- Coordinates across channels

### AI Market Analyst
- Receives a task: "Analyze tendencies for niche X"
- Browses the web, social media, and data sources
- Produces a structured report with findings, insights, and recommendations
- Can trigger follow-up tasks for other agents

### AI Email Classifier
- Reads incoming emails
- Categorizes, prioritizes, and routes them
- Can draft responses for human approval or send automatically

---

## What Makes This Powerful: Task Orchestration System

Every agent operates through a **task-based orchestration engine**:

- **TaskTemplate** defines **how** work should be done
- **TaskAssignment** defines **who, where, and when** that template runs
- **TaskExecution** is the concrete run / instance of work
- **TaskParticipant** allows multiple identities to collaborate on the same execution
- Executions can be **one-time** (manual or triggered by another agent)
- Executions can be **scheduled** (cron-based, e.g. every Monday at 9am)
- Executions can be **event-driven** (triggered by an incoming message, comment, or metric threshold)
- Agents can **create executions for other agents** — enabling multi-agent workflows

This means the platform can run autonomously, 24/7, like a real team that never sleeps.

---

## Database Architecture (Agreed Decisions)

### IAM: users and roles (organization-scoped)

- **Users** belong to an **Organization** first (invite, SSO, billing context). The catalog of **Roles** is defined at the **organization** level (IAM-style: names + permissions). Roles are **not** tied to a single workspace; they are reusable across the org.
- **What links a human user to a workspace** is **WorkspaceMember**: `user` + `workspace` + **`role` (FK)** plus membership metadata. Unique on `(user, workspace)`.
- This is separate from **agent “roles”** in the product sense (AI Influencer, AI Marketer, etc.) — those describe what a **CyberIdentity** does, not IAM.

### Multi-Tenant Hierarchy
```
Organization
  ├── OrganizationMember (user FK + organization FK)
  ├── Role (IAM catalog: permissions, org-scoped)
  └── Workspace(s)
        ├── WorkspaceMember (user FK + workspace FK + role FK + …)
        ├── CyberIdentity (the virtual worker; has a type + validated config)
        │     ├── Memory
        │     └── IdentityAsset → MediaObject
        ├── ConnectorAccount
        │     └── ConnectorManager
        ├── TaskTemplate
        ├── TaskAssignment
        └── TaskExecution
              ├── TaskParticipant
              └── Artifact → MediaObject
```

### Architecture direction

- The platform is moving from a **social-first schema** to a more **general worker platform**.
- Social posting remains an important vertical, but the core system should support influencers, community managers, analysts, email workers, sales agents, and future worker types without renaming core models later.
- The clean separation is:
  - **TaskTemplate** = how to do the work
  - **TaskAssignment** = who, where, and when it should run
  - **TaskExecution** = the concrete run
  - **TaskParticipant** = which identities collaborated on that run
- Files should have a single source of truth in **MediaObject**.
- Stable identity-owned references belong in **IdentityAsset**.
- Retrievable knowledge / context belongs in **Memory**.

### Per identity type: DB models and UI (direction)

- Prefer **dedicated tables** for type-specific data (**1:1** with `CyberIdentity` where needed), with **real columns and FKs**, instead of relying only on generic JSON and app-layer conventions.
- `CyberIdentity` should have a **type** (e.g. influencer, community_manager, analyst) plus a **config** JSON validated with Pydantic according to that type.
- Use real profile tables when the workflow becomes deep enough to justify them (for example, an `InfluencerProfile` with strongly typed columns).
- **`CyberIdentity.config`** is good for flexible, validated worker setup.
- Stable files like face references, voice samples, and brand guidelines should live in **IdentityAsset**, not in memory.
- Social-specific models can still exist later as first-class domain models, but they should sit **on top of** the generalized worker / execution foundation rather than define it.
- Other identity types get their own profile (and domain) models as we add them.

### Key Models

**OrganizationMember**
- user (FK), organization (FK)
- status (e.g. invited / active / suspended), `joined_at`, optional `invited_by`
- Org-wide concerns (e.g. billing, org settings) are modeled here or via flags — separate from per-workspace **WorkspaceMember**.

**Role** (IAM)
- organization (FK)
- slug / display name
- `role_capabilities` (JSONField): list of capability objects; validated with Pydantic at read/write time. Each item is at least `{ "id": "<string>" }` (e.g. `manage_social_accounts`). The full set of capability IDs is defined in code or docs as the product matures; the JSON shape stays flexible for now.
- Workspace membership references this role when assigning access in a workspace.

**WorkspaceMember**
- user (FK), workspace (FK), role (FK → **Role**)
- status, `invited_at` / `joined_at`, optional `invited_by`
- Unique `(user, workspace)`.

**CyberIdentity**
- workspace (FK)
- type (e.g. influencer, community_manager, analyst)
- name, description, personality, appearance
- `config` (JSONField): validated with Pydantic based on `type`
- Can have many memories, assets, managed connectors, assignments, and participations in task executions

**InfluencerProfile** (example — 1:1 with `CyberIdentity` when `type = influencer`)
- `cyber_identity` (OneToOne → **CyberIdentity**)
- `core_niche`, `base_positive_prompt`, `base_negative_prompt` (image generation), `lora_model_id` (visual consistency), and other influencer-specific fields as **real columns** (many populated from the create flow into this row).
- Other agent kinds: analogous `*Profile` models later (e.g. community manager), each with its own columns — no need for a single “flexible everything” JSON graph.

**Memory**
- identity (FK to CyberIdentity)
- memory_type: core | event | preference | knowledge
- content (TextField)
- optional media_object (FK)
- source, source_ref
- importance_weight (1–10)
- Enables RAG: only inject relevant memories into the agent prompt
- Can be text-only, file-only, or text + file

**IdentityAsset**
- identity (FK)
- media (FK to MediaObject)
- asset_type: reference_face | reference_body | voice_sample | style_reference | brand_guideline
- label
- is_active
- metadata
- Stable identity-owned files and references

**MediaObject** (single source of truth for all files)
- workspace (FK)
- file (FileField)
- original_filename, file_size, content_type
- is_public (bool)
- metadata (JSONField — resolution, duration, etc.)
- Reused by: identity assets, memories, task artifacts, voice samples, uploads

**ConnectorAccount**
- workspace (FK)
- connector_type (Instagram, Gmail, HubSpot, WhatsApp, CMS, ...)
- display_name
- external_account_id
- auth (JSONField)
- settings (JSONField)
- timezone
- status
- Reusable external connection, not limited to social

**ConnectorManager** (through model)
- identity (FK)
- connector_account (FK)
- mode / role (e.g. owner, contributor, publisher)
- Lets multiple identities share the same connector, or one identity manage multiple connectors

**TaskTemplate**
- workspace (FK)
- type
- name
- instructions
- recommended_tools (JSONField)
- default_input (JSONField)
- schema_version
- enabled
- Defines **how** work should be done

**TaskAssignment**
- task_template (FK)
- connector_account (nullable FK)
- schedule_type
- schedule_config (JSONField)
- requires_approval (bool)
- approval_policy (JSONField)
- input_override (JSONField)
- enabled
- Defines **who, where, and when** a template runs
- Can be manual, scheduled, or event-driven

**TaskExecution**
- workspace (FK)
- task_template (FK)
- task_assignment (nullable FK)
- connector_account (nullable FK)
- approved_by_workspace_member (nullable FK)
- type
- status
- requires_approval (bool)
- input (JSONField)
- output (JSONField)
- error_log
- external_delivery_id
- created_at, started_at, completed_at, approved_at, delivered_at
- Snapshot of the actual run / instance of work

**TaskParticipant**
- task_execution (FK)
- cyber_identity (FK)
- participant_role (lead, researcher, reviewer, executor, ...)
- contribution / metadata (JSONField)
- joined_at
- Unique `(task_execution, cyber_identity)`
- Allows multiple identities to collaborate on the same execution

**Artifact**
- task_execution (FK)
- media (FK to MediaObject)
- kind
- metadata
- Output files or deliverables produced by an execution

---

## Automation Pipeline (How it works while you sleep)

1. **TaskAssignment** defines a recurring or event-based job
   - Example: "Influencer team posts to Instagram every day at 7am"
   - Example: "Email classifier processes new inbound messages"

2. The scheduler or trigger creates a **TaskExecution**
   - It copies the resolved template type and input snapshot
   - It links the connector that will be used for delivery if relevant
   - It may come from an assignment or be a one-off manual run (`task_assignment = null`)

3. The orchestrator attaches one or more **TaskParticipants**
   - Example: one identity acts as researcher, another as copywriter, another as reviewer
   - This makes collaboration and handoffs first-class instead of implicit

4. The participants produce outputs and artifacts
   - Text output goes into `TaskExecution.output`
   - Files go into `Artifact -> MediaObject`

5. If approval is required
   - Execution waits for a human reviewer
   - `approved_by_workspace_member` and `approved_at` are recorded

6. If the task targets an external system
   - The connector account is used to publish, send, sync, or deliver
   - `external_delivery_id` and `delivered_at` are recorded

### Example: influencer posting flow

1. `TaskTemplate`: "Create and publish a gym post"
2. `TaskAssignment`: run daily at 7am for Instagr`am account X
3. `TaskExecution`: today’s concrete run
4. `TaskParticipant`: researcher identity + copywriter identity + publisher identity
5. `Artifact`: generated image(s) for the post

---

## Open Questions / To Decide

- [ ] Do we need a platform-managed `IdentityType` catalog later, or is `CyberIdentity.type + config` enough for MVP?
- [ ] `content_focus` on **ConnectorAccount** vs **InfluencerProfile** (or equivalent) niche fields — how they interact per channel
- [ ] Should `TaskParticipantTemplate` exist now, or can participant teams be copied into executions directly from assignment config for MVP?
- [ ] What orchestration rules are needed for multi-identity executions? sequential handoff, parallel work, reviewer gates?
- [ ] Human approval UI — where in the product flow?
- [ ] How should connector auth be protected? encrypted field vs vault service
- [ ] Which social platform API to integrate first? (Instagram Graph API)
- [ ] Image generation provider — Stable Diffusion (self-hosted) vs API (Replicate, fal.ai)?
- [ ] Voice/audio agent support timeline
- [ ] Pricing model — per agent? per workspace? per task execution?

---

## MVP Scope (First Version)

1. Organization + org IAM (**Role** catalog, **OrganizationMember**, **WorkspaceMember** with `user` + `role` FK)
2. Create **CyberIdentity** with `type` + validated `config`, plus **InfluencerProfile** where strongly typed fields matter
3. **Memory**, **IdentityAsset**, and **MediaObject**
4. Connect an Instagram account through **ConnectorAccount**
5. Create **TaskTemplate**, **TaskAssignment**, **TaskExecution**
6. Support at least one **TaskParticipant** per execution, with the architecture ready for multi-identity collaboration
7. Agent auto-generates image + caption using brand guidelines
8. Human review or auto-publish
9. Basic Memory system (manual entries first, then auto-learned)

Everything else is v2.
