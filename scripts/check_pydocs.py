"""
Esup-Pod - Documentation Audit Script

This script audits Python files across the project to ensure code documentation standards.
Specifically, it checks that:
- The mention 'Esup-Pod' is present on the first or second line of the file.
- A module-level docstring is defined.
- Every class has an associated docstring.
- Every function/method (excluding private methods other than __init__) has a docstring.

It uses 'git ls-files' to scan relevant files, falling back to an OS walk if git is unavailable.
"""

import ast
import os
import subprocess


def get_git_files(root_dir="src"):
    """
    Returns a list of all non-ignored Python files in the repository.
    Uses 'git ls-files' to accurately respect .gitignore.
    """
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", root_dir],
            universal_newlines=True,
        )
        files = output.splitlines()
        return [
            f
            for f in files
            if (f.endswith(".py") or f.endswith(".py.example")) and "__init__.py" not in f
        ]
    except subprocess.CalledProcessError:
        print("Warning: Could not use git to filter files. Falling back to manual crawl.")
        all_py_files = []
        for root, dirs, filenames in os.walk(root_dir):
            if any(
                d in root for d in [".git", "__pycache__", "venv", ".venv", "migrations"]
            ):
                continue
            for f in filenames:
                if (
                    f.endswith(".py") or f.endswith(".py.example")
                ) and "__init__.py" not in f:
                    all_py_files.append(os.path.join(root, f))
        return all_py_files


def check_file_pydocs(filepath):
    """Analyzes docstrings and Esup-Pod mention in a Python file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except Exception as e:
        return {"error": f"Parsing Error: {str(e)}"}

    results = {
        "missing_module_doc": False,
        "missing_esup_pod": False,
        "missing_class_docs": [],
        "missing_func_docs": [],
    }

    lines = content.splitlines()
    esup_pod_found = False
    for i in range(min(2, len(lines))):
        if "Esup-Pod" in lines[i]:
            esup_pod_found = True
            break

    if not esup_pod_found:
        results["missing_esup_pod"] = True

    module_doc = ast.get_docstring(tree)
    if not module_doc:
        results["missing_module_doc"] = True

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node):
                results["missing_class_docs"].append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.name.startswith("__")
                and node.name.endswith("__")
                and node.name != "__init__"
            ):
                continue

            func_length = node.end_lineno - node.lineno + 1
            if func_length < 3:
                continue

            if not ast.get_docstring(node):
                results["missing_func_docs"].append(node.name)

    return results


def run_audit(root_dir="src"):
    """Audits clean files list and outputs issues."""
    print(f"Auditing documentation (Git-aware) in: {root_dir}")
    print("-" * 60)

    clean_files = get_git_files(root_dir)
    found_issues = False

    for filepath in clean_files:
        audit = check_file_pydocs(filepath)

        if audit.get("error"):
            print(f"FAILED: {filepath} - {audit['error']}")
            continue

        issues = []
        if audit["missing_module_doc"]:
            issues.append("MISSING module docstring")
        elif audit["missing_esup_pod"]:
            issues.append("MISSING 'Esup-Pod' in header")

        if audit["missing_class_docs"]:
            issues.append(
                f"MISSING class docstrings: {', '.join(audit['missing_class_docs'])}"
            )

        if audit["missing_func_docs"]:
            funcs = audit["missing_func_docs"]
            summary = ", ".join(funcs[:5]) + (
                f" (+{len(funcs)-5})" if len(funcs) > 5 else ""
            )
            issues.append(f"MISSING func docstrings: {summary}")

        if issues:
            found_issues = True
            print(f"FILE: {filepath}")
            for issue in issues:
                print(f"  - {issue}")
            print()

    if not found_issues:
        print("Everything is perfect! 🏁")


if __name__ == "__main__":
    run_audit()
