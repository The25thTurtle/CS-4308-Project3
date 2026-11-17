"""Lexical scanner for the SCL subset."""

import sys
import json
from pathlib import Path

KEYWORDS = ["int", "print", "if", "else", "while"]

OPERATORS = {
    "=": "ASSIGN",
    "+": "PLUS",
    "-": "MINUS",
    "*": "MULTIPLY",
    "/": "DIVIDE",
    "<": "LESS_THAN",
    ">": "GREATER_THAN",
    "==": "EQUAL",
    "!=": "NOT_EQUAL",
    "<=": "LESS_EQUAL",
    ">=": "GREATER_EQUAL",
}

SPECIAL_CHARACTERS = {
    "(": "LEFT_PAREN",
    ")": "RIGHT_PAREN",
    "{": "LEFT_BRACE",
    "}": "RIGHT_BRACE",
    ";": "SEMICOLON",
    ",": "COMMA",
}


def scan(source_code):
    """Convert SCL source text into a list of token dictionaries."""
    tokens = []
    identifiers = []
    i = 0

    while i < len(source_code):
        current = source_code[i]

        if current.isspace():
            i += 1
            continue

        # Single-line comments: // comment
        if source_code.startswith("//", i):
            newline = source_code.find("\n", i)
            i = len(source_code) if newline == -1 else newline + 1
            continue

        # Identifiers and keywords
        if current.isalpha() or current == "_":
            start = i
            i += 1
            while i < len(source_code) and (
                source_code[i].isalnum() or source_code[i] == "_"
            ):
                i += 1

            value = source_code[start:i]
            if value in KEYWORDS:
                tokens.append({"type": "KEYWORD", "value": value})
            else:
                tokens.append({"type": "IDENTIFIER", "value": value})
                if value not in identifiers:
                    identifiers.append(value)
            continue

        # Integer and real constants (including forms such as 12. and .5)
        if current.isdigit() or (
            current == "." and i + 1 < len(source_code)
            and source_code[i + 1].isdigit()
        ):
            start = i
            has_dot = False

            if current == ".":
                has_dot = True
                i += 1

            while i < len(source_code) and source_code[i].isdigit():
                i += 1

            if i < len(source_code) and source_code[i] == "." and not has_dot:
                has_dot = True
                i += 1
                while i < len(source_code) and source_code[i].isdigit():
                    i += 1

            value = source_code[start:i]
            tokens.append({
                "type": "REAL" if has_dot else "INTEGER",
                "value": value,
            })
            continue

        # String literals with basic escape support
        if current == '"':
            start = i
            i += 1
            chars = []
            while i < len(source_code) and source_code[i] != '"':
                if source_code[i] == "\\":
                    i += 1
                    if i >= len(source_code):
                        raise ValueError("Unterminated escape sequence in string literal.")
                    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                    chars.append(escapes.get(source_code[i], source_code[i]))
                    i += 1
                else:
                    if source_code[i] == "\n":
                        raise ValueError("String literals cannot contain an unescaped newline.")
                    chars.append(source_code[i])
                    i += 1

            if i >= len(source_code):
                raise ValueError("Unterminated string literal beginning at character {}.".format(start))

            i += 1  # closing quote
            tokens.append({"type": "STRING", "value": "".join(chars)})
            continue

        # Two-character operators must be checked before one-character ones.
        two_char = source_code[i:i + 2]
        if two_char in OPERATORS:
            tokens.append({"type": OPERATORS[two_char], "value": two_char})
            i += 2
            continue

        if current in OPERATORS:
            tokens.append({"type": OPERATORS[current], "value": current})
            i += 1
            continue

        if current in SPECIAL_CHARACTERS:
            tokens.append({"type": SPECIAL_CHARACTERS[current], "value": current})
            i += 1
            continue

        tokens.append({"type": "UNKNOWN", "value": current})
        i += 1

    return tokens, identifiers


def main():
    if len(sys.argv) != 2:
        print("Usage: python scanner.py <source_file>")
        sys.exit(1)

    path = Path(sys.argv[1])
    try:
        source = path.read_text(encoding="utf-8")
        tokens, identifiers = scan(source)
    except (OSError, ValueError) as error:
        print("Scanner error: {}".format(error))
        sys.exit(1)

    for token in tokens:
        print("{:<12} {}".format(token["type"], token["value"]))
    print("Identifiers: {}".format(", ".join(identifiers) or "(none)"))

    json_path = path.with_suffix(".json")
    json_path.write_text(json.dumps(tokens, indent=4), encoding="utf-8")
    print("Token JSON written to: {}".format(json_path))


if __name__ == "__main__":
    main()
