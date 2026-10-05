"""
Base Abstract Compiler Analyzer for Smart Compiler Error Detective.
Provides common compiler analysis pipeline and helper methods.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import difflib
from .models import (
    CompilerPhase,
    Severity,
    ErrorItem,
    TokenItem,
    SymbolItem,
    AnalysisResult,
)


class BaseCompilerAnalyzer(ABC):
    """
    Modular compiler analyzer base class.
    Executes lexical, syntax, and semantic analysis in sequential phases.
    """

    def __init__(self, language_name: str):
        self.language_name = language_name

    def analyze(self, source_code: str) -> AnalysisResult:
        """
        Executes the three fundamental compiler phases:
        1. Lexical Analysis (Scanner -> Tokens)
        2. Syntax Analysis (Parser -> Grammar verification)
        3. Semantic Analysis (Type Checker / Scope / Symbol Table)
        """
        if not source_code.strip():
            return AnalysisResult(
                language=self.language_name,
                success=True,
                total_errors=0,
                lexical_errors_count=0,
                syntax_errors_count=0,
                semantic_errors_count=0,
                warnings_count=0,
                summary="Source code is empty. No compilation errors detected.",
            )

        # Phase 1: Lexical Analysis
        tokens, lexical_errors = self.lexical_analysis(source_code)

        # Phase 2: Syntax Analysis
        syntax_tree, syntax_errors = self.syntax_analysis(tokens, source_code)

        # Phase 3: Semantic Analysis
        symbol_table, semantic_errors = self.semantic_analysis(syntax_tree, tokens, source_code)

        # Combine all errors & warnings
        all_issues = lexical_errors + syntax_errors + semantic_errors

        # Deduplicate and sort by line and column
        seen_keys = set()
        unique_errors: List[ErrorItem] = []
        unique_warnings: List[ErrorItem] = []

        # Sort primarily by line, then column, then phase priority
        phase_priority = {
            CompilerPhase.LEXICAL.value: 1,
            CompilerPhase.SYNTAX.value: 2,
            CompilerPhase.SEMANTIC.value: 3,
        }

        all_issues.sort(
            key=lambda e: (
                e.line,
                e.column,
                phase_priority.get(e.phase, 99),
            )
        )

        for issue in all_issues:
            key = (issue.phase, issue.line, issue.column, issue.message)
            if key not in seen_keys:
                seen_keys.add(key)
                if issue.severity == Severity.WARNING.value:
                    unique_warnings.append(issue)
                else:
                    unique_errors.append(issue)

        total_err = len(unique_errors)
        lex_count = sum(1 for e in unique_errors if e.phase == CompilerPhase.LEXICAL.value)
        syn_count = sum(1 for e in unique_errors if e.phase == CompilerPhase.SYNTAX.value)
        sem_count = sum(1 for e in unique_errors if e.phase == CompilerPhase.SEMANTIC.value)
        warn_count = len(unique_warnings)

        if total_err == 0 and warn_count == 0:
            summary = f"Code parsed successfully! All lexical, syntax, and semantic checks passed with 0 errors."
        elif total_err == 0 and warn_count > 0:
            summary = f"Code parsed with 0 errors, but generated {warn_count} warning(s)."
        else:
            summary = (
                f"Found {total_err} error(s) ({lex_count} Lexical, "
                f"{syn_count} Syntax, {sem_count} Semantic) "
                f"and {warn_count} warning(s)."
            )

        return AnalysisResult(
            language=self.language_name,
            success=(total_err == 0),
            total_errors=total_err,
            lexical_errors_count=lex_count,
            syntax_errors_count=syn_count,
            semantic_errors_count=sem_count,
            warnings_count=warn_count,
            errors=unique_errors,
            warnings=unique_warnings,
            tokens=tokens,
            symbol_table=symbol_table,
            summary=summary,
        )

    @abstractmethod
    def lexical_analysis(self, source_code: str) -> Tuple[List[TokenItem], List[ErrorItem]]:
        """Scans characters into tokens and catches lexical errors."""
        pass

    @abstractmethod
    def syntax_analysis(
        self, tokens: List[TokenItem], source_code: str
    ) -> Tuple[Any, List[ErrorItem]]:
        """Parses tokens according to language grammar and catches syntax errors."""
        pass

    @abstractmethod
    def semantic_analysis(
        self, ast_or_cst: Any, tokens: List[TokenItem], source_code: str
    ) -> Tuple[List[SymbolItem], List[ErrorItem]]:
        """Performs scope, type, and identifier checks; constructs symbol table."""
        pass

    # Helper methods for all language analyzers
    @staticmethod
    def get_line_and_col(source: str, index: int) -> Tuple[int, int]:
        """Convert a 0-based character index into (line, col) both 1-based."""
        lines = source[:index].split("\n")
        line = len(lines)
        col = len(lines[-1]) + 1
        return line, col

    @staticmethod
    def find_best_match(target: str, candidates: List[str]) -> Optional[str]:
        """Finds closest matching identifier or keyword for typo suggestions."""
        matches = difflib.get_close_matches(target, candidates, n=1, cutoff=0.6)
        return matches[0] if matches else None
