"""Recursive-descent parser for the SCL subset used in this deliverable.

Input: JSON token file produced by scl_scanner.py
Output: JSON parse tree
"""
import json
import sys
from pathlib import Path

COMPARISON_TYPES = {
    "EQUAL", "NOT_EQUAL", "LESS_THAN", "GREATER_THAN",
    "LESS_EQUAL", "GREATER_EQUAL"
}
ARITHMETIC_TYPES = {"PLUS", "MINUS", "MULTIPLY", "DIVIDE"}
IGNORED_TYPES = {"COMMENT", "LINE_COMMENT", "BLOCK_COMMENT"}

class ParseError(Exception):
    """Raised when the token stream does not match the SCL grammar."""

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.declared_identifiers = set()

    # Public function 1: return next non-comment token.
    def getNextToken(self):
        while self.position < len(self.tokens):
            token = self.tokens[self.position]
            self.position += 1
            if token.get("type") not in IGNORED_TYPES:
                return token
        return None

    # Public function 2: check whether an identifier has been declared.
    def identifierExists(self, identifier):
        return identifier in self.declared_identifiers

    def _peek(self):
        """Look ahead without consuming a token."""
        index = self.position
        while index < len(self.tokens) and self.tokens[index].get("type") in IGNORED_TYPES:
            index += 1
        return self.tokens[index] if index < len(self.tokens) else None

    def _advance(self):
        return self.getNextToken()

    def _error(self, message):
        token = self._peek()
        if token is None:
            where = "at end of input"
        else:
            where = "at token {!r} ({})".format(
                token.get("value"), token.get("type", "unknown")
            )
        raise ParseError("{} {}".format(message, where))

    def _expect(self, token_type, value=None):
        token = self._peek()
        if token is None:
            self._error("Expected {}".format(value or token_type))
        if token.get("type") != token_type or (
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

    # Public function 3: parse the complete program.
    def begin(self):
        return self.start()

    # Grammar: program = { declaration | statement } ;
    def start(self):
        children = []
        while self._peek() is not None:
            if self._is_keyword("int"):
                children.append(self.declaration())
            else:
                children.append(self.statement())
        return {"type": "Program", "children": children}

    # declaration = "int" identifier "=" expression ";" ;
    def declaration(self):
        self._expect("KEYWORD", "int")
        name_token = self._expect("IDENTIFIER")
        name = name_token["value"]
        if self.identifierExists(name):
            self._error("Variable {!r} has already been declared".format(name))
        self._expect("ASSIGN", "=")
        value = self.expression()
        self._expect("SEMICOLON", ";")
        self.declared_identifiers.add(name)
        return {
            "type": "Declaration",
            "name": name,
            "value": value
        }

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

    # assignment = identifier "=" expression ";" ;
    def assignment(self):
        name = self._expect("IDENTIFIER")["value"]
        if not self.identifierExists(name):
            self._error("Variable {!r} has not been declared".format(name))
        self._expect("ASSIGN", "=")
        value = self.expression()
        self._expect("SEMICOLON", ";")
        return {"type": "Assignment", "name": name, "value": value}

    # print_statement = "print" "(" expression ")" ";" ;
    def print_statement(self):
        self._expect("KEYWORD", "print")
        self._expect("LEFT_PAREN", "(")
        value = self.expression()
        self._expect("RIGHT_PAREN", ")")
        self._expect("SEMICOLON", ";")
        return {"type": "Print", "value": value}

    # if_statement = "if" "(" condition ")" "{" { statement } "}"
    #                [ "else" "{" { statement } "}" ] ;
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
            "type": "If",
            "condition": condition,
            "then": then_body,
            "else": else_body
        }

    # while_statement = "while" "(" condition ")" "{" { statement } "}" ;
    def while_statement(self):
        self._expect("KEYWORD", "while")
        self._expect("LEFT_PAREN", "(")
        condition = self.condition()
        self._expect("RIGHT_PAREN", ")")
        body = self.block()
        return {"type": "While", "condition": condition, "body": body}

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

    # condition = expression comparison_operator expression ;
    def condition(self):
        left = self.expression()
        token = self._peek()
        if token is None or token.get("type") not in COMPARISON_TYPES:
            self._error("Expected a comparison operator")
        operator = self._advance()
        right = self.expression()
        return {
            "type": "Condition",
            "operator": operator["value"],
            "left": left,
            "right": right
        }

    # expression = term { ("+" | "-") term } ;
    def expression(self):
        node = self.term()
        while self._is_type("PLUS") or self._is_type("MINUS"):
            operator = self._advance()["value"]
            right = self.term()
            node = {
                "type": "BinaryExpression",
                "operator": operator,
                "left": node,
                "right": right
            }
        return node

    # term = factor { ("*" | "/") factor } ;
    def term(self):
        node = self.factor()
        while self._is_type("MULTIPLY") or self._is_type("DIVIDE"):
            operator = self._advance()["value"]
            right = self.factor()
            node = {
                "type": "BinaryExpression",
                "operator": operator,
                "left": node,
                "right": right
            }
        return node

    # factor = identifier | integer | "(" expression ")" ;
    def factor(self):
        token = self._peek()
        if token is None:
            self._error("Expected an expression factor")
        if token.get("type") == "IDENTIFIER":
            name = self._advance()["value"]
            if not self.identifierExists(name):
                self._error("Variable {!r} has not been declared".format(name))
            return {"type": "Identifier", "name": name}
        if token.get("type") == "INTEGER":
            return {"type": "Integer", "value": int(self._advance()["value"])}
        if token.get("type") == "LEFT_PAREN":
            self._advance()
            node = self.expression()
            self._expect("RIGHT_PAREN", ")")
            return node
        self._error("Expected an identifier, integer, or parenthesized expression")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scl_parser.py <tokens.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print("Error: token file {!r} was not found.".format(str(input_path)))
        sys.exit(1)

    try:
        with input_path.open("r", encoding="utf-8") as file:
            tokens = json.load(file)
        if not isinstance(tokens, list):
            raise ValueError("JSON root must be a list of token objects")
        for index, token in enumerate(tokens):
            if not isinstance(token, dict) or "type" not in token or "value" not in token:
                raise ValueError("Token at index {} must contain 'type' and 'value'".format(index))
        parser = Parser(tokens)
        tree = parser.begin()
    except (json.JSONDecodeError, ValueError) as error:
        print("Input error: {}".format(error))
        sys.exit(1)
    except ParseError as error:
        print("Syntax error: {}".format(error))
        sys.exit(1)

    output_path = input_path.with_name(input_path.stem + "_parse_tree.json")
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(tree, file, indent=4)
        file.write("\n")
    print("Parsing successful.")
    print("Declared variables: {}".format(", ".join(sorted(parser.declared_identifiers)) or "(none)"))
    print("Parse tree written to: {}".format(output_path))

if __name__ == "__main__":
    main()