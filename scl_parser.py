"""Recursive-descent parser for the SCL subset."""

import json
import sys
from pathlib import Path

COMPARISON_TYPES = {
    "EQUAL", "NOT_EQUAL", "LESS_THAN", "GREATER_THAN",
    "LESS_EQUAL", "GREATER_EQUAL",
}
IGNORED_TYPES = {"COMMENT", "LINE_COMMENT", "BLOCK_COMMENT"}


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.declared_identifiers = set()

    def _peek(self):
        index = self.position
        while index < len(self.tokens) and self.tokens[index].get("type") in IGNORED_TYPES:
            index += 1
        return self.tokens[index] if index < len(self.tokens) else None

    def _advance(self):
        while self.position < len(self.tokens) and self.tokens[self.position].get("type") in IGNORED_TYPES:
            self.position += 1
        if self.position >= len(self.tokens):
            return None
        token = self.tokens[self.position]
        self.position += 1
        return token

    def _error(self, message):
        token = self._peek()
        if token is None:
            where = "at end of input"
        else:
            where = "at token {!r} ({})".format(token.get("value"), token.get("type"))
        raise ParseError("{} {}".format(message, where))

    def _expect(self, token_type, value=None):
        token = self._peek()
        if token is None or token.get("type") != token_type or (
            value is not None and token.get("value") != value
        ):
            self._error("Expected {}".format(value or token_type))
        return self._advance()

    def _is_keyword(self, value):
        token = self._peek()
        return token is not None and token.get("type") == "KEYWORD" and token.get("value") == value

    def _is_type(self, token_type):
        token = self._peek()
        return token is not None and token.get("type") == token_type

    def begin(self):
        return self.start()

    # program = { declaration | statement }
    def start(self):
        children = []
        while self._peek() is not None:
            if self._is_keyword("int"):
                children.append(self.declaration())
            else:
                children.append(self.statement())
        return {"type": "Program", "children": children}

    # int declaration = "int" identifier "=" expression ";"
    def declaration(self):
        self._expect("KEYWORD", "int")
        name = self._expect("IDENTIFIER")["value"]
        if name in self.declared_identifiers:
            self._error("Variable {!r} has already been declared".format(name))
        self._expect("ASSIGN", "=")
        value = self.expression()
        self._expect("SEMICOLON", ";")
        self.declared_identifiers.add(name)
        return {"type": "Declaration", "name": name, "value": value}

    def statement(self):
        if self._is_keyword("print"):
            return self.print_statement()
        if self._is_keyword("if"):
            return self.if_statement()
        if self._is_keyword("while"):
            return self.while_statement()
        if self._is_type("IDENTIFIER"):
            return self.assignment()
        self._error("Expected a declaration or statement")

    def assignment(self):
        name = self._expect("IDENTIFIER")["value"]
        if name not in self.declared_identifiers:
            self._error("Variable {!r} has not been declared".format(name))
        self._expect("ASSIGN", "=")
        value = self.expression()
        self._expect("SEMICOLON", ";")
        return {"type": "Assignment", "name": name, "value": value}

    def print_statement(self):
        self._expect("KEYWORD", "print")
        self._expect("LEFT_PAREN", "(")
        value = self.expression()
        self._expect("RIGHT_PAREN", ")")
        self._expect("SEMICOLON", ";")
        return {"type": "Print", "value": value}

    def if_statement(self):
        self._expect("KEYWORD", "if")
        self._expect("LEFT_PAREN", "(")
        condition = self.condition()
        self._expect("RIGHT_PAREN", ")")
        then_body = self.block()
        else_body = []
        if self._is_keyword("else"):
            self._advance()
            else_body = self.block()
        return {
            "type": "If", "condition": condition,
            "then": then_body, "else": else_body,
        }

    def while_statement(self):
        self._expect("KEYWORD", "while")
        self._expect("LEFT_PAREN", "(")
        condition = self.condition()
        self._expect("RIGHT_PAREN", ")")
        return {
            "type": "While",
            "condition": condition,
            "body": self.block(),
        }

    def block(self):
        self._expect("LEFT_BRACE", "{")
        statements = []
        while not self._is_type("RIGHT_BRACE"):
            if self._peek() is None:
                self._error("Expected '}' to close block")
            if self._is_keyword("int"):
                statements.append(self.declaration())
            else:
                statements.append(self.statement())
        self._expect("RIGHT_BRACE", "}")
        return statements

    def condition(self):
        left = self.expression()
        token = self._peek()
        if token is None or token.get("type") not in COMPARISON_TYPES:
            self._error("Expected a comparison operator")
        operator = self._advance()["value"]
        right = self.expression()
        return {
            "type": "Condition",
            "operator": operator,
            "left": left,
            "right": right,
        }

    # expression = term { ("+" | "-") term }
    def expression(self):
        node = self.term()
        while self._is_type("PLUS") or self._is_type("MINUS"):
            operator = self._advance()["value"]
            node = {
                "type": "BinaryExpression", "operator": operator,
                "left": node, "right": self.term(),
            }
        return node

    # term = unary { ("*" | "/") unary }
    def term(self):
        node = self.unary()
        while self._is_type("MULTIPLY") or self._is_type("DIVIDE"):
            operator = self._advance()["value"]
            node = {
                "type": "BinaryExpression", "operator": operator,
                "left": node, "right": self.unary(),
            }
        return node

    def unary(self):
        if self._is_type("MINUS"):
            self._advance()
            return {"type": "UnaryExpression", "operator": "-", "operand": self.unary()}
        return self.factor()

    # factor = identifier | integer | real | string | "(" expression ")"
    def factor(self):
        token = self._peek()
        if token is None:
            self._error("Expected an expression factor")

        if token.get("type") == "IDENTIFIER":
            name = self._advance()["value"]
            if name not in self.declared_identifiers:
                self._error("Variable {!r} has not been declared".format(name))
            return {"type": "Identifier", "name": name}

        if token.get("type") == "INTEGER":
            return {"type": "Integer", "value": int(self._advance()["value"])}

        if token.get("type") == "REAL":
            return {"type": "Real", "value": float(self._advance()["value"])}

        if token.get("type") == "STRING":
            return {"type": "String", "value": self._advance()["value"]}

        if token.get("type") == "LEFT_PAREN":
            self._advance()
            node = self.expression()
            self._expect("RIGHT_PAREN", ")")
            return node

        self._error("Expected an identifier, number, string, or parenthesized expression")


def main():
    if len(sys.argv) != 2:
        print("Usage: python parser.py <tokens.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    try:
        tokens = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(tokens, list):
            raise ValueError("Token JSON root must be a list.")
        parser = Parser(tokens)
        tree = parser.begin()
    except (OSError, json.JSONDecodeError, ValueError, ParseError) as error:
        print("Parser error: {}".format(error))
        sys.exit(1)

    output_path = input_path.with_name(input_path.stem + "_parse_tree.json")
    output_path.write_text(json.dumps(tree, indent=4) + "\n", encoding="utf-8")
    print("Parsing successful.")
    print("Parse tree written to: {}".format(output_path))


if __name__ == "__main__":
    main()
