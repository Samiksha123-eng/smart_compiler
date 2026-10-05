"""
Python Language Lexical, Syntax, and Semantic Analyzer.
Modular component for Smart Compiler Error Detective.
Uses Python tokenize and AST visitor combined with compiler error explanation rules.
"""

import ast
import tokenize
import io
import re
from typing import List, Tuple, Dict, Any, Optional, Set
from ..models import (
    CompilerPhase,
    Severity,
    ErrorItem,
    TokenItem,
    SymbolItem,
)
from ..base_analyzer import BaseCompilerAnalyzer


PYTHON_BUILTINS = {
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "callable",
    "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod",
    "enumerate", "eval", "exec", "filter", "float", "format", "frozenset", "getattr",
    "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
    "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min",
    "next", "object", "oct", "open", "ord", "pow", "print", "property", "range",
    "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
    "str", "sum", "super", "tuple", "type", "vars", "zip", "__import__",
    "True", "False", "None"
}


class PythonSemanticVisitor(ast.NodeVisitor):
    """
    AST visitor for Python semantic checks:
    - Undeclared / Unbound variables
    - Division by zero
    - Type incompatibilities in constants
    - Duplicate parameter definitions
    - Unreachable code
    """

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.errors: List[ErrorItem] = []
        self.symbol_table: List[SymbolItem] = []
        self.scopes: List[Dict[str, SymbolItem]] = [{}]  # Scope stack
        self.current_func: Optional[str] = None
        self.in_loop: int = 0

    @property
    def current_scope(self) -> Dict[str, SymbolItem]:
        return self.scopes[-1]

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Register function symbol in current scope
        fn_sym = SymbolItem(
            name=node.name,
            data_type="function",
            scope="global" if len(self.scopes) == 1 else self.current_func or "local",
            line_declared=node.lineno,
            initialized=True,
        )
        self.symbol_table.append(fn_sym)
        self.current_scope[node.name] = fn_sym

        # Check for duplicate parameter names
        param_names: Set[str] = set()
        for arg in node.args.args:
            if arg.arg in param_names:
                self.errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SEMANTIC.value,
                        line=arg.lineno,
                        column=arg.col_offset + 1,
                        length=len(arg.arg),
                        title="Duplicate Parameter Name",
                        message=f"Duplicate argument '{arg.arg}' in function definition '{node.name}'.",
                        explanation="In Python, each formal parameter in a function definition must have a unique identifier name.",
                        suggestion=f"Rename duplicate parameter '{arg.arg}'.",
                        rule_reference="Python Language Ref §8.6: Function Definitions",
                    )
                )
            param_names.add(arg.arg)

        # Enter function scope
        prev_func = self.current_func
        self.current_func = node.name
        self.scopes.append({})

        # Add parameters to new scope
        for arg in node.args.args:
            p_sym = SymbolItem(
                name=arg.arg,
                data_type="parameter",
                scope=node.name,
                line_declared=arg.lineno,
                initialized=True,
            )
            self.symbol_table.append(p_sym)
            self.current_scope[arg.arg] = p_sym

        # Check for unreachable statements after return
        found_return = False
        for stmt in node.body:
            if found_return:
                self.errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SEMANTIC.value,
                        line=stmt.lineno,
                        column=stmt.col_offset + 1,
                        length=10,
                        title="Unreachable Code Detected",
                        message="Code statement will never be executed because it follows an unconditional 'return'.",
                        explanation="Any instructions placed after a 'return' statement in the same execution block can never be reached by the runtime interpreter.",
                        suggestion="Remove the dead code or place it before the return statement.",
                        severity=Severity.WARNING.value,
                        rule_reference="Control Flow Analysis: Dead Code Detection",
                    )
                )
            if isinstance(stmt, ast.Return):
                found_return = True

            self.visit(stmt)

        # Exit function scope
        self.scopes.pop()
        self.current_func = prev_func

    def visit_Assign(self, node: ast.Assign):
        # Visit value first
        self.visit(node.value)

        # Register targets
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                scope_name = "global" if len(self.scopes) == 1 else self.current_func or "local"
                sym = SymbolItem(
                    name=var_name,
                    data_type="variable",
                    scope=scope_name,
                    line_declared=target.lineno,
                    initialized=True,
                )
                self.symbol_table.append(sym)
                self.current_scope[var_name] = sym

    def visit_AugAssign(self, node: ast.AugAssign):
        # x += 1 requires x to exist
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            if not self._is_defined(var_name):
                self.errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SEMANTIC.value,
                        line=node.target.lineno,
                        column=node.target.col_offset + 1,
                        length=len(var_name),
                        title="Unbound Local / NameError",
                        message=f"Name '{var_name}' referenced before assignment in augmented assignment '{node.op.__class__.__name__}'.",
                        explanation=f"Augmented assignment like '{var_name} += ...' reads the existing value before modifying it. '{var_name}' must be initialized first.",
                        suggestion=f"Initialize '{var_name}' before this line, e.g. '{var_name} = 0'.",
                        suggested_fix=f"{var_name} = 0",
                        rule_reference="Python Ref §6.2.1: Augmented Assignment",
                    )
                )
        self.visit(node.value)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            var_name = node.id
            if not self._is_defined(var_name):
                # Typo matching
                candidates = list(PYTHON_BUILTINS)
                for s in self.scopes:
                    candidates.extend(s.keys())
                match = BaseCompilerAnalyzer.find_best_match(var_name, candidates)
                sugg = f"Did you mean '{match}'?" if match else f"Define '{var_name}' before referencing it."

                self.errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SEMANTIC.value,
                        line=node.lineno,
                        column=node.col_offset + 1,
                        length=len(var_name),
                        title="NameError (Undefined Variable)",
                        message=f"Name '{var_name}' is not defined.",
                        explanation=f"The identifier '{var_name}' is used in an expression, but Python found no variable or function with this name in local, enclosing, or global scopes.",
                        suggestion=sugg,
                        suggested_fix=f"{match}" if match else f"{var_name} = 0",
                        rule_reference="Python Ref §4.2: Naming and Binding (NameError)",
                    )
                )

    def visit_BinOp(self, node: ast.BinOp):
        # Division by zero check
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SEMANTIC.value,
                        line=node.right.lineno,
                        column=node.right.col_offset + 1,
                        length=1,
                        title="ZeroDivisionError",
                        message="Division or modulo by zero constant.",
                        explanation="Dividing or computing modulo by zero constant evaluates to ZeroDivisionError.",
                        suggestion="Change divisor to a non-zero constant or add a zero check.",
                        rule_reference="Python Ref §6.6: Binary Arithmetic Operations",
                    )
                )

        # Type Mismatch: str + int or int + str
        if isinstance(node.op, ast.Add):
            if (
                isinstance(node.left, ast.Constant)
                and isinstance(node.right, ast.Constant)
            ):
                lval = node.left.value
                rval = node.right.value
                if (isinstance(lval, str) and isinstance(rval, (int, float))) or (
                    isinstance(lval, (int, float)) and isinstance(rval, str)
                ):
                    self.errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=node.lineno,
                            column=node.col_offset + 1,
                            length=10,
                            title="TypeError (Unsupported Operand Types)",
                            message=f"Can only concatenate str (not '{type(rval).__name__}') to str.",
                            explanation="In Python, '+' cannot concatenate a string and a number directly without explicit str() conversion.",
                            suggestion="Use str() conversion: e.g., 'str(x)' or an f-string.",
                            suggested_fix=f"str({lval}) + str({rval})",
                            rule_reference="Python Ref §6.6: TypeError in Binary Operations",
                        )
                    )

        self.generic_visit(node)

    def _is_defined(self, name: str) -> bool:
        if name in PYTHON_BUILTINS:
            return True
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False


