"""
C++ Language Lexical, Syntax, and Semantic Analyzer.
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


CPP_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
    "bool", "break", "case", "catch", "char", "char16_t", "char32_t", "class",
    "compl", "const", "constexpr", "const_cast", "continue", "decltype", "default",
    "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit", "export",
    "extern", "false", "float", "for", "friend", "goto", "if", "inline", "int",
    "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
    "operator", "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch", "template", "this",
    "thread_local", "throw", "true", "try", "typedef", "typeid", "typename",
    "union", "unsigned", "using", "virtual", "void", "volatile", "wchar_t",
    "while", "xor", "xor_eq", "override", "final"
}

BASE_CPP_TYPES = {
    "int", "float", "double", "char", "void", "bool", "short", "long",
    "string", "auto", "unsigned", "signed"
}


class CppCompilerAnalyzer(BaseCompilerAnalyzer):
    """
    Academic compiler error detective for C++ programs.
    Demonstrates OOP/C++ specific lexical, syntax, and semantic checks.
    """

    def __init__(self):
        super().__init__("C++")

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

                if in_multiline_comment:
                    close_idx = line.find("*/", i)
                    if close_idx != -1:
                        in_multiline_comment = False
                        i = close_idx + 2
                        col += (close_idx + 2 - i)
                        continue
                    else:
                        break

                if char in " \t\r\n":
                    i += 1
                    col += 1
                    continue

                if char == "/" and i + 1 < n and line[i + 1] == "/":
                    break

                if char == "/" and i + 1 < n and line[i + 1] == "*":
                    in_multiline_comment = True
                    comment_start_line = line_num
                    comment_start_col = col
                    i += 2
                    col += 2
                    continue

                # Preprocessor: #include <iostream>, #define
                if char == "#":
                    prep_line = line[i:].rstrip("\r\n")
                    tokens.append(TokenItem(token_id, "PREPROCESSOR", prep_line, line_num, col))
                    token_id += 1
                    i += len(prep_line)
                    col += len(prep_line)
                    continue

                # String literal
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
                                message="Missing closing double quote (\") on C++ string literal.",
                                explanation="C++ string literals must be properly closed on the same line or use raw string syntax R\"(...)\".",
                                suggestion="Add a closing quote '\"' to terminate the string.",
                                suggested_fix=f'{str_val}"',
                                rule_reference="ISO C++ §5.13.5: String Literals",
                            )
                        )
                    tokens.append(TokenItem(token_id, "STRING_LITERAL", str_val, line_num, start_col))
                    token_id += 1
                    continue

                # Char literal
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
                                title="Unterminated Character Literal",
                                message="Missing closing single quote (') on character literal.",
                                explanation="Character literals in C++ must be terminated by a closing single quotation mark.",
                                suggestion="Add a closing single quote '\''.",
                                suggested_fix=f"{char_val}'",
                                rule_reference="ISO C++ §5.13.3: Character Literals",
                            )
                        )
                    tokens.append(TokenItem(token_id, "CHAR_LITERAL", char_val, line_num, start_col))
                    token_id += 1
                    continue

                # Identifiers & Keywords
                if char.isalpha() or char == "_":
                    id_match = re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*", line[i:])
                    if id_match:
                        lexeme = id_match.group(0)
                        token_type = "KEYWORD" if lexeme in CPP_KEYWORDS else "IDENTIFIER"
                        tokens.append(TokenItem(token_id, token_type, lexeme, line_num, col))
                        token_id += 1
                        i += len(lexeme)
                        col += len(lexeme)
                        continue

                # Numbers
                if char.isdigit():
                    num_match = re.match(r"^(0[xX][0-9a-fA-F]+|[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?[fFlLuU]*|[0-9]+[a-zA-Z0-9_.]*)", line[i:])
                    if num_match:
                        lexeme = num_match.group(0)
                        if re.search(r"[g-zG-Z_]", lexeme) and not re.match(r"^0[xX][0-9a-fA-F]+$", lexeme):
                            errors.append(
                                ErrorItem(
                                    phase=CompilerPhase.LEXICAL.value,
                                    line=line_num,
                                    column=col,
                                    length=len(lexeme),
                                    title="Invalid Numeric Literal",
                                    message=f"Invalid suffix or malformed number '{lexeme}'.",
                                    explanation="Numeric constants cannot have invalid suffixes. Identifiers cannot begin with digits.",
                                    suggestion="Check spelling or separate number from variable name.",
                                    rule_reference="ISO C++ §5.13: Lexical Literals",
                                )
                            )
                        tokens.append(TokenItem(token_id, "NUMBER", lexeme, line_num, col))
                        token_id += 1
                        i += len(lexeme)
                        col += len(lexeme)
                        continue

                # C++ Multi-character Operators
                three_char = [">>=", "<<="]
                if i + 2 < n and line[i:i+3] in three_char:
                    tokens.append(TokenItem(token_id, "OPERATOR", line[i:i+3], line_num, col))
                    token_id += 1
                    i += 3
                    col += 3
                    continue

                two_char = [
                    "::", "->", "++", "--", "<<", ">>", "<=", ">=", "==", "!=",
                    "&&", "||", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="
                ]
                if i + 1 < n and line[i:i+2] in two_char:
                    op_val = line[i:i+2]
                    tok_type = "SCOPE_RESOLUTION" if op_val == "::" else "OPERATOR"
                    tokens.append(TokenItem(token_id, tok_type, op_val, line_num, col))
                    token_id += 1
                    i += 2
                    col += 2
                    continue

                # Single-character Operators & Delimiters
                if char in "+-*/%=<>!&|^~.":
                    tokens.append(TokenItem(token_id, "OPERATOR", char, line_num, col))
                    token_id += 1
                    i += 1
                    col += 1
                    continue
                elif char in ";,{}[ ]():":
                    tokens.append(TokenItem(token_id, "DELIMITER", char, line_num, col))
                    token_id += 1
                    i += 1
                    col += 1
                    continue

                # Illegal Character
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.LEXICAL.value,
                        line=line_num,
                        column=col,
                        length=1,
                        title="Illegal Character",
                        message=f"Stray '{char}' in program.",
                        explanation=f"The character '{char}' is not recognized in the C++ lexical grammar.",
                        suggestion=f"Remove character '{char}'.",
                        suggested_fix="",
                        rule_reference="ISO C++ §5.2: Character Sets and Lexical Conventions",
                    )
                )
                i += 1
                col += 1

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
                            message=f"Extraneous closing '{tok.value}' without matching opening '{expected}'.",
                            explanation=f"The parser detected a closing '{tok.value}' that lacks a corresponding opening bracket.",
                            suggestion=f"Remove '{tok.value}' or add opening '{expected}'.",
                            rule_reference="ISO C++ §9: Statements Grammar",
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
                                message=f"Expected '{self._get_closing(open_char)}' to match '{open_char}' from line {open_line}, but found '{tok.value}'.",
                                explanation="All opening parentheses and braces must be closed by their matching pair in LIFO order.",
                                suggestion=f"Change '{tok.value}' to '{self._get_closing(open_char)}'.",
                                suggested_fix=self._get_closing(open_char),
                                rule_reference="ISO C++ §9: Statements Grammar",
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
                    message=f"Unclosed '{open_char}'; missing closing '{closing}'.",
                    explanation=f"An opening '{open_char}' was not matched with a closing '{closing}' before end-of-file.",
                    suggestion=f"Add '{closing}' at the end of the matching block.",
                    suggested_fix=closing,
                    rule_reference="ISO C++ §9: Statements Grammar",
                )
            )

        # 2. C++ Line-by-Line Grammar Checks
        in_class_def = False
        class_brace_depth = 0

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("#"):
                continue

            # Track class definitions
            if re.match(r"^class\s+[a-zA-Z_][a-zA-Z0-9_]*", stripped):
                in_class_def = True
                class_brace_depth += stripped.count("{") - stripped.count("}")
                if "{" in stripped and "}" in stripped and not stripped.endswith(";"):
                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SYNTAX.value,
                            line=line_idx,
                            column=len(line.rstrip()) + 1,
                            length=1,
                            title="Missing Semicolon After Class Definition",
                            message="Expected ';' after class definition.",
                            explanation="In C++, a class declaration must end with a semicolon ';' after its closing brace '}'.",
                            suggestion="Add ';' after the closing brace.",
                            suggested_fix=f"{line.rstrip()};",
                            rule_reference="ISO C++ §12: Class Declarations",
                        )
                    )
            elif in_class_def:
                class_brace_depth += stripped.count("{") - stripped.count("}")
                if class_brace_depth <= 0 and stripped.startswith("}"):
                    in_class_def = False
                    if not stripped.endswith(";"):
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.SYNTAX.value,
                                line=line_idx,
                                column=len(line.rstrip()) + 1,
                                length=1,
                                title="Missing Semicolon After Class Definition",
                                message="Expected ';' after class definition.",
                                explanation="In C++, a class declaration must end with a semicolon ';' after its closing brace '}'.",
                                suggestion="Add ';' after the closing brace.",
                                suggested_fix=f"{line.rstrip()};",
                                rule_reference="ISO C++ §12: Class Declarations",
                            )
                        )

            # Stream operator mismatch: `cout >> ...` or `cin << ...`
            if re.search(r"\bcout\s*>>", stripped):
                match = re.search(r"\bcout\s*>>", stripped)
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=match.start() + 1,
                        length=match.end() - match.start(),
                        title="Invalid Stream Operator with 'cout'",
                        message="Invalid operator '>>' with 'cout'. Use insertion operator '<<'.",
                        explanation="'std::cout' is an output stream and uses the insertion operator '<<'. The extraction operator '>>' is used with input streams like 'std::cin'.",
                        suggestion="Change 'cout >>' to 'cout <<'.",
                        suggested_fix=stripped.replace("cout >>", "cout <<"),
                        rule_reference="ISO C++ §30.7.5: Output Streams (ostream)",
                    )
                )

            if re.search(r"\bcin\s*<<", stripped):
                match = re.search(r"\bcin\s*<<", stripped)
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=match.start() + 1,
                        length=match.end() - match.start(),
                        title="Invalid Stream Operator with 'cin'",
                        message="Invalid operator '<<' with 'cin'. Use extraction operator '>>'.",
                        explanation="'std::cin' is an input stream and uses the extraction operator '>>'. The insertion operator '<<' is used with 'cout'.",
                        suggestion="Change 'cin <<' to 'cin >>'.",
                        suggested_fix=stripped.replace("cin <<", "cin >>"),
                        rule_reference="ISO C++ §30.7.4: Input Streams (istream)",
                    )
                )

            # Missing Semicolons
            needs_semi = False
            is_control = bool(
                re.match(r"^(if|while|for|else\s+if|switch)\s*\(.*\)$", stripped)
                or stripped in ("else", "public:", "private:", "protected:", "default:")
                or stripped.endswith("{")
                or stripped.endswith("}")
                or stripped.endswith(":")
                or stripped.endswith(";")
                or stripped.endswith(",")
            )

            is_func_header = bool(
                re.match(r"^(int|float|double|char|void|bool|auto|string|long)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\)$", stripped)
            )

            if not is_control and not is_func_header:
                if (
                    re.match(r"^(return\b|break\b|continue\b|using\s+namespace\b)", stripped)
                    or re.match(r"^(int|float|double|char|void|bool|auto|string)(\s*\*|\s+)[a-zA-Z_]", stripped)
                    or re.search(r"\b(cout|cin)\b.*[^\;]$", stripped)
                    or re.search(r"=\s*[^;]+$", stripped)
                ):
                    needs_semi = True

            if needs_semi and not stripped.endswith(";"):
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=len(line.rstrip()) + 1,
                        length=1,
                        title="Missing Semicolon ';'",
                        message="Expected ';' at the end of statement.",
                        explanation="C++ statements, declarations, and 'using namespace' directives must end with a semicolon.",
                        suggestion=f"Append ';' to line {line_idx}.",
                        suggested_fix=f"{line.rstrip()};",
                        rule_reference="ISO C++ §9.2: Expression Statement",
                    )
                )

        return None, errors

    # =========================================================================
    # PHASE 3: SEMANTIC ANALYSIS
    # =========================================================================
    def semantic_analysis(
        self, ast_or_cst: Any, tokens: List[TokenItem], source_code: str
    ) -> Tuple[List[SymbolItem], List[ErrorItem]]:
        errors: List[ErrorItem] = []
        symbol_table: List[SymbolItem] = []
        scope_symbols: Dict[str, Dict[str, SymbolItem]] = {"global": {}}
        current_scope = "global"
        has_namespace_std = False
        current_func_type: Optional[str] = None
        current_func_has_return = False
        user_types = set(BASE_CPP_TYPES)

        std_identifiers = {
            "cout", "cin", "endl", "string", "vector", "map", "set",
            "pair", "make_pair", "min", "max", "sort", "reverse",
            "iostream", "fstream", "sstream", "printf"
        }

        # Check if `using namespace std;` exists
        if re.search(r"\busing\s+namespace\s+std\s*;", source_code):
            has_namespace_std = True

        # Pre-pass: Discover all class declarations
        for idx, tok in enumerate(tokens):
            if tok.type == "KEYWORD" and tok.value == "class" and idx + 1 < len(tokens):
                cls_tok = tokens[idx + 1]
                if cls_tok.type == "IDENTIFIER":
                    user_types.add(cls_tok.value)
                    sym = SymbolItem(cls_tok.value, "class", "global", cls_tok.line, True)
                    symbol_table.append(sym)
                    scope_symbols["global"][cls_tok.value] = sym

        i = 0
        n = len(tokens)

        while i < n:
            tok = tokens[i]

            # Skip preprocessor
            if tok.type == "PREPROCESSOR":
                i += 1
                continue

            # Skip 'using namespace std;'
            if tok.type == "KEYWORD" and tok.value == "using":
                while i < n and tokens[i].value != ";":
                    i += 1
                i += 1
                continue

            # Class header: class Name { ... };
            if tok.type == "KEYWORD" and tok.value == "class" and i + 1 < n:
                cls_name = tokens[i + 1].value
                current_scope = cls_name
                if current_scope not in scope_symbols:
                    scope_symbols[current_scope] = {}
                i += 2
                continue

            # Function header
            if (
                tok.type == "KEYWORD"
                and tok.value in user_types
                and i + 2 < n
                and tokens[i + 1].type == "IDENTIFIER"
                and tokens[i + 2].value == "("
            ):
                func_ret_type = tok.value
                func_name = tokens[i + 1].value
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

                # Advance past parameters
                i += 3
                while i < n and tokens[i].value != ")":
                    if tokens[i].type == "KEYWORD" and tokens[i].value in user_types:
                        p_type = tokens[i].value
                        if i + 1 < n and tokens[i + 1].type == "IDENTIFIER":
                            p_name = tokens[i + 1].value
                            p_sym = SymbolItem(p_name, p_type, current_scope, tokens[i + 1].line, True)
                            symbol_table.append(p_sym)
                            scope_symbols[current_scope][p_name] = p_sym
                            i += 1
                    i += 1
                i += 1
                continue

            # Scope exit
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
                                message=f"Non-void function '{current_scope}' reaches end of body without return statement.",
                                explanation=f"Control reaches end of non-void function returning '{current_func_type}'.",
                                suggestion=f"Add 'return <value>;' before closing brace.",
                                suggested_fix="return 0;",
                                rule_reference="ISO C++ §9.6.3: Return Statement",
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
                                explanation="In C++, void functions cannot return an expression.",
                                suggestion="Use bare 'return;' without an expression.",
                                suggested_fix="return;",
                                rule_reference="ISO C++ §9.6.3: Return Statement",
                            )
                        )
                i += 1
                continue

            # Variable Declarations: type [*] var1 [= expr1], var2 [= expr2];
            # Also handle std::string or user classes
            is_type_decl = (
                (tok.type == "KEYWORD" and tok.value in user_types)
                or (tok.type == "IDENTIFIER" and tok.value in user_types)
                or (tok.type == "IDENTIFIER" and tok.value == "std" and i + 2 < n and tokens[i+1].value == "::" and tokens[i+2].value in ("string", "vector"))
            )

            if is_type_decl:
                decl_type = tok.value
                if tok.value == "std":
                    decl_type = f"std::{tokens[i+2].value}"
                    i += 2

                j = i + 1
                while j < n and tokens[j].value != ";":
                    effective_type = decl_type
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
                                    message=f"Redefinition of '{var_name}' in scope '{current_scope}'.",
                                    explanation=f"Identifier '{var_name}' has already been defined in this scope.",
                                    suggestion=f"Rename '{var_name}' or remove duplicate declaration.",
                                    rule_reference="ISO C++ §6.3: Scope of Declarations",
                                )
                            )
                        else:
                            is_init = False
                            sym = SymbolItem(var_name, effective_type, current_scope, var_line, False)
                            symbol_table.append(sym)
                            if current_scope not in scope_symbols:
                                scope_symbols[current_scope] = {}
                            scope_symbols[current_scope][var_name] = sym

                        j += 1

                        # Check initialization '='
                        if j < n and tokens[j].value == "=":
                            if var_name in scope_symbols.get(current_scope, {}):
                                scope_symbols[current_scope][var_name].initialized = True
                            j += 1

                            bracket_depth = 0
                            while j < n and (tokens[j].value != ";" and (tokens[j].value != "," or bracket_depth > 0)):
                                expr_tok = tokens[j]
                                if expr_tok.value in "([{":
                                    bracket_depth += 1
                                elif expr_tok.value in ")]}":
                                    bracket_depth = max(0, bracket_depth - 1)

                                # Type mismatch: string to int/bool
                                if effective_type in ("int", "double", "float", "bool", "short", "long") and expr_tok.type == "STRING_LITERAL":
                                    errors.append(
                                        ErrorItem(
                                            phase=CompilerPhase.SEMANTIC.value,
                                            line=expr_tok.line,
                                            column=expr_tok.column,
                                            length=len(expr_tok.value),
                                            title="Incompatible Type Assignment",
                                            message=f"Cannot initialize variable of type '{effective_type}' with an rvalue of type 'const char*'.",
                                            explanation=f"C++ enforces strong static typing. Assigning string literal {expr_tok.value} to '{effective_type}' is invalid.",
                                            suggestion=f"Assign an appropriate {effective_type} value, or change type to 'std::string'.",
                                            suggested_fix=f"std::string {var_name} = {expr_tok.value};",
                                            rule_reference="ISO C++ §11.6: Initializers",
                                        )
                                    )

                                # Division by zero
                                if expr_tok.type == "OPERATOR" and expr_tok.value in ("/", "%"):
                                    if j + 1 < n and tokens[j + 1].type == "NUMBER" and tokens[j + 1].value in ("0", "0.0"):
                                        errors.append(
                                            ErrorItem(
                                                phase=CompilerPhase.SEMANTIC.value,
                                                line=tokens[j + 1].line,
                                                column=tokens[j + 1].column,
                                                length=len(tokens[j + 1].value),
                                                title="Division by Zero",
                                                message=f"Division or modulo by zero constant '{expr_tok.value} 0'.",
                                                explanation="Evaluating division by zero constant produces undefined behavior in C++.",
                                                suggestion="Ensure denominator is non-zero.",
                                                rule_reference="ISO C++ §8.6: Multiplicative Operators",
                                            )
                                        )

                                # Check identifiers in RHS expression
                                if expr_tok.type == "IDENTIFIER":
                                    id_v = expr_tok.value
                                    is_prefixed_std = (j >= 2 and tokens[j-1].value == "::" and tokens[j-2].value == "std")
                                    in_loc = id_v in scope_symbols.get(current_scope, {})
                                    in_glob = id_v in scope_symbols.get("global", {})
                                    is_std = id_v in std_identifiers and (has_namespace_std or is_prefixed_std)
                                    is_member = (j > 0 and tokens[j-1].value in (".", "->", "::"))
                                    if not (in_loc or in_glob or is_std or is_member or id_v == current_scope):
                                        all_syms = list(scope_symbols.get(current_scope, {}).keys()) + list(scope_symbols.get("global", {}).keys())
                                        match = self.find_best_match(id_v, all_syms)
                                        sugg = f"Did you mean '{match}'?" if match else f"Declare '{id_v}' before use, e.g. 'int {id_v};'."
                                        errors.append(
                                            ErrorItem(
                                                phase=CompilerPhase.SEMANTIC.value,
                                                line=expr_tok.line,
                                                column=expr_tok.column,
                                                length=len(id_v),
                                                title="Undeclared Identifier",
                                                message=f"Use of undeclared identifier '{id_v}'.",
                                                explanation=f"Variable or symbol '{id_v}' has not been declared in scope '{current_scope}'.",
                                                suggestion=sugg,
                                                suggested_fix=f"{match}" if match else f"int {id_v};",
                                                rule_reference="ISO C++ §6.4: Name Lookup",
                                            )
                                        )

                                j += 1

                        if j < n and tokens[j].value == ",":
                            j += 1
                    else:
                        j += 1

                i = j
                continue

            # Standard library resolution check: cout, cin, endl without std::
            if tok.type == "IDENTIFIER" and tok.value in ("cout", "cin", "endl"):
                is_prefixed_std = (i >= 2 and tokens[i-1].value == "::" and tokens[i-2].value == "std")
                if not is_prefixed_std and not has_namespace_std:
                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=tok.line,
                            column=tok.column,
                            length=len(tok.value),
                            title="Unqualified Standard Identifier",
                            message=f"'{tok.value}' was not declared in this scope (did you forget 'using namespace std;' or 'std::{tok.value}'?).",
                            explanation=f"In C++, standard library members reside in the 'std' namespace. They must be referenced as 'std::{tok.value}' or unlocked with 'using namespace std;'.",
                            suggestion=f"Use 'std::{tok.value}' or add 'using namespace std;' at the top of the file.",
                            suggested_fix=f"std::{tok.value}",
                            rule_reference="ISO C++ §10.3: Namespaces",
                        )
                    )

            # Undeclared Identifiers in general expressions
            elif tok.type == "IDENTIFIER":
                ident_name = tok.value
                is_member = (i > 0 and tokens[i-1].value in (".", "->", "::"))
                is_namespace_prefix = (i + 1 < n and tokens[i+1].value == "::")
                in_local = ident_name in scope_symbols.get(current_scope, {})
                in_global = ident_name in scope_symbols.get("global", {})
                is_std = ident_name in std_identifiers and has_namespace_std

                if not (in_local or in_global or is_std or is_member or is_namespace_prefix or ident_name == current_scope):
                    all_syms = list(scope_symbols.get(current_scope, {}).keys()) + list(scope_symbols.get("global", {}).keys())
                    best_match = self.find_best_match(ident_name, all_syms)
                    suggestion = f"Did you mean '{best_match}'?" if best_match else f"Declare '{ident_name}' before using it, e.g. 'int {ident_name};'."

                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=tok.line,
                            column=tok.column,
                            length=len(ident_name),
                            title="Undeclared Identifier",
                            message=f"Use of undeclared identifier '{ident_name}'.",
                            explanation=f"Variable or symbol '{ident_name}' has not been declared in scope '{current_scope}'.",
                            suggestion=suggestion,
                            suggested_fix=f"{best_match}" if best_match else f"int {ident_name};",
                            rule_reference="ISO C++ §6.4: Name Lookup",
                        )
                    )

            # Standalone Division by zero
            if tok.type == "OPERATOR" and tok.value in ("/", "%"):
                if i + 1 < n and tokens[i + 1].type == "NUMBER" and tokens[i + 1].value in ("0", "0.0"):
                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=tokens[i + 1].line,
                            column=tokens[i + 1].column,
                            length=len(tokens[i + 1].value),
                            title="Division by Zero",
                            message=f"Division or modulo by zero constant '{tok.value} 0'.",
                            explanation="Evaluating division by zero constant produces undefined behavior in C++.",
                            suggestion="Ensure denominator is non-zero.",
                            rule_reference="ISO C++ §8.6: Multiplicative Operators",
                        )
                    )

            i += 1

        return symbol_table, errors

    @staticmethod
    def _get_closing(open_bracket: str) -> str:
        pairs = {"(": ")", "{": "}", "[": "]"}
        return pairs.get(open_bracket, ")")
