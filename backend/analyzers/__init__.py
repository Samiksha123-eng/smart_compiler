"""
Analyzer package initialization and factory.
"""

from typing import Dict, Optional
from ..base_analyzer import BaseCompilerAnalyzer
from .c_analyzer import CCompilerAnalyzer
from .cpp_analyzer import CppCompilerAnalyzer
from .java_analyzer import JavaCompilerAnalyzer
from .python_analyzer import PythonCompilerAnalyzer


_ANALYZERS: Dict[str, BaseCompilerAnalyzer] = {
    "c": CCompilerAnalyzer(),
    "cpp": CppCompilerAnalyzer(),
    "c++": CppCompilerAnalyzer(),
    "java": JavaCompilerAnalyzer(),
    "python": PythonCompilerAnalyzer(),
    "py": PythonCompilerAnalyzer(),
}


def get_analyzer(language: str) -> Optional[BaseCompilerAnalyzer]:
    """Retrieve the appropriate compiler analyzer for the requested programming language."""
    key = language.strip().lower()
    return _ANALYZERS.get(key)


def get_supported_languages() -> list:
    """Return list of distinct supported programming languages."""
    return ["C", "C++", "Java", "Python"]
