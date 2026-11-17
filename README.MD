SCL Interpreter (Python)

Files:
- scl_scanner.py: turns SCL source into tokens (lexical analysis)
- scl_parser.py: checks grammar and creates an in-memory parse tree
- interpreter.py: executes the parse tree
- main.py: runs all three stages in order
- sample.scl: sample input

Run the complete interpreter:
    python main.py sample.scl

Run the stages separately:
    python scl_scanner.py sample.scl
    python scl_parser.py sample_program.json
    python interpreter.py sample_parse_tree.json

Supported syntax:
    int name = expression;
    name = expression;
    print(expression);
    if (condition) { statements } else { statements }
    while (condition) { statements }

Data values: integer, real, and double-quoted string literals.
Arithmetic: +, -, *, / and unary minus.
Comparisons: ==, !=, <, >, <=, >=.
Comments: // to end of line.

Note:
The language keeps the original 'int' declaration keyword. The interpreter
accepts integer or real numeric values for these variables; 'int' is currently
the declaration syntax inherited from the earlier scanner/parser assignment,
not a strict type checker.
