"""Conservative syntax patterns, not a general semantic bug detector."""

import ast
import textwrap
import time

from .schemas import Category, Finding, InferenceMetadata, ReviewResult


class StaticReviewer:
    def review(self, function):
        started = time.perf_counter()
        tree = ast.parse(textwrap.dedent(function.code))
        findings = []
        root = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))

        def add(node, category, explanation, fix):
            findings.append(
                Finding(
                    path=function.path,
                    line=function.start_line + node.lineno - 1,
                    category=category,
                    explanation=explanation,
                    suggested_fix=fix,
                )
            )

        def nodes(node):
            yield node
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                yield from nodes(child)

        defaults = [*root.args.defaults, *[d for d in root.args.kw_defaults if d is not None]]
        for default in defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)) or (
                isinstance(default, ast.Call)
                and isinstance(default.func, ast.Name)
                and default.func.id in {"list", "dict", "set"}
                and not default.args
                and not default.keywords
            ):
                add(
                    default,
                    Category.MUTABLE,
                    "Default collection is shared across calls.",
                    "Use None as the default and create a new collection inside the function.",
                )
        for node in nodes(root):
            if isinstance(node, ast.Compare) and len(node.ops) == 1:
                left, right, op = node.left, node.comparators[0], node.ops[0]
                if isinstance(op, (ast.Is, ast.IsNot)) and any(
                    isinstance(n, (ast.List, ast.Dict, ast.Set)) for n in (left, right)
                ):
                    add(
                        node,
                        Category.NONE_EMPTY,
                        "Identity comparison with a new collection does not test emptiness.",
                        "Use a truthiness or equality check appropriate to the input contract.",
                    )
            if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                call = node.iter
                if not (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == "range"
                    and len(call.args) == 1
                ):
                    continue
                limit = call.args[0]
                if not (
                    isinstance(limit, ast.BinOp)
                    and isinstance(limit.op, ast.Add)
                    and isinstance(limit.right, ast.Constant)
                    and limit.right.value == 1
                    and isinstance(limit.left, ast.Call)
                    and isinstance(limit.left.func, ast.Name)
                    and limit.left.func.id == "len"
                    and len(limit.left.args) == 1
                ):
                    continue
                collection = ast.dump(limit.left.args[0])
                if any(
                    isinstance(n, ast.Subscript)
                    and ast.dump(n.value) == collection
                    and isinstance(n.slice, ast.Name)
                    and n.slice.id == node.target.id
                    for statement in node.body
                    for n in nodes(statement)
                ):
                    add(
                        node,
                        Category.BOUNDARY,
                        "Loop includes len(collection), which is outside valid index bounds.",
                        "Use range(len(collection)) or iterate over the collection directly.",
                    )
        return ReviewResult(
            function=function,
            status="ok",
            findings=findings,
            metadata=InferenceMetadata(
                backend="static",
                prompt_version="ast-v1",
                latency_seconds=time.perf_counter() - started,
            ),
        )
