import ast
import os
import subprocess


def get_git_files(root_dir="src"):
    """
    Returns a list of all non-ignored Python files in the repository.
    Uses 'git ls-files' to accurately respect .gitignore.
    """
    try:
        # Get all tracked files and untracked (but not ignored) files
        output = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", root_dir],
            universal_newlines=True,
        )
        files = output.splitlines()
        # Strictly only .py and NO __init__.py (usually boilerplate)
        return [f for f in files if f.endswith(".py") and "__init__.py" not in f]
    except subprocess.CalledProcessError:
        # If not a git repo or git not available, fall back to os.walk with manual filters
        print("Warning: Could not use git to filter files. Falling back to manual crawl.")
        all_py_files = []
        for root, dirs, filenames in os.walk(root_dir):
            if any(d in root for d in [".git", "__pycache__", "venv", ".venv"]):
                continue
            for f in filenames:
                if f.endswith(".py") and "__init__.py" not in f:
                    all_py_files.append(os.path.join(root, f))
        return all_py_files


def check_file_pydocs(filepath):
    """Analyzes docstrings, comments, newline at EOF, and Esup-Pod mention in a Python file."""
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
        "missing_newline_eof": False,
    }

    if content and not content.endswith("\n"):
        results["missing_newline_eof"] = True

    # 1. Module Docstring Check
    module_doc = ast.get_docstring(tree)
    if not module_doc:
        results["missing_module_doc"] = True
    elif "Esup-Pod" not in module_doc:
        results["missing_esup_pod"] = True

    # 2. Deep AST Walk for Classes and Functions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node):
                results["missing_class_docs"].append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private/special methods like __repr__, but KEEP __init__
            if (
                node.name.startswith("__")
                and node.name.endswith("__")
                and node.name != "__init__"
            ):
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

        if audit.get("missing_newline_eof"):
            issues.append("MISSING empty line at EOF")

        if issues:
            found_issues = True
            print(f"FILE: {filepath}")
            for issue in issues:
                print(f"  - {issue}")
            print()

    if not found_issues:
        print("Everything is perfect! 🏁 (No errors)")


if __name__ == "__main__":
    run_audit()
