"""
Comprehensive unit tests for Smart Compiler Error Detective.
Validates Lexical, Syntax, and Semantic analysis across C, C++, Java, and Python.
"""

import unittest
from backend.analyzers import get_analyzer
from backend.sample_programs import SAMPLES
from backend.models import CompilerPhase


class TestCompilerAnalyzers(unittest.TestCase):

    # ==================== C TESTS ====================
    def test_c_buggy_detection(self):
        analyzer = get_analyzer("c")
        result = analyzer.analyze(SAMPLES["c"]["buggy"])
        self.assertFalse(result.success)
        self.assertGreater(result.total_errors, 0)
        self.assertGreater(result.lexical_errors_count, 0)
        self.assertGreater(result.syntax_errors_count, 0)
        self.assertGreater(result.semantic_errors_count, 0)
        self.assertGreater(len(result.tokens), 0)
        self.assertGreater(len(result.symbol_table), 0)

    def test_c_clean_program(self):
        analyzer = get_analyzer("c")
        result = analyzer.analyze(SAMPLES["c"]["clean"])
        self.assertTrue(result.success)
        self.assertEqual(result.total_errors, 0)

    def test_c_unclosed_string_lexical(self):
        code = 'int main() { char* s = "hello; return 0; }'
        result = get_analyzer("c").analyze(code)
        lex_errs = [e for e in result.errors if e.phase == CompilerPhase.LEXICAL.value]
        self.assertTrue(any("String" in e.title for e in lex_errs))

    def test_c_unmatched_brackets_syntax(self):
        code = 'int main() { if (1 { return 0; } }'
        result = get_analyzer("c").analyze(code)
        syn_errs = [e for e in result.errors if e.phase == CompilerPhase.SYNTAX.value]
        self.assertTrue(len(syn_errs) > 0)

    def test_c_typo_suggestion_semantic(self):
        code = 'int main() { int counter = 10; countr = 20; return 0; }'
        result = get_analyzer("c").analyze(code)
        sem_errs = [e for e in result.errors if e.phase == CompilerPhase.SEMANTIC.value]
        self.assertTrue(any("counter" in e.suggestion for e in sem_errs))

    # ==================== C++ TESTS ====================
    def test_cpp_buggy_detection(self):
        analyzer = get_analyzer("cpp")
        result = analyzer.analyze(SAMPLES["cpp"]["buggy"])
        self.assertFalse(result.success)
        self.assertGreater(result.syntax_errors_count, 0)
        self.assertGreater(result.semantic_errors_count, 0)

    def test_cpp_clean_program(self):
        analyzer = get_analyzer("cpp")
        result = analyzer.analyze(SAMPLES["cpp"]["clean"])
        self.assertTrue(result.success)
        self.assertEqual(result.total_errors, 0)

    def test_cpp_class_missing_semicolon(self):
        code = 'class Car { public: int speed; } int main() { return 0; }'
        result = get_analyzer("cpp").analyze(code)
        syn_errs = [e for e in result.errors if e.phase == CompilerPhase.SYNTAX.value]
        self.assertTrue(any("Class" in e.title for e in syn_errs))

    def test_cpp_stream_operator_syntax(self):
        code = '#include <iostream>\nusing namespace std;\nint main() { cout >> "hello"; return 0; }'
        result = get_analyzer("cpp").analyze(code)
        syn_errs = [e for e in result.errors if e.phase == CompilerPhase.SYNTAX.value]
        self.assertTrue(any("Stream Operator" in e.title for e in syn_errs))

    # ==================== JAVA TESTS ====================
    def test_java_buggy_detection(self):
        analyzer = get_analyzer("java")
        result = analyzer.analyze(SAMPLES["java"]["buggy"])
        self.assertFalse(result.success)
        self.assertGreater(result.lexical_errors_count, 0)
        self.assertGreater(result.syntax_errors_count, 0)
        self.assertGreater(result.semantic_errors_count, 0)

    def test_java_clean_program(self):
        analyzer = get_analyzer("java")
        result = analyzer.analyze(SAMPLES["java"]["clean"])
        self.assertTrue(result.success)
        self.assertEqual(result.total_errors, 0)

    def test_java_boolean_int_mismatch_semantic(self):
        code = 'public class Test { public static void main(String[] args) { boolean flag = 1; } }'
        result = get_analyzer("java").analyze(code)
        sem_errs = [e for e in result.errors if e.phase == CompilerPhase.SEMANTIC.value]
        self.assertTrue(any("Incompatible" in e.title for e in sem_errs))

    def test_java_missing_class_syntax(self):
        code = 'public static void main(String[] args) { int x = 5; }'
        result = get_analyzer("java").analyze(code)
        syn_errs = [e for e in result.errors if e.phase == CompilerPhase.SYNTAX.value]
        self.assertTrue(any("Class" in e.title for e in syn_errs))

    # ==================== PYTHON TESTS ====================
    def test_python_buggy_detection(self):
        analyzer = get_analyzer("python")
        result = analyzer.analyze(SAMPLES["python"]["buggy"])
        self.assertFalse(result.success)
        self.assertGreater(result.syntax_errors_count, 0)
        self.assertGreater(result.lexical_errors_count, 0)

    def test_python_clean_program(self):
        analyzer = get_analyzer("python")
        result = analyzer.analyze(SAMPLES["python"]["clean"])
        self.assertTrue(result.success)
        self.assertEqual(result.total_errors, 0)

    def test_python_missing_colon_syntax(self):
        code = 'def greet(name)\n    print("Hello", name)'
        result = get_analyzer("python").analyze(code)
        syn_errs = [e for e in result.errors if e.phase == CompilerPhase.SYNTAX.value]
        self.assertTrue(any("Colon" in e.title or "Syntax" in e.title for e in syn_errs))

    def test_python_division_by_zero_semantic(self):
        code = 'def div():\n    x = 100 / 0\n    return x'
        result = get_analyzer("python").analyze(code)
        sem_errs = [e for e in result.errors if e.phase == CompilerPhase.SEMANTIC.value]
        self.assertTrue(any("Zero" in e.title for e in sem_errs))


if __name__ == "__main__":
    unittest.main()
