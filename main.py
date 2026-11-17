"""Run the complete SCL pipeline: scanner -> parser -> interpreter."""

import sys
from pathlib import Path

from scl_scanner import scan
from scl_parser import Parser, ParseError
from interpreter import Interpreter, InterpreterError


def run_file(filename):
    source_path = Path(filename)
    if not source_path.is_file():
        raise FileNotFoundError("Source file {!r} was not found.".format(filename))

    source = source_path.read_text(encoding="utf-8")

    # Stage 1: lexical analysis
    tokens, identifiers = scan(source)

    unknown = [token for token in tokens if token["type"] == "UNKNOWN"]
    if unknown:
        details = ", ".join(repr(token["value"]) for token in unknown)
        raise ValueError("Scanner found unknown character(s): {}".format(details))

    print("=== SCANNER ===")
    for token in tokens:
        print("{:<12} {}".format(token["type"], token["value"]))
    print("Identifiers: {}".format(", ".join(identifiers) or "(none)"))

    # Stage 2: parsing
    print("\n=== PARSER ===")
    parser = Parser(tokens)
    tree = parser.begin()
    print("Parsing successful. {} top-level statement(s) recognized.".format(
        len(tree["children"])
    ))

    # Stage 3: execution
    print("\n=== INTERPRETER OUTPUT ===")
    interpreter = Interpreter()
    interpreter.run(tree)
    print("=== EXECUTION COMPLETED ===")


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <source_file.scl>")
        sys.exit(1)
    try:
        run_file(sys.argv[1])
    except (OSError, ValueError, ParseError, InterpreterError, KeyError) as error:
        print("Error: {}".format(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
