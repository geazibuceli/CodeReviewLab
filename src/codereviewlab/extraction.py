"""Extract complete functions; never reconstruct code from partial diff hunks."""

import ast
import re
import tokenize
from pathlib import Path

from .schemas import FunctionInput


def extract_source(source: str, path: str, max_lines: int = 200) -> tuple[list, list]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [], [f"{path}:{exc.lineno}: syntax error: {exc.msg}"]
    lines = source.splitlines()
    imports = [
        ast.get_source_segment(source, n) or ""
        for n in tree.body
        if isinstance(n, ast.Import | ast.ImportFrom)
    ]
    context = "\n".join(imports)[:4000]
    functions, issues = [], []

    def visit(node, parents=()):
        for child in ast.iter_child_nodes(node):
            scoped = isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            name = (*parents, child.name) if scoped else parents
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                start = min([child.lineno] + [d.lineno for d in child.decorator_list])
                end = child.end_lineno
                if end - start + 1 > max_lines:
                    issues.append(f"{path}:{start}: oversized function {'.'.join(name)}")
                else:
                    functions.append(
                        FunctionInput(
                            path=path,
                            name=".".join(name),
                            start_line=start,
                            end_line=end,
                            code="\n".join(lines[start - 1 : end]),
                            context=context,
                        )
                    )
            visit(child, name)

    visit(tree)
    return functions, issues


def extract_file(path: Path, max_lines: int = 200) -> tuple[list, list]:
    if path.suffix != ".py":
        return [], [f"{path}: unsupported input; expected .py"]
    with tokenize.open(path) as stream:
        return extract_source(stream.read(), path.as_posix(), max_lines)


def changed_functions(diff: str, repo: Path) -> tuple[list, list]:
    """Use post-image repository files only after verifying every hunk's context."""
    root = repo.resolve()
    selected, issues = [], []
    blocks = re.split(r"(?m)^diff --git .*\n", diff)
    if len(blocks) == 1:
        blocks = re.split(r"(?m)(?=^--- )", diff)
    for block in blocks:
        match = re.search(r"(?m)^\+\+\+ (?:b/)?([^\n\t]+)", block)
        if not match:
            continue
        relative = match.group(1)
        if relative == "/dev/null":
            issues.append("Deleted file has no post-image functions")
            continue
        target = (root / relative).resolve()
        if not target.is_relative_to(root):
            issues.append(f"{relative}: unsafe diff path")
            continue
        if target.suffix != ".py":
            issues.append(f"{relative}: unsupported diff file")
            continue
        if not target.is_file():
            issues.append(f"{relative}: incomplete diff context; post-image file missing")
            continue
        with tokenize.open(target) as stream:
            source = stream.read()
        source_lines = source.splitlines()
        changed, valid, saw_hunk = set(), True, False
        hunk_lines = block.splitlines()
        i = 0
        while i < len(hunk_lines):
            header = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", hunk_lines[i])
            if not header:
                i += 1
                continue
            saw_hunk = True
            position = int(header[3])
            old_count = int(header[2] or 1)
            new_count = int(header[4] or 1)
            old_seen = new_seen = 0
            i += 1
            while i < len(hunk_lines) and not hunk_lines[i].startswith("@@"):
                line = hunk_lines[i]
                if line.startswith((" ", "+")):
                    if (
                        position < 1
                        or position > len(source_lines)
                        or (source_lines[position - 1] != line[1:])
                    ):
                        valid = False
                    if line.startswith("+"):
                        changed.add(position)
                    else:
                        old_seen += 1
                    new_seen += 1
                    position += 1
                elif line.startswith("-"):
                    old_seen += 1
                    # A deletion changes the adjacent post-image statement.
                    changed.add(max(1, min(position, len(source_lines))))
                elif not line.startswith("\\"):
                    break
                i += 1
            if (old_seen, new_seen) != (old_count, new_count):
                valid = False
        if not valid or not saw_hunk:
            issues.append(f"{relative}: incomplete or mismatched diff context")
            continue
        functions, errors = extract_source(source, relative)
        issues.extend(errors)
        selected.extend(
            f for f in functions if any(f.start_line <= line <= f.end_line for line in changed)
        )
    if not blocks or not re.search(r"(?m)^\+\+\+ ", diff):
        issues.append("No supported unified diff file headers found")
    return list({(f.path, f.start_line): f for f in selected}.values()), issues
