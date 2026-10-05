"""
Models and Data Structures for Smart Compiler Error Detective.
Shared across all language analyzer modules.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
from datetime import datetime


class CompilerPhase(str, Enum):
    LEXICAL = "Lexical"
    SYNTAX = "Syntax"
    SEMANTIC = "Semantic"


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ErrorItem:
    phase: str                           # Lexical | Syntax | Semantic
    line: int                            # 1-indexed
    column: int                          # 1-indexed
    length: int                          # Character length of erroneous token
    title: str                           # Short error title
    message: str                         # Technical error message
    explanation: str                     # Simple English explanation
    suggestion: str                      # Recommended correction
    rule_reference: str                  # Compiler phase / standard rule reference
    severity: str = Severity.ERROR.value # error | warning | info
    suggested_fix: Optional[str] = None  # Corrected line or snippet
    id: str = field(default_factory=lambda: f"ERR_{uuid.uuid4().hex[:6]}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TokenItem:
    id: int
    type: str                            # KEYWORD, IDENTIFIER, OPERATOR, LITERAL, etc.
    value: str                           # The lexeme
    line: int
    column: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SymbolItem:
    name: str
    data_type: str
    scope: str
    line_declared: int
    initialized: bool = False
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    language: str
    success: bool
    total_errors: int
    lexical_errors_count: int
    syntax_errors_count: int
    semantic_errors_count: int
    warnings_count: int
    errors: List[ErrorItem] = field(default_factory=list)
    warnings: List[ErrorItem] = field(default_factory=list)
    tokens: List[TokenItem] = field(default_factory=list)
    symbol_table: List[SymbolItem] = field(default_factory=list)
    summary: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "success": self.success,
            "total_errors": self.total_errors,
            "lexical_errors_count": self.lexical_errors_count,
            "syntax_errors_count": self.syntax_errors_count,
            "semantic_errors_count": self.semantic_errors_count,
            "warnings_count": self.warnings_count,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "tokens": [t.to_dict() for t in self.tokens],
            "symbol_table": [s.to_dict() for s in self.symbol_table],
            "summary": self.summary,
            "timestamp": self.timestamp,
        }
