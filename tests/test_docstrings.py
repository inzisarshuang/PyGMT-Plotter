"""Enforce the repository rule that every production function states its purpose."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ProductionDocstringTests(unittest.TestCase):
    def test_every_production_function_has_a_docstring(self) -> None:
        """Report every production function or method missing an opening docstring."""
        source_files = list((REPOSITORY_ROOT / "lib").glob("*.py"))
        source_files.extend(REPOSITORY_ROOT.glob("plot_*/*.py"))
        missing = []

        for source_file in source_files:
            tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        missing.append(
                            f"{source_file.relative_to(REPOSITORY_ROOT)}:{node.lineno}:{node.name}"
                        )

        self.assertEqual(missing, [], "missing function docstrings:\n" + "\n".join(missing))


if __name__ == "__main__":
    unittest.main()
