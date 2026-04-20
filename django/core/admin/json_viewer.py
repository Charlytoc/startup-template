"""Collapsible JSON viewer for the Django admin.

Use this to turn giant ``JSONField`` blobs (tool call dumps, agent session logs, job configs)
into a readable, collapsible HTML tree. Works both as a form widget (editable) and as a
read-only helper via :class:`PrettyJSONAdminMixin`.
"""

from __future__ import annotations

import json
from typing import Any

from django import forms
from django.contrib.admin.widgets import AdminTextareaWidget
from django.db import models
from django.utils.html import escape, format_html
from django.utils.safestring import SafeString, mark_safe

_CSS = """
.cursor-json-viewer, .cursor-json-widget { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; line-height: 1.5; }
.cursor-json-viewer details { margin: 0; }
.cursor-json-viewer summary { cursor: pointer; list-style: none; padding: 2px 4px; border-radius: 4px; }
.cursor-json-viewer summary::-webkit-details-marker { display: none; }
.cursor-json-viewer summary::before { content: "▸"; display: inline-block; width: 1em; color: #888; transition: transform 120ms ease; }
.cursor-json-viewer details[open] > summary::before { content: "▾"; }
.cursor-json-viewer summary:hover { background: rgba(128,128,128,0.08); }
.cursor-json-viewer .json-nested { border-left: 1px solid rgba(128,128,128,0.25); margin-left: 0.5em; padding-left: 0.75em; }
.cursor-json-viewer .json-key { color: #9cdcfe; font-weight: 600; }
.cursor-json-viewer .json-index { color: #888; }
.cursor-json-viewer .json-preview { color: #888; margin-left: 0.5em; font-style: italic; }
.cursor-json-viewer .json-leaf-string { color: #ce9178; }
.cursor-json-viewer .json-leaf-number { color: #b5cea8; }
.cursor-json-viewer .json-leaf-bool { color: #569cd6; }
.cursor-json-viewer .json-leaf-null { color: #808080; font-style: italic; }
.cursor-json-viewer .json-leaf-inline { margin-left: 0.25em; }
.cursor-json-viewer .json-empty { color: #888; font-style: italic; }
.cursor-json-widget .cursor-json-raw { margin-top: 0.5em; }
.cursor-json-widget .cursor-json-raw textarea { width: 100%; min-height: 160px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
"""


_LEAF_PREVIEW_MAX = 60


def _coerce_to_python(value: Any) -> Any:
    """Accept dict/list as-is; try to JSON-parse strings; otherwise return as-is."""
    if value is None or isinstance(value, (dict, list, int, float, bool)):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return ""
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return value
    return value


def _render_leaf(value: Any) -> SafeString:
    if value is None:
        return mark_safe('<span class="json-leaf-null">null</span>')
    if isinstance(value, bool):
        return format_html('<span class="json-leaf-bool">{}</span>', "true" if value else "false")
    if isinstance(value, (int, float)):
        return format_html('<span class="json-leaf-number">{}</span>', value)
    return format_html('<span class="json-leaf-string">"{}"</span>', str(value))


def _inline_preview(value: Any) -> SafeString:
    """Short hint shown in the summary line when the node is a container or long string."""
    if isinstance(value, dict):
        keys = list(value.keys())
        sample = ", ".join(str(k) for k in keys[:4])
        if len(keys) > 4:
            sample += ", ..."
        return format_html(
            '<span class="json-preview">{{{} keys: {}}}</span>', len(keys), sample
        )
    if isinstance(value, list):
        return format_html('<span class="json-preview">[{} items]</span>', len(value))
    if isinstance(value, str) and len(value) > _LEAF_PREVIEW_MAX:
        return format_html(
            '<span class="json-preview">"{}…" ({} chars)</span>',
            value[:_LEAF_PREVIEW_MAX],
            len(value),
        )
    return mark_safe("")


