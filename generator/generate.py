"""CLI entry point for generating the binary protocol module."""

from __future__ import annotations

import argparse
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from generator.schema import load_schema


def render_protocol(schema_path: Path, output_path: Path) -> None:
    """Render the protocol implementation from interface.json."""

    schema = load_schema(schema_path)
    template_dir = Path(__file__).with_name("templates")

    # StrictUndefined turns misspelled template variables into clear failures.
    env = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("protocol.py.j2")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.render(schema=schema), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate binary protocol serializers.")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("interface.json"),
        help="Path to the JSON interface definition.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("generated/protocol.py"),
        help="Path for the generated Python module.",
    )
    args = parser.parse_args()

    render_protocol(args.schema, args.output)
    print(f"Generated {args.output} from {args.schema}")


if __name__ == "__main__":
    main()
