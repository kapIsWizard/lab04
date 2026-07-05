"""Schema loading and validation for the protocol generator.

The generator is intentionally small, but the validation step is separated from
template rendering so new field types or message-level options can be added in a
single place without touching the CLI.
"""

from __future__ import annotations

import json
import keyword
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class TypeSpec:
    """Metadata needed by both validation and generated type hints."""

    name: str
    python_type: str


# Add new field types here first. The generated runtime also needs a codec with
# the same name in templates/protocol.py.j2. Dynamic JSON-backed types are useful
# for nested data that should not require a dedicated message definition.
TYPE_REGISTRY: dict[str, TypeSpec] = {
    "int8": TypeSpec("int8", "int"),
    "int16": TypeSpec("int16", "int"),
    "uint8": TypeSpec("uint8", "int"),
    "uint16": TypeSpec("uint16", "int"),
    "uint32": TypeSpec("uint32", "int"),
    "int32": TypeSpec("int32", "int"),
    "uint64": TypeSpec("uint64", "int"),
    "int64": TypeSpec("int64", "int"),
    "float32": TypeSpec("float32", "float"),
    "float64": TypeSpec("float64", "float"),
    "bool": TypeSpec("bool", "bool"),
    "string": TypeSpec("string", "str"),
    "bytes": TypeSpec("bytes", "bytes"),
    "dictionary": TypeSpec("dictionary", "dict[str, Any]"),
    "dict": TypeSpec("dict", "dict[str, Any]"),
    "list": TypeSpec("list", "list[Any]"),
    "array": TypeSpec("array", "list[Any]"),
    "any": TypeSpec("any", "Any"),
}


def load_schema(path: Path) -> dict[str, Any]:
    """Load, validate, and enrich an interface definition."""

    with path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    _validate_schema(schema)
    return _enrich_schema(schema)


def _validate_schema(schema: dict[str, Any]) -> None:
    if not isinstance(schema, dict):
        raise ValueError("Schema root must be a JSON object.")

    protocol = schema.get("protocol")
    if not isinstance(protocol, str) or not protocol:
        raise ValueError("'protocol' must be a non-empty string.")

    messages = schema.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("'messages' must be a non-empty list.")

    seen_names: set[str] = set()
    seen_ids: set[int] = set()

    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("Every message must be an object.")

        name = message.get("name")
        if not _is_identifier(name) or not str(name)[0].isupper():
            raise ValueError(f"Message name must be a PascalCase identifier: {name!r}")
        if name in seen_names:
            raise ValueError(f"Duplicate message name: {name}")
        seen_names.add(name)

        message_id = message.get("id")
        if not isinstance(message_id, int) or not 0 <= message_id <= 65535:
            raise ValueError(f"Message id for {name} must be between 0 and 65535.")
        if message_id in seen_ids:
            raise ValueError(f"Duplicate message id: {message_id}")
        seen_ids.add(message_id)

        fields = message.get("fields")
        if not isinstance(fields, list):
            raise ValueError(f"'fields' for {name} must be a list.")

        seen_fields: set[str] = set()
        for field in fields:
            if not isinstance(field, dict):
                raise ValueError(f"Every field in {name} must be an object.")

            field_name = field.get("name")
            if not _is_identifier(field_name):
                raise ValueError(f"Invalid field name in {name}: {field_name!r}")
            if field_name in seen_fields:
                raise ValueError(f"Duplicate field name in {name}: {field_name}")
            seen_fields.add(field_name)

            field_type = field.get("type")
            if field_type not in TYPE_REGISTRY:
                supported = ", ".join(sorted(TYPE_REGISTRY))
                raise ValueError(
                    f"Unsupported type {field_type!r} in {name}.{field_name}. "
                    f"Supported types: {supported}"
                )


def _enrich_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Attach derived names used by the Jinja template."""

    enriched = dict(schema)
    enriched["messages"] = []
    enriched["byte_order"] = schema.get("byte_order", "big")

    for message in schema["messages"]:
        item = dict(message)
        item["serializer_name"] = f"serialize_{_to_snake_case(message['name'])}"
        item["deserializer_name"] = f"deserialize_{_to_snake_case(message['name'])}"
        item["fields"] = []

        for field in message["fields"]:
            field_item = dict(field)
            field_item["python_type"] = TYPE_REGISTRY[field["type"]].python_type
            item["fields"].append(field_item)

        enriched["messages"].append(item)

    return enriched


def _is_identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(_IDENTIFIER_RE.match(value)) and not keyword.iskeyword(value)


def _to_snake_case(name: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)