class PythonCompilerAnalyzer(BaseCompilerAnalyzer):
    """
    Academic compiler error detective for Python programs.
    Demonstrates Lexical (tokens, indent), Syntax (grammar, colons), and Semantic (name resolution, types).
    """

    def __init__(self):
        super().__init__("Python")

    # =========================================================================
    # PHASE 1: LEXICAL ANALYSIS
    # =========================================================================
    def lexical_analysis(self, source_code: str) -> Tuple[List[TokenItem], List[ErrorItem]]:
        tokens: List[TokenItem] = []
        errors: List[ErrorItem] = []
        token_id = 1

        readline = io.StringIO(source_code).readline
        try:
            for tok in tokenize.generate_tokens(readline):
                tok_type_name = tokenize.tok_name.get(tok.type, "UNKNOWN")

                # Filter out raw COMMENT and NL tokens from core AST tokens for cleaner inspector,
                # but keep track of meaningful tokens
                if tok_type_name not in ("NL", "COMMENT"):
                    tokens.append(
                        TokenItem(
                            id=token_id,
                            type=tok_type_name,
                            value=tok.string,
                            line=tok.start[0],
                            column=tok.start[1] + 1,
                        )
                    )
                    token_id += 1
        except tokenize.TokenError as te:
            msg, (line, col) = te.args
            errors.append(
                ErrorItem(
                    phase=CompilerPhase.LEXICAL.value,
                    line=line,
                    column=col + 1,
                    length=1,
                    title="Lexical / Tokenization Error",
                    message=f"Tokenizer error: {msg}.",
                    explanation="The Python scanner failed while reading tokens. This typically indicates an unterminated string literal, unmatched parentheses, or an illegal character sequence.",
                    suggestion="Check for unclosed quotes '\"' or multi-line string tags ''' before end-of-file.",
                    rule_reference="Python Ref §2.4: Literals & Lexical Structure",
                )
            )
        except IndentationError as ie:
            errors.append(
                ErrorItem(
                    phase=CompilerPhase.LEXICAL.value,
                    line=ie.lineno or 1,
                    column=(ie.offset or 1),
                    length=1,
                    title="IndentationError (Lexical Indent)",
                    message=str(ie.msg),
                    explanation="Python uses the off-side rule where indentation defines code block boundaries. Indentation must be consistent across spaces/tabs.",
                    suggestion="Verify indentation depth (typically 4 spaces per block).",
                    rule_reference="Python Ref §2.1.8: Indentation",
                )
            )
        except Exception as e:
            errors.append(
                ErrorItem(
                    phase=CompilerPhase.LEXICAL.value,
                    line=1,
                    column=1,
                    length=1,
                    title="Lexical Analysis Error",
                    message=str(e),
                    explanation="Error encountered during lexical scanning.",
                    suggestion="Check source code formatting.",
                    rule_reference="Python Lexical Grammar",
                )
            )

        # Check for illegal characters (e.g. $, ~ where not expected)
        lines = source_code.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for col_idx, ch in enumerate(line, start=1):
                if ch in ("$", ";") and not self._is_in_string_or_comment(line, col_idx - 1):
                    if ch == "$":
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.LEXICAL.value,
                                line=line_num,
                                column=col_idx,
                                length=1,
                                title="Illegal Character '$'",
                                message="Invalid character '$' in Python source.",
                                explanation="The '$' symbol is not a valid operator, identifier character, or token in Python syntax.",
                                suggestion="Remove '$' symbol.",
                                suggested_fix="",
                                rule_reference="Python Ref §2.3: Identifiers and Keywords",
                            )
                        )

        return tokens, errors

    # =========================================================================
    # PHASE 2: SYNTAX ANALYSIS
    # =========================================================================
    def syntax_analysis(
        self, tokens: List[TokenItem], source_code: str
    ) -> Tuple[Any, List[ErrorItem]]:
        errors: List[ErrorItem] = []
        parsed_tree = None

        # 1. Check Missing Colons on control structures
        lines = source_code.splitlines()
        block_headers = (
            "def ", "class ", "if ", "elif ", "else:", "while ",
            "for ", "try:", "except", "finally:", "with "
        )

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for header in block_headers:
                # If line starts with header keyword
                kw = header.strip(" :")
                if re.match(rf"^{kw}\b", stripped):
                    # Check if line ends with a colon
                    # Exclude lines that continue with backslash or parentheses
                    if not stripped.endswith(":") and not stripped.endswith("\\"):
                        # If closing parenthesis is present or it's a simple statement
                        if ")" in stripped or kw in ("else", "try", "finally"):
                            errors.append(
                                ErrorItem(
                                    phase=CompilerPhase.SYNTAX.value,
                                    line=line_idx,
                                    column=len(line.rstrip()) + 1,
                                    length=1,
                                    title=f"Missing Colon ':' after '{kw}'",
                                    message=f"SyntaxError: expected ':' at end of '{kw}' statement.",
                                    explanation=f"In Python, compound statements introducing an indented block (such as 'if', 'for', 'def', 'while') must end with a colon ':'.",
                                    suggestion=f"Append a colon ':' to line {line_idx}.",
                                    suggested_fix=f"{line.rstrip()}:",
                                    rule_reference="Python Ref §8: Compound Statements",
                                )
                            )

        # 2. Attempt AST Parse
        try:
            parsed_tree = ast.parse(source_code)
        except SyntaxError as se:
            msg = se.msg or "Invalid syntax"
            line = se.lineno or 1
            col = se.offset or 1
            text = se.text or ""

            # Enhance explanation based on common SyntaxError messages
            title = "SyntaxError"
            explanation = "The Python parser failed to construct a valid Abstract Syntax Tree (AST)."
            suggestion = "Review grammar and punctuation around the highlighted position."
            fix = None

            if "invalid syntax" in msg.lower():
                title = "Invalid Syntax"
                explanation = "Python could not parse this statement. Common causes include missing operators, mismatched brackets, or unexpected tokens."
                suggestion = "Check for missing parentheses, colons, or misplaced keywords."
            elif "expected ':'" in msg.lower():
                title = "Expected ':'"
                explanation = "Python compound statements require a trailing colon before an indented suite."
                suggestion = "Add ':' at the end of the clause header."
                fix = f"{text.rstrip()}:"
            elif "unindent does not match" in msg.lower():
                title = "IndentationError: Unindent Mismatch"
                explanation = "The closing indentation level does not align with any outer indentation block."
                suggestion = "Align spaces to match the parent block."
            elif "expected an indented block" in msg.lower():
                title = "IndentationError: Expected Indented Block"
                explanation = "A statement following a colon must be indented relative to the header line."
                suggestion = "Indent the statements inside the body or add 'pass'."
                fix = "    pass"
            elif "cannot assign to" in msg.lower():
                title = "SyntaxError: Cannot Assign to Expression"
                explanation = "The left-hand side of an assignment statement must be a valid variable or target, not a constant literal."
                suggestion = "Swap the assignment order: 'variable = value'."

            errors.append(
                ErrorItem(
                    phase=CompilerPhase.SYNTAX.value,
                    line=line,
                    column=col,
                    length=max(1, len(text.strip())),
                    title=title,
                    message=f"SyntaxError: {msg}.",
                    explanation=explanation,
                    suggestion=suggestion,
                    suggested_fix=fix,
                    rule_reference="Python Language Grammar §8",
                )
            )

        return parsed_tree, errors

    # =========================================================================
    # PHASE 3: SEMANTIC ANALYSIS
    # =========================================================================
    def semantic_analysis(
        self, ast_or_cst: Any, tokens: List[TokenItem], source_code: str
    ) -> Tuple[List[SymbolItem], List[ErrorItem]]:
        if ast_or_cst is None:
            # Cannot do deep AST semantic analysis if syntax parsing completely failed
            return [], []

        lines = source_code.splitlines()
        visitor = PythonSemanticVisitor(lines)
        try:
            visitor.visit(ast_or_cst)
        except Exception:
            pass

        return visitor.symbol_table, visitor.errors

    @staticmethod
    def _is_in_string_or_comment(line: str, index: int) -> bool:
        in_str = False
        quote = None
        for i, ch in enumerate(line):
            if i >= index:
                break
            if ch == "#" and not in_str:
                return True
            if ch in ("'", '"'):
                if not in_str:
                    in_str = True
                    quote = ch
                elif ch == quote:
                    in_str = False
        return in_str
