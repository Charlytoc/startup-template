import re
import uuid

from core.models import Organization


def _label_from_email_local_part(email: str) -> str:
    """Human-readable label from the part before @ (first segment before a dot)."""
    local, _, _ = email.partition("@")
    local = local.strip()
    if not local:
        return ""
    handle = local.split(".", 1)[0].strip()
    ascii_handle = re.sub(r"[^a-zA-Z0-9]", "", handle)
    if not ascii_handle:
        return ""
    if len(ascii_handle) == 1:
        return ascii_handle.upper()
    return ascii_handle[0].upper() + ascii_handle[1:].lower()


def personal_organization_name(email: str) -> str:
    """e.g. charly@makedarwin.com -> Charly's Organization"""
    label = _label_from_email_local_part(email)
    if not label:
        return "My Organization"
    name = f"{label}'s Organization"
    return name[: Organization._meta.get_field("name").max_length]


def personal_organization_domain(email: str) -> str:
    """
    Stable, unique internal domain derived from the full email (not shown as a website URL).
    """
    suffix = ".users.local"
    max_total = Organization._meta.get_field("domain").max_length
    reserved = len(suffix) + 10  # room for uniqueness suffix like -a1b2c3d4
    raw = email.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", raw.replace("@", "-at-")).strip("-") or "org"
    base = slug[: max(1, max_total - reserved)]
    candidate = f"{base}{suffix}"
    while Organization.objects.filter(domain=candidate).exists():
        fragment = uuid.uuid4().hex[:8]
        stem = f"{base}-{fragment}"[: max_total - len(suffix)]
        candidate = f"{stem}{suffix}"
    return candidate[:max_total]


def create_personal_organization_for_signup(email: str) -> Organization:
    return Organization.objects.create(
        name=personal_organization_name(email),
        domain=personal_organization_domain(email),
        status=Organization.Status.ACTIVE,
    )