def _render_node(node: Any, depth: int = 0) -> SafeString:
    # Leaves render inline (no <details>).
    if not isinstance(node, (dict, list)):
        return format_html('<span class="json-leaf-inline">{}</span>', _render_leaf(node))

    if isinstance(node, dict):
        if not node:
            return mark_safe('<span class="json-empty">{}</span>')
        parts: list[str] = ['<div class="json-dict">']
        for k, v in node.items():
            is_container = isinstance(v, (dict, list))
            if is_container:
                parts.append(
                    format_html(
                        '<details><summary><span class="json-key">{key}</span>'
                        '<span>: </span>{preview}</summary>'
                        '<div class="json-nested">{inner}</div></details>',
                        key=escape(str(k)),
                        preview=_inline_preview(v),
                        inner=_render_node(v, depth + 1),
                    )
                )
            else:
                parts.append(
                    format_html(
                        '<div class="json-entry"><span class="json-key">{key}</span>'
                        '<span>: </span>{leaf}</div>',
                        key=escape(str(k)),
                        leaf=_render_leaf(v),
                    )
                )
        parts.append("</div>")
        return mark_safe("".join(parts))

    # list
    if not node:
        return mark_safe('<span class="json-empty">[]</span>')
    parts = ['<div class="json-list">']
    for i, v in enumerate(node):
        is_container = isinstance(v, (dict, list))
        if is_container:
            parts.append(
                format_html(
                    '<details><summary><span class="json-index">[{idx}]</span>'
                    '{preview}</summary>'
                    '<div class="json-nested">{inner}</div></details>',
                    idx=i,
                    preview=_inline_preview(v),
                    inner=_render_node(v, depth + 1),
                )
            )
        else:
            parts.append(
                format_html(
                    '<div class="json-entry"><span class="json-index">[{idx}]</span>'
                    '<span>: </span>{leaf}</div>',
                    idx=i,
                    leaf=_render_leaf(v),
                )
            )
    parts.append("</div>")
    return mark_safe("".join(parts))


def render_json_html(value: Any) -> SafeString:
    """Return a ``SafeString`` with a collapsible HTML tree for ``value``.

    Accepts ``dict``, ``list``, ``str`` (will attempt JSON parse), primitives, or ``None``.
    Always returns HTML safe for admin rendering.
    """
    coerced = _coerce_to_python(value)
    style = format_html("<style>{}</style>", mark_safe(_CSS))
    body = format_html('<div class="cursor-json-viewer">{}</div>', _render_node(coerced))
    return mark_safe(str(style) + str(body))


class JSONViewerWidget(AdminTextareaWidget):
    """Editable JSON widget: shows a collapsible preview above the raw textarea."""

    class Media:
        pass

    def render(self, name, value, attrs=None, renderer=None):
        raw = super().render(name, value, attrs=attrs, renderer=renderer)
        try:
            parsed = json.loads(value) if isinstance(value, str) and value.strip() else value
        except json.JSONDecodeError:
            parsed = value
        pretty = render_json_html(parsed if parsed is not None else {})
        return format_html(
            '<div class="cursor-json-widget">{pretty}'
            '<details class="cursor-json-raw"><summary>Edit raw JSON</summary>{raw}</details>'
            "</div>",
            pretty=pretty,
            raw=raw,
        )


class PrettyJSONAdminMixin:
    """Mixin that auto-renders ``JSONField``s with :class:`JSONViewerWidget`.

    Also provides :pymeth:`pretty_json_readonly` to declare nicer read-only displays for
    JSON fields that live in ``readonly_fields`` (where widgets do not apply).

    Usage::

        class MyAdmin(PrettyJSONAdminMixin, admin.ModelAdmin):
            pretty_json_fields = ("config", "inputs", "outputs", "tools")
    """

    formfield_overrides = {
        models.JSONField: {"widget": JSONViewerWidget},
    }

    pretty_json_fields: tuple[str, ...] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for field_name in getattr(cls, "pretty_json_fields", ()):  # declared on subclass
            method_name = f"{field_name}_pretty"
            if hasattr(cls, method_name):
                continue

            def _make(fn):
                def _display(self, obj, _fn=fn):
                    return render_json_html(getattr(obj, _fn, None))
                _display.short_description = fn.replace("_", " ").title()
                return _display

            setattr(cls, method_name, _make(field_name))
