"""
Java Language Lexical, Syntax, and Semantic Analyzer.
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


JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "true", "false", "null",
    "record", "sealed", "permits", "yield", "var"
}

BASE_JAVA_TYPES = {
    "int", "double", "float", "long", "short", "byte", "char", "boolean",
    "String", "void", "Object", "Integer", "Double", "Boolean", "var"
}


class JavaCompilerAnalyzer(BaseCompilerAnalyzer):
    """
    Academic compiler error detective for Java programs.
    Demonstrates Java OOP structure, static typing, and JVM-style compilation phases.
    """

    def __init__(self):
        super().__init__("Java")

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

                # Annotation: @Override, @Deprecated
                if char == "@":
                    ann_match = re.match(r"^@[a-zA-Z_][a-zA-Z0-9_]*", line[i:])
                    if ann_match:
                        lexeme = ann_match.group(0)
                        tokens.append(TokenItem(token_id, "ANNOTATION", lexeme, line_num, col))
                        token_id += 1
                        i += len(lexeme)
                        col += len(lexeme)
                        continue
                    else:
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.LEXICAL.value,
                                line=line_num,
                                column=col,
                                length=1,
                                title="Illegal Character '@'",
                                message="Illegal character '@' not forming a valid annotation.",
                                explanation="In Java, '@' is reserved for annotations followed by an identifier (e.g. '@Override').",
                                suggestion="Remove '@' or specify valid annotation name.",
                                rule_reference="JLS §3.8: Identifiers and Annotations",
                            )
                        )
                        i += 1
                        col += 1
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
                                title="Unclosed String Literal",
                                message="Unclosed string literal in Java.",
                                explanation="In Java, standard string literals cannot contain unescaped newline characters and must be closed with '\"'.",
                                suggestion="Add closing double quote '\"'.",
                                suggested_fix=f'{str_val}"',
                                rule_reference="JLS §3.10.5: String Literals",
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
                                title="Unclosed Character Literal",
                                message="Unclosed character literal in Java.",
                                explanation="Character literals must be enclosed in single quotes.",
                                suggestion="Add a closing single quote '\''.",
                                suggested_fix=f"{char_val}'",
                                rule_reference="JLS §3.10.4: Character Literals",
                            )
                        )
                    elif len(char_val) > 4 or (len(char_val) == 4 and not char_val.startswith("'\\")):
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.LEXICAL.value,
                                line=line_num,
                                column=start_col,
                                length=len(char_val),
                                title="Invalid Character Constant",
                                message=f"Too many characters in character literal {char_val}.",
                                explanation="In Java, a char literal represents exactly one UTF-16 code point. For strings, use double quotes.",
                                suggestion=f'Change to double quotes: "{char_val[1:-1]}"',
                                suggested_fix=f'"{char_val[1:-1]}"',
                                rule_reference="JLS §3.10.4: Character Literals",
                            )
                        )
                    tokens.append(TokenItem(token_id, "CHAR_LITERAL", char_val, line_num, start_col))
                    token_id += 1
                    continue

                # Identifiers or Keywords
                if char.isalpha() or char in "_$":
                    id_match = re.match(r"^[a-zA-Z_$][a-zA-Z0-9_$]*", line[i:])
                    if id_match:
                        lexeme = id_match.group(0)
                        token_type = "KEYWORD" if lexeme in JAVA_KEYWORDS else "IDENTIFIER"
                        tokens.append(TokenItem(token_id, token_type, lexeme, line_num, col))
                        token_id += 1
                        i += len(lexeme)
                        col += len(lexeme)
                        continue

                # Numbers
                if char.isdigit():
                    num_match = re.match(r"^(0[xX][0-9a-fA-F]+|[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?[fFdDlL]*|[0-9]+[a-zA-Z0-9_.]*)", line[i:])
                    if num_match:
                        lexeme = num_match.group(0)
                        if re.search(r"[g-zG-Z_]", lexeme) and not re.match(r"^0[xX][0-9a-fA-F]+$", lexeme):
                            errors.append(
                                ErrorItem(
                                    phase=CompilerPhase.LEXICAL.value,
                                    line=line_num,
                                    column=col,
                                    length=len(lexeme),
                                    title="Invalid Number Format",
                                    message=f"Malformed number literal or illegal identifier '{lexeme}'.",
                                    explanation="Java does not allow invalid suffix characters on numeric literals.",
                                    suggestion="Correct the number format or rename identifier.",
                                    rule_reference="JLS §3.10.1: Integer Literals",
                                )
                            )
                        tokens.append(TokenItem(token_id, "NUMBER", lexeme, line_num, col))
                        token_id += 1
                        i += len(lexeme)
                        col += len(lexeme)
                        continue

                # Operators & Delimiters
                two_char = ["==", "!=", "<=", ">=", "&&", "||", "++", "--", "+=", "-=", "*=", "/=", "%=", "->", "::"]
                if i + 1 < n and line[i:i+2] in two_char:
                    tokens.append(TokenItem(token_id, "OPERATOR", line[i:i+2], line_num, col))
                    token_id += 1
                    i += 2
                    col += 2
                    continue

                if char in "+-*/%=<>!&|^~":
                    tokens.append(TokenItem(token_id, "OPERATOR", char, line_num, col))
                    token_id += 1
                    i += 1
                    col += 1
                    continue
                elif char in ";,{}[ ]():.":
                    tokens.append(TokenItem(token_id, "DELIMITER", char, line_num, col))
                    token_id += 1
                    i += 1
                    col += 1
                    continue

                # Stray illegal character
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.LEXICAL.value,
                        line=line_num,
                        column=col,
                        length=1,
                        title="Illegal Character",
                        message=f"Illegal character '{char}' found in Java source.",
                        explanation=f"The symbol '{char}' is not a valid Java lexical token.",
                        suggestion=f"Remove '{char}'.",
                        suggested_fix="",
                        rule_reference="JLS §3.1: Unicode and Lexical Translations",
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
                            explanation=f"The parser detected a closing '{tok.value}' that lacks an opening bracket.",
                            suggestion=f"Remove '{tok.value}'.",
                            rule_reference="JLS §14: Blocks and Statements",
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
                                explanation="Parentheses and braces must be closed in symmetrical LIFO order.",
                                suggestion=f"Change '{tok.value}' to '{self._get_closing(open_char)}'.",
                                suggested_fix=self._get_closing(open_char),
                                rule_reference="JLS §14: Blocks and Statements",
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
                    explanation=f"Opening '{open_char}' at line {open_line} is missing its matching '{closing}'.",
                    suggestion=f"Add '{closing}' at the end of the corresponding block.",
                    suggested_fix=closing,
                    rule_reference="JLS §14: Blocks and Statements",
                )
            )

        # 2. Check Class Structure: Java code must have at least one class
        has_class_decl = any(tok.type == "KEYWORD" and tok.value == "class" for tok in tokens)
        if not has_class_decl and len(tokens) > 0:
            errors.append(
                ErrorItem(
                    phase=CompilerPhase.SYNTAX.value,
                    line=1,
                    column=1,
                    length=4,
                    title="Missing Class Declaration",
                    message="Class, interface, enum, or record expected.",
                    explanation="In Java, all executable statements and methods must reside inside a class declaration.",
                    suggestion="Wrap your code in a class, e.g.: `public class Main { ... }`.",
                    suggested_fix="public class Main {\n    // Code here\n}",
                    rule_reference="JLS §7.6: Top Level Type Declarations",
                )
            )

        # 3. Line-by-Line Grammar Checks
        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("@"):
                continue

            # Typo in System.out.println
            if "System.out.printLn" in stripped:
                idx = stripped.find("System.out.printLn")
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=idx + 1,
                        length=18,
                        title="Typo in 'System.out.println'",
                        message="Cannot find symbol 'printLn' on 'java.io.PrintStream'.",
                        explanation="Java method names are case-sensitive. The standard method is 'println' with a lowercase 'l', not 'printLn'.",
                        suggestion="Change 'printLn' to 'println'.",
                        suggested_fix=stripped.replace("printLn", "println"),
                        rule_reference="Java Standard Library: PrintStream",
                    )
                )

            # Malformed main method
            if re.search(r"public\s+void\s+main\s*\(", stripped) and "static" not in stripped:
                errors.append(
                    ErrorItem(
                        phase=CompilerPhase.SYNTAX.value,
                        line=line_idx,
                        column=stripped.find("main") + 1,
                        length=4,
                        title="Malformed 'main' Method Signature",
                        message="The main method is not declared 'static'.",
                        explanation="In Java, the application entry point must be declared as 'public static void main(String[] args)'. Missing 'static' prevents the JVM from launching the program.",
                        suggestion="Add the 'static' keyword: 'public static void main(String[] args)'.",
                        suggested_fix=stripped.replace("public void main", "public static void main"),
                        rule_reference="JLS §12.1.4: Invoke main Method",
                    )
                )

            # Missing Semicolon Check
            needs_semi = False
            is_control = bool(
                re.match(r"^(if|while|for|switch)\s*\(.*\)$", stripped)
                or stripped in ("else", "try", "finally", "static")
                or stripped.endswith("{")
                or stripped.endswith("}")
                or stripped.endswith(";")
                or stripped.endswith(":")
                or stripped.endswith(",")
            )

            is_class_or_method_header = bool(
                re.search(r"\b(class|interface|enum)\s+[a-zA-Z_]", stripped)
                or re.search(r"\b(public|private|protected|static|final)\s+.*\)\s*$", stripped)
                or re.search(r"\b(void|int|double|float|String|boolean)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(.*\)$", stripped)
            )

            if not is_control and not is_class_or_method_header:
                if (
                    re.match(r"^(return\b|break\b|continue\b|throw\b|import\b|package\b)", stripped)
                    or re.match(r"^(int|double|float|long|short|byte|char|boolean|String|var)(\s*\[\s*\]|\s+)[a-zA-Z_]", stripped)
                    or re.search(r"\bSystem\.out\.print(ln)?\s*\(.*\)$", stripped)
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
                        message="';' expected at end of statement.",
                        explanation="In Java, declarations, expressions, return statements, and import statements must terminate with ';'.",
                        suggestion=f"Append ';' to the end of line {line_idx}.",
                        suggested_fix=f"{line.rstrip()};",
                        rule_reference="JLS §14.5: Statements Grammar",
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
        current_method_type: Optional[str] = None
        current_method_has_return = False
        user_types = set(BASE_JAVA_TYPES)

        known_java_classes = {
            "System", "String", "Math", "Integer", "Double", "Boolean",
            "Scanner", "ArrayList", "List", "Arrays", "Collections", "Exception",
            "out", "in", "err"
        }

        # Pre-pass: Discover all declared classes
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

            # Class header
            if tok.type == "KEYWORD" and tok.value == "class" and i + 1 < n:
                class_name = tokens[i + 1].value
                current_scope = class_name
                if current_scope not in scope_symbols:
                    scope_symbols[current_scope] = {}
                i += 2
                continue

            # Method headers: e.g. void main( ... ) or int calculate( ... )
            if (
                tok.type == "KEYWORD"
                and tok.value in user_types
                and i + 2 < n
                and tokens[i + 1].type == "IDENTIFIER"
                and tokens[i + 2].value == "("
            ):
                m_ret = tok.value
                m_name = tokens[i + 1].value
                method_scope = f"{current_scope}::{m_name}"
                current_scope = method_scope
                current_method_type = m_ret
                current_method_has_return = False
                if current_scope not in scope_symbols:
                    scope_symbols[current_scope] = {}

                m_sym = SymbolItem(m_name, f"method()->{m_ret}", "class", tok.line, True)
                symbol_table.append(m_sym)

                # Skip params
                i += 3
                while i < n and tokens[i].value != ")":
                    if (tokens[i].type == "KEYWORD" and tokens[i].value in user_types) or (tokens[i].type == "IDENTIFIER" and tokens[i].value in user_types):
                        p_t = tokens[i].value
                        pj = i + 1
                        # Handle array String[] args
                        if pj + 1 < n and tokens[pj].value == "[" and tokens[pj+1].value == "]":
                            p_t += "[]"
                            pj += 2
                        if pj < n and tokens[pj].type == "IDENTIFIER":
                            p_n = tokens[pj].value
                            p_sym = SymbolItem(p_n, p_t, current_scope, tokens[pj].line, True)
                            symbol_table.append(p_sym)
                            scope_symbols[current_scope][p_n] = p_sym
                            i = pj
                    i += 1
                i += 1
                continue

            # Return statement
            if tok.type == "KEYWORD" and tok.value == "return":
                current_method_has_return = True
                if current_method_type == "void":
                    if i + 1 < n and tokens[i + 1].value != ";":
                        errors.append(
                            ErrorItem(
                                phase=CompilerPhase.SEMANTIC.value,
                                line=tok.line,
                                column=tok.column,
                                length=6,
                                title="Incompatible Return Type",
                                message="Cannot return a value from a method with void result type.",
                                explanation="In Java, methods with return type 'void' cannot return an expression.",
                                suggestion="Use 'return;' without an expression, or update method return type.",
                                suggested_fix="return;",
                                rule_reference="JLS §14.17: The return Statement",
                            )
                        )
                i += 1
                continue

            # Scope exit
            if tok.value == "}" and "::" in current_scope:
                if current_method_type and current_method_type != "void" and not current_method_has_return:
                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=tok.line,
                            column=tok.column,
                            length=1,
                            title="Missing Return Statement",
                            message=f"Missing return statement in method with return type '{current_method_type}'.",
                            explanation=f"Non-void method must return a result of type {current_method_type}.",
                            suggestion=f"Add 'return <{current_method_type}>;' before method close.",
                            suggested_fix="return 0;",
                            rule_reference="JLS §8.4.7: Method Body",
                        )
                    )
                current_scope = current_scope.split("::")[0]
                current_method_type = None
                i += 1
                continue

            # Variable Declarations: type var1 [= expr1], var2 [= expr2];
            is_type_decl = (
                (tok.type == "KEYWORD" and tok.value in user_types)
                or (tok.type == "IDENTIFIER" and tok.value in user_types)
            )

            if is_type_decl:
                v_type = tok.value
                j = i + 1

                while j < n and tokens[j].value != ";":
                    effective_type = v_type
                    # Handle array brackets e.g. int[] or String[]
                    if j + 1 < n and tokens[j].value == "[" and tokens[j+1].value == "]":
                        effective_type += "[]"
                        j += 2

                    if j < n and tokens[j].type == "IDENTIFIER":
                        v_name = tokens[j].value
                        v_line = tokens[j].line
                        v_col = tokens[j].column

                        active_scope = scope_symbols.get(current_scope, {})
                        if v_name in active_scope:
                            errors.append(
                                ErrorItem(
                                    phase=CompilerPhase.SEMANTIC.value,
                                    line=v_line,
                                    column=v_col,
                                    length=len(v_name),
                                    title="Variable Redeclaration",
                                    message=f"Variable '{v_name}' is already defined in scope.",
                                    explanation=f"Java does not allow multiple declarations of '{v_name}' in the same scope.",
                                    suggestion=f"Rename '{v_name}' or remove second declaration.",
                                    rule_reference="JLS §6.4: Shadowing and Obscuring",
                                )
                            )
                        else:
                            is_init = False
                            sym = SymbolItem(v_name, effective_type, current_scope, v_line, False)
                            symbol_table.append(sym)
                            if current_scope not in scope_symbols:
                                scope_symbols[current_scope] = {}
                            scope_symbols[current_scope][v_name] = sym

                        j += 1

                        # Check if initialized with '='
                        if j < n and tokens[j].value == "=":
                            if v_name in scope_symbols.get(current_scope, {}):
                                scope_symbols[current_scope][v_name].initialized = True
                            j += 1

                            bracket_depth = 0
                            while j < n and (tokens[j].value != ";" and (tokens[j].value != "," or bracket_depth > 0)):
                                expr_tok = tokens[j]
                                if expr_tok.value in "([{":
                                    bracket_depth += 1
                                elif expr_tok.value in ")]}":
                                    bracket_depth = max(0, bracket_depth - 1)

                                # Type Compatibility Checks
                                if effective_type in ("int", "double", "float", "long", "short", "byte") and expr_tok.type == "STRING_LITERAL":
                                    errors.append(
                                        ErrorItem(
                                            phase=CompilerPhase.SEMANTIC.value,
                                            line=expr_tok.line,
                                            column=expr_tok.column,
                                            length=len(expr_tok.value),
                                            title="Incompatible Types",
                                            message=f"Incompatible types: java.lang.String cannot be converted to {effective_type}.",
                                            explanation=f"Java does not perform automatic coercion from String to {effective_type}.",
                                            suggestion=f"Change variable type to String or assign a valid numeric literal.",
                                            suggested_fix=f"String {v_name} = {expr_tok.value};",
                                            rule_reference="JLS §5.2: Assignment Contexts",
                                        )
                                    )
                                elif effective_type == "boolean" and expr_tok.type == "NUMBER":
                                    errors.append(
                                        ErrorItem(
                                            phase=CompilerPhase.SEMANTIC.value,
                                            line=expr_tok.line,
                                            column=expr_tok.column,
                                            length=len(expr_tok.value),
                                            title="Incompatible Types",
                                            message="Incompatible types: int cannot be converted to boolean.",
                                            explanation="In Java, boolean is not numeric; 0 and 1 cannot be converted to boolean (use 'true' or 'false').",
                                            suggestion="Use boolean literal 'true' or 'false'.",
                                            suggested_fix=f"boolean {v_name} = true;",
                                            rule_reference="JLS §5.1.8: Unboxing Conversion / Types",
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
                                                title="Division by Zero (/ by zero)",
                                                message="Division or modulo by zero constant causes ArithmeticException: / by zero.",
                                                explanation="Integer division or modulo by constant zero is guaranteed to throw ArithmeticException at runtime.",
                                                suggestion="Ensure denominator evaluates to a non-zero value.",
                                                rule_reference="JLS §15.17.2: Division Operator /",
                                            )
                                        )

                                # Check identifiers inside RHS expression
                                if expr_tok.type == "IDENTIFIER":
                                    id_val = expr_tok.value
                                    is_member = (j > 0 and tokens[j-1].value == ".")
                                    is_builtin = id_val in known_java_classes or id_val in ("args", "main")
                                    in_local = id_val in scope_symbols.get(current_scope, {})
                                    in_class = id_val in scope_symbols.get(current_scope.split("::")[0], {})
                                    in_global = id_val in scope_symbols.get("global", {})
                                    if not (is_member or is_builtin or in_local or in_class or in_global or id_val == current_scope):
                                        all_ids = list(scope_symbols.get(current_scope, {}).keys()) + list(known_java_classes)
                                        match = self.find_best_match(id_val, all_ids)
                                        sugg = f"Did you mean '{match}'?" if match else f"Cannot find symbol '{id_val}'. Declare it before using."
                                        errors.append(
                                            ErrorItem(
                                                phase=CompilerPhase.SEMANTIC.value,
                                                line=expr_tok.line,
                                                column=expr_tok.column,
                                                length=len(id_val),
                                                title="Cannot Find Symbol",
                                                message=f"Cannot find symbol '{id_val}'.",
                                                explanation=f"Variable or symbol '{id_val}' has not been declared in the current lexical environment.",
                                                suggestion=sugg,
                                                suggested_fix=f"{match}" if match else f"int {id_val};",
                                                rule_reference="JLS §6.5: Determining the Meaning of a Name",
                                            )
                                        )

                                j += 1

                        if j < n and tokens[j].value == ",":
                            j += 1
                    else:
                        j += 1

                i = j
                continue

            # General Undeclared Identifier Check
            if tok.type == "IDENTIFIER":
                id_val = tok.value
                is_member = (i > 0 and tokens[i-1].value == ".")
                is_builtin = id_val in known_java_classes or id_val in ("args", "main")
                in_local = id_val in scope_symbols.get(current_scope, {})
                in_class = id_val in scope_symbols.get(current_scope.split("::")[0], {})
                in_global = id_val in scope_symbols.get("global", {})

                if not (is_member or is_builtin or in_local or in_class or in_global or id_val == current_scope):
                    all_ids = list(scope_symbols.get(current_scope, {}).keys()) + list(known_java_classes)
                    match = self.find_best_match(id_val, all_ids)
                    sugg = f"Did you mean '{match}'?" if match else f"Cannot find symbol '{id_val}'. Declare it before using."

                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=tok.line,
                            column=tok.column,
                            length=len(id_val),
                            title="Cannot Find Symbol",
                            message=f"Cannot find symbol '{id_val}'.",
                            explanation=f"Variable or symbol '{id_val}' has not been declared in the current lexical environment.",
                            suggestion=sugg,
                            suggested_fix=f"{match}" if match else f"int {id_val};",
                            rule_reference="JLS §6.5: Determining the Meaning of a Name",
                        )
                    )

            # Division by Zero in standalone expressions
            if tok.type == "OPERATOR" and tok.value in ("/", "%"):
                if i + 1 < n and tokens[i + 1].type == "NUMBER" and tokens[i + 1].value in ("0", "0.0"):
                    errors.append(
                        ErrorItem(
                            phase=CompilerPhase.SEMANTIC.value,
                            line=tokens[i + 1].line,
                            column=tokens[i + 1].column,
                            length=len(tokens[i + 1].value),
                            title="Division by Zero (/ by zero)",
                            message="Division or modulo by zero constant causes ArithmeticException: / by zero.",
                            explanation="Integer division or modulo by constant zero is guaranteed to throw ArithmeticException at runtime and is flagged during semantic inspection.",
                            suggestion="Ensure denominator evaluates to a non-zero value.",
                            rule_reference="JLS §15.17.2: Division Operator /",
                        )
                    )

            i += 1

        return symbol_table, errors

    @staticmethod
    def _get_closing(open_bracket: str) -> str:
        pairs = {"(": ")", "{": "}", "[": "]"}
        return pairs.get(open_bracket, ")")
