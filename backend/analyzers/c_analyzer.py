"""
C Language Lexical, Syntax, and Semantic Analyzer.
Modular component for Smart Compiler Error Detective.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from ..models import (
    CompilerPhase,
    Severity,
    ErrorItem,
    TokenItem,
    SymbolItem,
)
from ..base_analyzer import BaseCompilerAnalyzer


C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while"
}

C_TYPES = {"int", "float", "double", "char", "void", "short", "long", "unsigned", "signed"}


class CCompilerAnalyzer(BaseCompilerAnalyzer):
    """
    Academic compiler error detective for C programs.
    Demonstrates Lexical, Syntax, and Semantic analysis phases.
    """

    def __init__(self):
        super().__init__("C")

    # =========================================================================
    # PHASE 1: LEXICAL ANALYSIS
    # =========================================================================
    def lexical_analysis(self, source_code: str) -> Tuple[List[TokenItem], List[ErrorItem]]:
        tokens: List[TokenItem] = []
        errors: List[ErrorItem] = []
        token_id = 1

        lines = source_code.splitlines(keepends=True)
        in_multiline_comment = False
        comment_start_line = 0
        comment_start_col = 0

        for line_num, line in enumerate(lines, start=1):
            col = 1
            i = 0
            n = len(line)

            while i < n:
                char = line[i]

                # Check if we are inside a multi-line comment /* ... */
                if in_multiline_comment:
                    close_idx = line.find("*/", i)
                    if close_idx != -1:
                        in_multiline_comment = False
                        i = close_idx + 2
                        col += (close_idx + 2 - i)
                        continue
                    else:
                        break

                # Whitespace
                if char in " \t\r\n":
                    i += 1
                    col += 1
                    continue

                # Single-line comment //
                if char == "/" and i + 1 < n and line[i + 1] == "/":
                    break

                # Multi-line comment start /*
                if char == "/" and i + 1 < n and line[i + 1] == "*":
                    in_multiline_comment = True
                    comment_start_line = line_num
                    comment_start_col = col
                    i += 2
                    col += 2
                    continue

                # Preprocessor directives: #include <stdio.h>, #define MAX 100
                if char == "#":
                    prep_line = line[i:].rstrip("\r\n")
                    tokens.append(TokenItem(token_id, "PREPROCESSOR", prep_line, line_num, col))
                    token_id += 1
                    i += len(prep_line)
                    col += len(prep_line)
                    continue

                # String literal: "..."
                if char == '"':
                    start_col = col
                    str_val = '"'
                    i += 1
                    col += 1
                    escaped = False
                    closed = False

                    while i < n:
                        c = line[i]
                        if c in "\r\n":
                            break
                        str_val += c
                        i += 1
                        col += 1
                        if escaped:
                            escaped = False
                        elif c == "\\":
                            escaped = True
                        elif c == '"':
                            closed = True
                            break

                    if not closed:
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.LEXICAL.value,
                                line=line_num,
                                column=start_col,
                                length=len(str_val),
                                title="Unterminated String Literal",
                                message="Missing closing double quote (\") on string literal.",
                                explanation="In C, string literals must be enclosed by matching double quotation marks on the same line (unless escaped with a backslash).",
                                suggestion="Add a closing quote '\"' before the end of the line.",
                                suggested_fix=f'{str_val}"',
                                rule_reference="C11 §6.4.5: String Literals",
                            )
                        )
                    tokens.append(TokenItem(token_id, "STRING_LITERAL", str_val, line_num, start_col))
                    token_id += 1
                    continue

                # Character literal: '...'
                if char == "'":
                    start_col = col
                    char_val = "'"
                    i += 1
                    col += 1
                    escaped = False
                    closed = False

                    while i < n:
                        c = line[i]
                        if c in "\r\n":
                            break
                        char_val += c
                        i += 1
                        col += 1
                        if escaped:
                            escaped = False
                        elif c == "\\":
                            escaped = True
                        elif c == "'":
                            closed = True
                            break

                    if not closed:
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.LEXICAL.value,
                                line=line_num,
                                column=start_col,
                                length=len(char_val),
                                title="Unterminated Character Constant",
                                message="Missing closing single quote (') on character literal.",
                                explanation="Character constants in C must be enclosed by single quotation marks and cannot span multiple lines.",
                                suggestion="Add a closing single quote '\'' at the end of the character constant.",
                                suggested_fix=f"{char_val}'",
                                rule_reference="C11 §6.4.4.4: Character Constants",
                            )
                        )
                    elif len(char_val) > 4 or (len(char_val) == 4 and not char_val.startswith("'\\")):
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.LEXICAL.value,
                                line=line_num,
                                column=start_col,
                                length=len(char_val),
                                title="Multi-Character Character Constant",
                                message=f"Character constant {char_val} contains multiple characters.",
                                explanation="In C, a character literal in single quotes can hold only one character (or one escape sequence). Use double quotes for strings.",
                                suggestion=f'Change single quotes to double quotes: "{char_val[1:-1]}"',
                                suggested_fix=f'"{char_val[1:-1]}"',
                                rule_reference="C11 §6.4.4.4: Character Constants",
                            )
                        )
                    tokens.append(TokenItem(token_id, "CHAR_LITERAL", char_val, line_num, start_col))
                    token_id += 1
                    continue

                # Identifiers or Keywords
                if char.isalpha() or char == "_":
                    id_match = re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*", line[i:])
                    if id_match:
                        lexeme = id_match.group(0)
                        token_type = "KEYWORD" if lexeme in C_KEYWORDS else "IDENTIFIER"
                        tokens.append(TokenItem(token_id, token_type, lexeme, line_num, col))
                        token_id += 1
                        i += len(lexeme)
                        col += len(lexeme)
                        continue

                # Numbers (Decimal, Hex, Octal, Float)
                if char.isdigit():
                    num_match = re.match(r"^(0[xX][0-9a-fA-F]+|[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?|[0-9]+[a-zA-Z0-9_.]*)", line[i:])
                    if num_match:
                        lexeme = num_match.group(0)
                        if re.search(r"[a-zA-Z_]", lexeme) and not re.match(r"^0[xX][0-9a-fA-F]+$", lexeme):
                            errors.append(
                                ErrorItem(
                                    phase=CompilerPhase.LEXICAL.value,
                                    line=line_num,
                                    column=col,
                                    length=len(lexeme),
                                    title="Invalid Numeric Literal",
                                    message=f"Malformed number suffix or invalid identifier '{lexeme}'.",
                                    explanation="Numeric constants cannot have invalid alphanumeric suffixes. If this was intended as an identifier, identifiers cannot start with a digit.",
                                    suggestion="Separate the number and identifier, or rename identifier if starting with a digit.",
                                    rule_reference="C11 §6.4.4: Constants",
                                )
                            )
                        elif lexeme.count(".") > 1:
                            errors.append(
                                ErrorItem(
                                    phase=CompilerPhase.LEXICAL.value,
                                    line=line_num,
                                    column=col,
                                    length=len(lexeme),
                                    title="Malformed Floating-Point Literal",
                                    message=f"Too many decimal points in floating constant '{lexeme}'.",
                                    explanation="A floating-point literal in C can contain at most one decimal point.",
                                    suggestion="Remove extraneous decimal points.",
                                    rule_reference="C11 §6.4.4.2: Floating Constants",
                                )
                            )
                        tokens.append(TokenItem(token_id, "NUMBER", lexeme, line_num, col))
                        token_id += 1
                        i += len(lexeme)
                        col += len(lexeme)
                        continue

                # Multi-character Operators
                two_char_ops = ["==", "!=", "<=", ">=", "&&", "||", "++", "--", "+=", "-=", "*=", "/=", "%=", "->", "<<", ">>"]
                matched_op = None
                if i + 1 < n and line[i:i+2] in two_char_ops:
                    matched_op = line[i:i+2]

                if matched_op:
                    tokens.append(TokenItem(token_id, "OPERATOR", matched_op, line_num, col))
                    token_id += 1
                    i += len(matched_op)
                    col += len(matched_op)
                    continue

                # Single-character Operators & Delimiters
                single_ops = "+-*/%=<>!&|^~."
                delimiters = ";,{}[ ]():"
                if char in single_ops:
                    tokens.append(TokenItem(token_id, "OPERATOR", char, line_num, col))
                    token_id += 1
                    i += 1
                    col += 1
                    continue
                elif char in delimiters:
                    tokens.append(TokenItem(token_id, "DELIMITER", char, line_num, col))
                    token_id += 1
                    i += 1
                    col += 1
                    continue

                # Unrecognized character -> Lexical Error!
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.LEXICAL.value,
                        line=line_num,
                        column=col,
                        length=1,
                        title="Illegal Character",
                        message=f"Stray '{char}' in program.",
                        explanation=f"The character '{char}' is not a valid token or symbol in the C language character set outside of strings or comments.",
                        suggestion=f"Remove the stray character '{char}'.",
                        suggested_fix="",
                        rule_reference="C11 §6.4: Lexical Elements",
                    )
                )
                i += 1
                col += 1

        if in_multiline_comment:
            errors.append(
                ErrorItem(
                    phase=CompilerPhase.LEXICAL.value,
                    line=comment_start_line,
                    column=comment_start_col,
                    length=2,
                    title="Unterminated Multi-Line Comment",
                    message="Comment began with '/*' but was never closed before end-of-file.",
                    explanation="In C, block comments beginning with '/*' must be terminated with matching '*/'.",
                    suggestion="Add '*/' to terminate the comment block.",
                    suggested_fix="*/",
                    rule_reference="C11 §6.4.9: Comments",
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
        lines = source_code.splitlines()

        # 1. Bracket Matching Stack
        stack: List[Tuple[str, int, int]] = []
        bracket_pairs = {")": "(", "}": "{", "]": "["}
        bracket_names = {"(": "parenthesis", "{": "curly brace", "[": "square bracket"}

        for tok in tokens:
            if tok.value in "({[":
                stack.append((tok.value, tok.line, tok.column))
            elif tok.value in ")}]":
                expected = bracket_pairs[tok.value]
                if not stack:
                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SYNTAX.value,
                            line=tok.line,
                            column=tok.column,
                            length=1,
                            title="Unmatched Closing Bracket",
                            message=f"Extraneous closing '{tok.value}' without matching '{expected}'.",
                            explanation=f"The parser encountered a closing '{tok.value}' but there was no corresponding opening '{expected}'.",
                            suggestion=f"Remove the extra '{tok.value}' or add a preceding '{expected}'.",
                            rule_reference="C Grammar: Phrase Structure Grammar §6.8",
                        )
                    )
                else:
                    open_char, open_line, _ = stack.pop()
                    if open_char != expected:
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.SYNTAX.value,
                                line=tok.line,
                                column=tok.column,
                                length=1,
                                title="Mismatched Bracket Types",
                                message=f"Expected '{self._get_closing(open_char)}' to close '{open_char}' from line {open_line}, but found '{tok.value}'.",
                                explanation="Brackets and braces must be closed in symmetrical Last-In-First-Out (LIFO) order.",
                                suggestion=f"Replace '{tok.value}' with '{self._get_closing(open_char)}'.",
                                suggested_fix=self._get_closing(open_char),
                                rule_reference="C Grammar: Compound Statements & Expressions",
                            )
                        )

        for open_char, open_line, open_col in stack:
            closing = self._get_closing(open_char)
            errors.append(
                ErrorItem(
                    phase=CompilerPhase.SYNTAX.value,
                    line=open_line,
                    column=open_col,
                    length=1,
                    title="Unclosed Bracket / Block",
                    message=f"Unclosed '{open_char}' ({bracket_names.get(open_char, 'bracket')}); missing '{closing}'.",
                    explanation=f"An opening '{open_char}' was never matched by a closing '{closing}' before reaching the end of the file.",
                    suggestion=f"Add a closing '{closing}' at the end of the corresponding block or statement.",
                    suggested_fix=closing,
                    rule_reference="C Grammar: Nested Blocks & Grouping",
                )
            )

        # 2. Line-by-Line Syntax Verification
        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("#"):
                continue

            needs_semicolon = False
            is_control_header = bool(
                re.match(r"^(if|while|for|else\s+if|switch)\s*\(.*\)$", stripped)
                or stripped == "else"
                or stripped.endswith("{")
                or stripped.endswith("}")
                or stripped.endswith(":")
                or stripped.endswith(";")
                or stripped.endswith(",")
                or stripped.endswith("\\")
            )

            is_func_header = bool(
                re.match(r"^(int|float|double|char|void|long|short)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\)$", stripped)
            )

            if not is_control_header and not is_func_header:
                if (
                    re.match(r"^(return\b|break\b|continue\b)", stripped)
                    or re.match(r"^(int|float|double|char|void|long|short)(\s*\*|\s+)[a-zA-Z_]", stripped)
                    or re.search(r"=\s*[^;]+$", stripped)
                    or re.search(r"\bprintf\s*\(.*\)$", stripped)
                    or re.search(r"\bscanf\s*\(.*\)$", stripped)
                    or re.search(r"\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\)$", stripped)
                ):
                    needs_semicolon = True

            if needs_semicolon and not stripped.endswith(";"):
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=len(line.rstrip()) + 1,
                        length=1,
                        title="Missing Semicolon ';'",
                        message="Expected ';' at the end of statement.",
                        explanation="In C, every declaration, assignment, expression statement, and jump statement must terminate with a semicolon ';'.",
                        suggestion=f"Append a semicolon ';' to the end of line {line_idx}.",
                        suggested_fix=f"{line.rstrip()};",
                        rule_reference="C11 §6.8: Statements and Blocks",
                    )
                )

            # Malformed `if` without parentheses
            if re.match(r"^if\s+[^(].*", stripped) and not stripped.startswith("if ("):
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=stripped.find("if") + 1,
                        length=2,
                        title="Malformed 'if' Statement",
                        message="Condition in 'if' statement must be enclosed in parentheses '()'.",
                        explanation="C grammar requires selection statements to format conditions as `if (expression)`.",
                        suggestion="Enclose the condition in parentheses, e.g., `if (condition)`.",
                        rule_reference="C11 §6.8.4.1: Selection Statements",
                    )
                )

            # Malformed `while` without parentheses
            if re.match(r"^while\s+[^(].*", stripped) and not stripped.startswith("while (") and not stripped.endswith(";"):
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=stripped.find("while") + 1,
                        length=5,
                        title="Malformed 'while' Loop",
                        message="Loop condition in 'while' must be enclosed in parentheses '()'.",
                        explanation="In C, while-loops require the conditional expression to be enclosed in parentheses.",
                        suggestion="Enclose the condition in parentheses, e.g., `while (condition)`.",
                        rule_reference="C11 §6.8.5.1: While Iteration Statements",
                    )
                )

            # Malformed `for` loop header
            for_match = re.match(r"^for\s*\((.*)\)", stripped)
            if for_match:
                header_content = for_match.group(1)
                semi_count = header_content.count(";")
                if semi_count != 2:
                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SYNTAX.value,
                            line=line_idx,
                            column=stripped.find("for") + 1,
                            length=len(stripped),
                            title="Malformed 'for' Loop Header",
                            message=f"For loop requires exactly 2 semicolons separating clauses, found {semi_count}.",
                            explanation="A standard C for-loop has the structure: `for (clause-1; expression-2; expression-3)`. Exactly two semicolons are required.",
                            suggestion="Format the loop as `for (init; condition; update)`.",
                            rule_reference="C11 §6.8.5.3: For Iteration Statements",
                        )
                    )

            # Dangling operators
            if re.search(r"(=|\+|\-|\*|/|%)\s*;", stripped):
                match = re.search(r"(=|\+|\-|\*|/|%)\s*;", stripped)
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=match.start() + 1,
                        length=1,
                        title="Expected Expression Before ';'",
                        message=f"Operator '{match.group(1)}' has missing right-hand operand before ';'.",
                        explanation="Binary operators in C require both a left-hand and right-hand operand to form a syntactically valid expression.",
                        suggestion="Provide a valid value or variable after the operator before the semicolon.",
                        rule_reference="C11 §6.5: Expressions Grammar",
                    )
                )

        return None, errors

    # =========================================================================
    # PHASE 3: SEMANTIC ANALYSIS (Symbol Table, Types, Scopes)
    # =========================================================================
    def semantic_analysis(
        self, ast_or_cst: Any, tokens: List[TokenItem], source_code: str
    ) -> Tuple[List[SymbolItem], List[ErrorItem]]:
        errors: List[ErrorItem] = []
        symbol_table: List[SymbolItem] = []
        scope_symbols: Dict[str, Dict[str, SymbolItem]] = {"global": {}}
        current_scope = "global"
        current_func_type: Optional[str] = None
        current_func_has_return = False

        standard_c_symbols = {
            "printf", "scanf", "puts", "gets", "getchar", "putchar",
            "malloc", "calloc", "free", "realloc", "exit", "abort",
            "strlen", "strcpy", "strncpy", "strcat", "strcmp", "strstr",
            "atoi", "atof", "atol", "abs", "sqrt", "pow", "sin", "cos",
            "fopen", "fclose", "fread", "fwrite", "fprintf", "fscanf",
            "NULL", "EOF", "size_t"
        }

        i = 0
        n = len(tokens)

        while i < n:
            tok = tokens[i]

            # Skip preprocessor tokens from semantic symbol checking
            if tok.type == "PREPROCESSOR":
                i += 1
                continue

            # Detect function definitions: <type> [pointer]* <identifier> ( ... ) {
            if tok.type == "KEYWORD" and tok.value in C_TYPES:
                # Lookahead to see if this is a function declaration: <type> [*] <name> (
                k = i + 1
                while k < n and tokens[k].value == "*":
                    k += 1
                if k + 1 < n and tokens[k].type == "IDENTIFIER" and tokens[k + 1].value == "(":
                    func_ret_type = tok.value
                    func_name = tokens[k].value
                    current_scope = func_name
                    current_func_type = func_ret_type
                    current_func_has_return = False
                    if current_scope not in scope_symbols:
                        scope_symbols[current_scope] = {}

                    func_sym = SymbolItem(
                        name=func_name,
                        data_type=f"function()->{func_ret_type}",
                        scope="global",
                        line_declared=tok.line,
                        initialized=True,
                    )
                    symbol_table.append(func_sym)
                    scope_symbols["global"][func_name] = func_sym

                    # Advance past function parameter list
                    i = k + 2
                    while i < n and tokens[i].value != ")":
                        if tokens[i].type == "KEYWORD" and tokens[i].value in C_TYPES:
                            p_type = tokens[i].value
                            pj = i + 1
                            while pj < n and tokens[pj].value == "*":
                                p_type += "*"
                                pj += 1
                            if pj < n and tokens[pj].type == "IDENTIFIER":
                                p_name = tokens[pj].value
                                p_sym = SymbolItem(
                                    name=p_name,
                                    data_type=p_type,
                                    scope=current_scope,
                                    line_declared=tokens[pj].line,
                                    initialized=True,
                                )
                                symbol_table.append(p_sym)
                                scope_symbols[current_scope][p_name] = p_sym
                                i = pj
                        i += 1
                    i += 1
                    continue

                # Otherwise, it is a Variable Declaration: type [*] var1 [= expr1], var2 [= expr2];
                var_type = tok.value
                j = i + 1
                while j < n and tokens[j].value != ";":
                    # Check pointer
                    effective_type = var_type
                    while j < n and tokens[j].value == "*":
                        effective_type += "*"
                        j += 1

                    if j < n and tokens[j].type == "IDENTIFIER":
                        var_name = tokens[j].value
                        var_line = tokens[j].line
                        var_col = tokens[j].column

                        active_scope = scope_symbols.get(current_scope, {})
                        if var_name in active_scope:
                            errors.append(
                                ErrorItem(
                                    phase=CompilerPhase.SEMANTIC.value,
                                    line=var_line,
                                    column=var_col,
                                    length=len(var_name),
                                    title="Variable Redeclaration",
                                    message=f"Redefinition of '{var_name}' in the same scope (previously declared at line {active_scope[var_name].line_declared}).",
                                    explanation=f"In C, '{var_name}' cannot be declared multiple times in the same scope block.",
                                    suggestion=f"Rename '{var_name}' or remove the duplicate declaration.",
                                    rule_reference="C11 §6.7: Declarations & Scope",
                                )
                            )
                        else:
                            is_init = False
                            sym = SymbolItem(
                                name=var_name,
                                data_type=effective_type,
                                scope=current_scope,
                                line_declared=var_line,
                                initialized=False,
                            )
                            symbol_table.append(sym)
                            if current_scope not in scope_symbols:
                                scope_symbols[current_scope] = {}
                            scope_symbols[current_scope][var_name] = sym

                        j += 1

                        # Check if initialized with '='
                        if j < n and tokens[j].value == "=":
                            if var_name in scope_symbols.get(current_scope, {}):
                                scope_symbols[current_scope][var_name].initialized = True
                            j += 1

                            # Scan RHS expression until top-level ',' or ';'
                            bracket_depth = 0
                            while j < n and (tokens[j].value != ";" and (tokens[j].value != "," or bracket_depth > 0)):
                                expr_tok = tokens[j]
                                if expr_tok.value in "([{":
                                    bracket_depth += 1
                                elif expr_tok.value in ")]}":
                                    bracket_depth = max(0, bracket_depth - 1)

                                # Type mismatch: string assigned to int
                                if effective_type in ("int", "short", "long", "float", "double") and expr_tok.type == "STRING_LITERAL":
                                    errors.append(
                                        ErrorItem(
                                            phase=CompilerPhase.SEMANTIC.value,
                                            line=expr_tok.line,
                                            column=expr_tok.column,
                                            length=len(expr_tok.value),
                                            title="Incompatible Type Assignment",
                                            message=f"Cannot assign string literal {expr_tok.value} to variable '{var_name}' of type '{effective_type}'.",
                                            explanation=f"A string literal cannot be assigned directly to an integer/float variable without explicit conversion.",
                                            suggestion=f"Change variable type to 'char*' or assign an integer/numeric literal.",
                                            suggested_fix=f"char* {var_name} = {expr_tok.value};",
                                            rule_reference="C11 §6.5.16.1: Assignment Type Compatibility",
                                        )
                                    )

                                # Division by zero in RHS
                                if expr_tok.type == "OPERATOR" and expr_tok.value in ("/", "%"):
                                    if j + 1 < n and tokens[j + 1].type == "NUMBER" and tokens[j + 1].value in ("0", "0.0"):
                                        errors.append(
                                            ErrorItem(
                                                phase=CompilerPhase.SEMANTIC.value,
                                                line=tokens[j + 1].line,
                                                column=tokens[j + 1].column,
                                                length=len(tokens[j + 1].value),
                                                title="Division by Zero",
                                                message=f"Constant division or modulo by zero with '{expr_tok.value} 0'.",
                                                explanation="Division or modulo by zero constant evaluates to undefined behavior in C.",
                                                suggestion="Ensure divisor expression evaluates to a non-zero value.",
                                                rule_reference="C11 §6.5.5: Multiplicative Operators",
                                            )
                                        )

                                # Check identifiers inside RHS expression for undeclared usage
                                if expr_tok.type == "IDENTIFIER":
                                    id_val = expr_tok.value
                                    in_loc = id_val in scope_symbols.get(current_scope, {})
                                    in_glob = id_val in scope_symbols.get("global", {})
                                    in_std = id_val in standard_c_symbols
                                    if not (in_loc or in_glob or in_std or id_val == current_scope):
                                        all_declared = list(scope_symbols.get(current_scope, {}).keys()) + list(scope_symbols.get("global", {}).keys()) + list(standard_c_symbols)
                                        best_match = self.find_best_match(id_val, all_declared)
                                        sugg = f"Did you mean '{best_match}'?" if best_match else f"Declare '{id_val}' before use, e.g. 'int {id_val};'."
                                        errors.append(
                                            ErrorItem(
                                                phase=CompilerPhase.SEMANTIC.value,
                                                line=expr_tok.line,
                                                column=expr_tok.column,
                                                length=len(id_val),
                                                title="Undeclared Identifier",
                                                message=f"Use of undeclared identifier '{id_val}'.",
                                                explanation=f"The identifier '{id_val}' was referenced before being declared in scope '{current_scope}'.",
                                                suggestion=sugg,
                                                suggested_fix=f"{best_match}" if best_match else f"int {id_val};",
                                                rule_reference="C11 §6.5.1: Primary Expressions / Scope",
                                            )
                                        )

                                j += 1

                        if j < n and tokens[j].value == ",":
                            j += 1
                    else:
                        j += 1

                i = j
                continue

            # Scope exit on closing brace for function
            if tok.value == "}" and current_scope != "global":
                if current_func_type and current_func_type != "void" and not current_func_has_return:
                    if current_scope != "main":
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.SEMANTIC.value,
                                line=tok.line,
                                column=tok.column,
                                length=1,
                                title="Missing Return Statement",
                                message=f"Non-void function '{current_scope}' (return type '{current_func_type}') reaches end of function without returning a value.",
                                explanation=f"Functions with return type '{current_func_type}' must return a value matching their declaration.",
                                suggestion=f"Add a 'return <{current_func_type}>;' statement before the closing brace.",
                                suggested_fix="return 0;",
                                rule_reference="C11 §6.8.6.4: Return Statements",
                            )
                        )
                current_scope = "global"
                current_func_type = None
                i += 1
                continue

            # Return statement
            if tok.type == "KEYWORD" and tok.value == "return":
                current_func_has_return = True
                if current_func_type == "void":
                    if i + 1 < n and tokens[i + 1].value != ";":
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.SEMANTIC.value,
                                line=tok.line,
                                column=tok.column,
                                length=6,
                                title="Void Function Returning Value",
                                message=f"Function '{current_scope}' has return type 'void' and cannot return a value.",
                                explanation="A function declared with 'void' return type does not return a value.",
                                suggestion="Use bare 'return;' without an expression.",
                                suggested_fix="return;",
                                rule_reference="C11 §6.8.6.4: Return Statements",
                            )
                        )
                i += 1
                continue

            # Regular Identifier Usage / Undeclared Check
            if tok.type == "IDENTIFIER":
                ident_name = tok.value
                in_local = ident_name in scope_symbols.get(current_scope, {})
                in_global = ident_name in scope_symbols.get("global", {})
                in_stdlib = ident_name in standard_c_symbols

                if not (in_local or in_global or in_stdlib or ident_name == current_scope):
                    all_declared = list(scope_symbols.get(current_scope, {}).keys()) + list(scope_symbols.get("global", {}).keys()) + list(standard_c_symbols)
                    best_match = self.find_best_match(ident_name, all_declared)
                    suggestion = f"Did you mean '{best_match}'?" if best_match else f"Declare '{ident_name}' before use, e.g. 'int {ident_name};'."

                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=tok.line,
                            column=tok.column,
                            length=len(ident_name),
                            title="Undeclared Identifier",
                            message=f"Use of undeclared identifier '{ident_name}'.",
                            explanation=f"The identifier '{ident_name}' was referenced before being declared in scope '{current_scope}'.",
                            suggestion=suggestion,
                            suggested_fix=f"{best_match}" if best_match else f"int {ident_name};",
                            rule_reference="C11 §6.5.1: Primary Expressions / Scope Resolution",
                        )
                    )
                else:
                    for sym in symbol_table:
                        if sym.name == ident_name and sym.scope in (current_scope, "global"):
                            sym.usage_count += 1
                            break

            # Check for Division by Zero in standalone expressions
            if tok.type == "OPERATOR" and tok.value in ("/", "%"):
                if i + 1 < n:
                    next_tok = tokens[i + 1]
                    if next_tok.type == "NUMBER" and next_tok.value in ("0", "0.0"):
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.SEMANTIC.value,
                                line=next_tok.line,
                                column=next_tok.column,
                                length=len(next_tok.value),
                                title="Division by Zero",
                                message=f"Constant division or modulo by zero with '{tok.value} 0'.",
                                explanation="Division or modulo by zero yields undefined behavior at runtime.",
                                suggestion="Ensure divisor expression evaluates to a non-zero value.",
                                rule_reference="C11 §6.5.5: Multiplicative Operators",
                            )
                        )

            i += 1

        return symbol_table, errors

    @staticmethod
    def _get_closing(open_bracket: str) -> str:
        pairs = {"(": ")", "{": "}", "[": "]"}
        return pairs.get(open_bracket, ")")
