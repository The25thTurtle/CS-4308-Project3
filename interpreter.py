"""Interpreter for the SCL subset produced by scl_parser.py.

Usage:
    python interpreter.py program_parse_tree.json

The parser's JSON tree is executed directly. Supported nodes:
Program, Declaration, Assignment, Print, If, While, Condition,
BinaryExpression, Identifier, and Integer.
"""

import json
import sys
from pathlib import Path


class InterpreterError(Exception):
    """Raised when an SCL program cannot be executed."""


class Interpreter:
    def __init__(self, max_loop_iterations=100000):
        self.variables = {}
        self.max_loop_iterations = max_loop_iterations

    def run(self, program):
        if not isinstance(program, dict) or program.get("type") != "Program":
            raise InterpreterError("The input parse tree must have type 'Program'.")

        for statement in program.get("children", []):
            self.execute_statement(statement)

    def execute_statement(self, statement):
        statement_type = statement.get("type")

        if statement_type == "Declaration":
            name = statement["name"]
            if name in self.variables:
                raise InterpreterError(
                    "Variable {!r} has already been declared.".format(name)
                )
            self.variables[name] = self.evaluate(statement["value"])

        elif statement_type == "Assignment":
            name = statement["name"]
            if name not in self.variables:
                raise InterpreterError(
                    "Variable {!r} has not been declared.".format(name)
                )
            self.variables[name] = self.evaluate(statement["value"])

        elif statement_type == "Print":
            value = self.evaluate(statement["value"])
            print(value)

        elif statement_type == "If":
            if self.evaluate_condition(statement["condition"]):
                self.execute_block(statement.get("then", []))
            else:
                self.execute_block(statement.get("else", []))

        elif statement_type == "While":
            iterations = 0
            while self.evaluate_condition(statement["condition"]):
                iterations += 1
                if iterations > self.max_loop_iterations:
                    raise InterpreterError(
                        "Loop exceeded the maximum of {} iterations.".format(
                            self.max_loop_iterations
                        )
                    )
                self.execute_block(statement.get("body", []))

        else:
            raise InterpreterError(
                "Unsupported statement type: {!r}".format(statement_type)
            )

    def execute_block(self, statements):
        for statement in statements:
            self.execute_statement(statement)

    def evaluate_condition(self, condition):
        if condition.get("type") != "Condition":
            raise InterpreterError("Invalid condition node.")

        left = self.evaluate(condition["left"])
        right = self.evaluate(condition["right"])
        operator = condition["operator"]

        comparisons = {
            "==": lambda: left == right,
            "!=": lambda: left != right,
            "<": lambda: left < right,
            ">": lambda: left > right,
            "<=": lambda: left <= right,
            ">=": lambda: left >= right,
        }

        if operator not in comparisons:
            raise InterpreterError(
                "Unsupported comparison operator: {!r}".format(operator)
            )

        try:
            return comparisons[operator]()
        except TypeError as error:
            raise InterpreterError(
                "Cannot compare these values: {}".format(error)
            )

    
    def evaluate(self, expression):
        expression_type = expression.get("type")

        if expression_type == "Integer":
            return expression["value"]

        if expression_type == "Real":
            return expression["value"]

        if expression_type == "String":
             return expression["value"]

        if expression_type == "Identifier":
            name = expression["name"]
            if name not in self.variables:
                raise InterpreterError(
                    "Variable {!r} has not been initialized.".format(name)
                )
            return self.variables[name]

        if expression_type == "UnaryExpression":
            operator = expression["operator"]
            operand = self.evaluate(expression["operand"])

            if operator == "-":
                return -operand
            if operator == "+":
                return operand

            raise InterpreterError(
                "Unsupported unary operator: {!r}".format(operator)
            )

        if expression_type == "BinaryExpression":
            left = self.evaluate(expression["left"])
            right = self.evaluate(expression["right"])
            operator = expression["operator"]

            if operator == "+":
                return left + right
            if operator == "-":
                return left - right
            if operator == "*":
                return left * right
            if operator == "/":
                if right == 0:
                    raise InterpreterError("Division by zero.")
                return left / right

            raise InterpreterError(
                "Unsupported arithmetic operator: {!r}".format(operator)
            )

        raise InterpreterError(
            "Unsupported expression type: {!r}".format(expression_type)
        )

def main():
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <parse_tree.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.is_file():
        print("Error: Parse tree file {!r} was not found.".format(str(input_path)))
        sys.exit(1)

    try:
        with input_path.open("r", encoding="utf-8") as file:
            parse_tree = json.load(file)

        interpreter = Interpreter()
        print("Program output:")
        print("----------------------------------------")
        interpreter.run(parse_tree)
        print("----------------------------------------")
        print("Execution completed successfully.")

    except (json.JSONDecodeError, OSError) as error:
        print("Input error: {}".format(error))
        sys.exit(1)
    except (InterpreterError, KeyError, TypeError, ValueError) as error:
        print("Runtime error: {}".format(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
