# Binary protocol code generator

This project implements a small code generator based on Jinja2 templates. The
schema in `interface.json` describes protocol messages, and the generator emits
Python dataclasses plus binary serialization, deserialization, and TCP framing
helpers.

## Project layout

- `interface.json` - message definitions used as generator input.
- `generator/schema.py` - schema validation and type registry.
- `generator/templates/protocol.py.j2` - Jinja2 template for generated code.
- `generated/protocol.py` - generated implementation used by examples.
- `examples/server.py` - TCP server that receives readings and answers forecast requests.
- `examples/client.py` - TCP client that sends demo messages.
- `tests/test_protocol.py` - serialization and socket helper tests.

## Generate code

```bash
python3 -m generator.generate
```

## Run tests

```bash
python3 -m unittest discover
```

## Run the TCP demo

Start the server:

```bash
python3 examples/server.py --host 127.0.0.1 --port 9009
```

In another terminal, run the client:

```bash
python3 examples/client.py --host 127.0.0.1 --port 9009
```

## Extending the generator

To add a new message, edit `interface.json` and rerun the generator. To add a
new primitive field type, register it in `generator/schema.py` and add a matching
codec in `generator/templates/protocol.py.j2`.

The generator also supports dynamic JSON-compatible fields: `dictionary`/`dict`,
`list`/`array`, and `any`. These are useful for nested values such as histories,
metadata, or settings that should not require a separate message class.
