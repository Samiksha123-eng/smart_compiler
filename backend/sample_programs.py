"""
Curated sample programs for C, C++, Java, and Python.
Designed for educational demonstrations of Lexical, Syntax, and Semantic errors.
"""

SAMPLES = {
    "c": {
        "buggy": """#include <stdio.h>

int main() {
    // 1. Lexical Error: stray illegal character '@'
    int count = 10;
    @

    // 2. Syntax Error: missing semicolon at end of statement
    int total = count * 2

    // 3. Semantic Error: undeclared identifier 'conut' (typo for 'count')
    int result = conut + 5;

    // 4. Semantic Error: type mismatch (assigning string literal to int)
    int label = "Academic Project";

    // 5. Semantic Error: constant division by zero
    int average = total / 0;

    printf("Result: %d\\n", result);
    return 0;
}
""",
        "clean": """#include <stdio.h>

int main() {
    int count = 10;
    int total = count * 2;
    int result = count + 5;
    char* label = "Academic Project";
    int average = total / 2;

    printf("Label: %s\\n", label);
    printf("Result: %d, Average: %d\\n", result, average);
    return 0;
}
""",
        "lexical_demo": """#include <stdio.h>

int main() {
    // Unterminated string literal
    char* message = "Hello, Compiler World;

    // Illegal character
    int $price = 100;

    // Malformed numeric literal
    int hexVal = 123xyz;

    return 0;
}
""",
        "syntax_demo": """#include <stdio.h>

int main() {
    // Missing semicolon
    int x = 42

    // Malformed if condition (missing parentheses)
    if x > 10 {
        printf("Greater\\n");
    }

    // Malformed for loop header
    for (int i = 0 i < 5 i++) {
        printf("%d\\n", i);
    }

    return 0;
}
""",
        "semantic_demo": """#include <stdio.h>

void displayBanner() {
    // Semantic Error: void function returning value
    return 42;
}

int main() {
    int x = 10;
    // Semantic Error: Redeclaration in same scope
    int x = 20;

    // Semantic Error: Undeclared variable
    unknownVariable = 50;

    // Semantic Error: Division by zero
    int z = 100 / 0;

    return 0;
}
"""
    },
    "cpp": {
        "buggy": """#include <iostream>
// Missing 'using namespace std;' demonstrates scope resolution check

class Student {
public:
    int id;
    std::string name;
} // Syntax Error: missing semicolon after class definition

int main() {
    // Syntax Error: Invalid stream operator 'cout >>'
    cout >> "Welcome to C++ Detective" << endl;

    // Semantic Error: Undeclared variable 'score'
    score = 95;

    // Semantic Error: Incompatible type assignment
    int age = "twenty";

    // Semantic Error: Division by zero
    int ratio = 100 / 0;

    return 0;
}
""",
        "clean": """#include <iostream>
using namespace std;

class Student {
public:
    int id;
    string name;
};

int main() {
    cout << "Welcome to C++ Detective" << endl;

    int score = 95;
    int age = 20;
    int ratio = 100 / 2;

    cout << "Score: " << score << ", Age: " << age << ", Ratio: " << ratio << endl;
    return 0;
}
"""
    },
    "java": {
        "buggy": """public class CompilerDemo {
    // Syntax Error: Malformed main method signature (missing 'static')
    public void main(String[] args) {
        // Lexical Error: Stray character
        int count = 5;
        @

        // Syntax Error: Missing semicolon
        int factor = 10

        // Syntax Error: Typo in method name (printLn instead of println)
        System.out.printLn("Factor is: " + factor);

        // Semantic Error: Incompatible types (int cannot be converted to boolean)
        boolean isActive = 1;

        // Semantic Error: Undeclared identifier
        int total = factor * unknownFactor;

        // Semantic Error: Constant division by zero
        int zeroDiv = 50 / 0;
    }
}
""",
        "clean": """public class CompilerDemo {
    public static void main(String[] args) {
        int count = 5;
        int factor = 10;

        System.out.println("Factor is: " + factor);

        boolean isActive = true;
        int unknownFactor = 2;
        int total = factor * unknownFactor;
        int zeroDiv = 50 / 5;

        System.out.println("Total: " + total + ", Active: " + isActive);
    }
}
"""
    },
    "python": {
        "buggy": """# Smart Compiler Error Detective - Python Demo

# 1. Syntax Error: Missing colon after function definition
def calculate_grade(score)
    # 2. Semantic Error: Undeclared variable used in calculation
    weighted_score = score * weight_factor

    # 3. Semantic Error: Type mismatch (str + int)
    summary = "Final Grade: " + 95

    # 4. Semantic Error: Division by zero constant
    percentage = score / 0

    return summary

# 5. Syntax Error: Missing colon in if statement
if calculate_grade(85) == "A"
    print("Excellent work!")

# 6. Lexical Error: Stray illegal symbol
$invalid_token = 42
""",
        "clean": """# Smart Compiler Error Detective - Clean Python Program

def calculate_grade(score):
    weight_factor = 1.1
    weighted_score = score * weight_factor
    summary = "Final Grade: " + str(95)
    percentage = score / 100.0
    return summary

if calculate_grade(85):
    print("Excellent work!")

valid_token = 42
print("Token value:", valid_token)
"""
    }
}
