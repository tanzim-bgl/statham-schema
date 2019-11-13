from argparse import ArgumentParser, Namespace
from contextlib import contextmanager
from io import TextIOWrapper
from logging import getLogger, INFO
from os import path
from typing import Any, ContextManager, Dict, Tuple
from sys import stdout

import yaml

from jsonschema_objects.dependency_resolver import ClassDependencyResolver
from jsonschema_objects.models import parse_schema
from jsonschema_objects.parser import dereference_schema
from jsonschema_objects.serializer import serialize_object_schemas


LOGGER = getLogger(__name__)
LOGGER.setLevel(INFO)


@contextmanager
def parse_args() -> ContextManager[Tuple[Namespace, TextIOWrapper]]:
    parser = ArgumentParser(description="Generate python attrs models from JSONSchema files.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Specify path to top-level schema document.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Output directory or file to write the output to. If this "
            "is a directory, the command will derive the name from the "
            "input file. If not passed, the command will write to "
            "stdout."
        )
    )
    parsed = parser.parse_args()
    if parsed.output:
        if path.isdir(parsed.output):
            filename = ".".join(path.basename(parsed.input).split(".")[:-1])
            output_path = path.join(parsed.output, ".".join([filename, "py"]))
        else:
            output_path = parsed.output
        with open(output_path, "w", encoding="utf8") as file:
            yield parsed, file
        return
    yield parsed, stdout
    return


def _load_schema(filepath: str) -> Dict[str, Any]:
    if not filepath.endswith((".json", ".yaml", ".yml")):
        raise TypeError(f"File {filepath} has unsupported extension.")
    with open(filepath, "r", encoding="utf8") as file:
        content = file.read()
    return yaml.safe_load(content)


def main(input_file: str) -> str:
    schema = _load_schema(input_file)
    schema: Dict[str, Any] = parse_schema(
        dereference_schema(schema, f"file://{input_file}", schema)
    )
    class_schemas = ClassDependencyResolver(schema)
    return serialize_object_schemas(class_schemas)


if __name__ == "__main__":
    with parse_args() as (args, output):
        output.write(main(args.input))
