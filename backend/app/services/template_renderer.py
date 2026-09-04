"""Safe rendering for built-in and user-provided post templates."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from ..category_settings import (
    ALLOWED_TEMPLATE_VARIABLES,
    Category,
    BUILTIN_TEMPLATES,
    default_template_for,
)
from .template_store import persistent_template_store
from .ai.utils import parse_hashtags

_VARIABLE_RE = re.compile(r"\{([a-zA-Z][a-zA-Z0-9_]*)\}")
_HASHTAG_RE = re.compile(r"(?<![\w#])#[^\s#{}]+", re.UNICODE)


class TemplateValidationError(ValueError):
    """Raised when a template is unsafe or mismatched with its category."""


def template_variables(template_body: str) -> set[str]:
    return set(_VARIABLE_RE.findall(template_body))


def extract_template_hashtags(template_body: str) -> list[str]:
    """Return literal hashtags written in a template, preserving their order."""
    return parse_hashtags(_HASHTAG_RE.findall(template_body))


def validate_template_body(template_body: str) -> None:
    variables = template_variables(template_body)
    invalid = sorted(variables - ALLOWED_TEMPLATE_VARIABLES)
    if invalid:
        formatted = ", ".join(f"{{{value}}}" for value in invalid)
        raise TemplateValidationError(f"使用できないテンプレート変数があります: {formatted}")


def render_template(
    template_body: str,
    values: Mapping[str, object],
    *,
    fixed_hashtags: Sequence[str] | None = None,
    ai_hashtags: Sequence[str] | None = None,
) -> str:
    validate_template_body(template_body)

    template_fixed_hashtags = parse_hashtags(
        fixed_hashtags if fixed_hashtags is not None else extract_template_hashtags(template_body)
    )
    provided_hashtags = parse_hashtags(str(values.get("hashtags", "") or ""))
    dynamic_hashtags = (
        parse_hashtags(ai_hashtags)
        if ai_hashtags is not None
        else [
            tag
            for tag in provided_hashtags
            if tag.casefold() not in {fixed.casefold() for fixed in template_fixed_hashtags}
        ]
    )
    render_values = dict(values)
    if template_fixed_hashtags:
        render_values["hashtags"] = " ".join(dynamic_hashtags)

    def replace(match: re.Match[str]) -> str:
        return str(render_values.get(match.group(1), "") or "")

    rendered_lines: list[str] = []
    for line in template_body.splitlines():
        line_variables = _VARIABLE_RE.findall(line)
        if line_variables and all(
            not str(render_values.get(variable, "") or "").strip()
            for variable in line_variables
        ):
            continue
        rendered = _VARIABLE_RE.sub(replace, line).rstrip()
        if rendered.strip() == "────────────":
            continue
        if rendered.strip() == "":
            rendered_lines.append(rendered)
            continue
        rendered_lines.append(rendered)

    output_lines: list[str] = []
    for line in rendered_lines:
        if line.strip() == "" and (not output_lines or output_lines[-1].strip() == ""):
            continue
        output_lines.append(line)
    while output_lines and not output_lines[-1].strip():
        output_lines.pop()

    if template_fixed_hashtags and dynamic_hashtags and "{hashtags}" not in template_body:
        fixed_keys = {tag.casefold() for tag in template_fixed_hashtags}
        target_index = -1
        for index, line in enumerate(output_lines):
            line_tags = parse_hashtags(line)
            if any(tag.casefold() in fixed_keys for tag in line_tags):
                target_index = index
        dynamic_text = " ".join(dynamic_hashtags)
        if target_index >= 0:
            output_lines[target_index] = f"{output_lines[target_index].rstrip()} {dynamic_text}"
        else:
            if output_lines and output_lines[-1].strip():
                output_lines.append("")
            output_lines.append(dynamic_text)
    return "\n".join(output_lines)


def resolve_template(
    category: Category,
    template_id: str,
    *,
    custom_template: str = "",
    custom_template_name: str = "",
) -> tuple[str, str]:
    if template_id == "custom":
        body = custom_template.strip()
        if not body:
            raise TemplateValidationError("カスタムテンプレート本文を入力してください。")
        validate_template_body(body)
        return "custom", body
    if template_id in {"", "auto"}:
        template = default_template_for(category)
        return str(template["template_id"]), str(template["template_body"])
    for template in BUILTIN_TEMPLATES:
        if template["template_id"] == template_id:
            if template["category"] != category:
                raise TemplateValidationError("選択したテンプレートがカテゴリと一致しません。")
            return str(template["template_id"]), str(template["template_body"])
    saved = persistent_template_store.get(template_id)
    if saved:
        if saved.category != category:
            raise TemplateValidationError("選択したテンプレートがカテゴリと一致しません。")
        validate_template_body(saved.template_body)
        return saved.template_id, saved.template_body
    raise TemplateValidationError("選択した投稿フォーマットが見つかりません。")
