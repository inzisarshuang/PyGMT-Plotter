"""Focused tests for shared plotting state and output behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "lib"))

from pygmt_visual import PyGMTPlotter


class PlotterStateTests(unittest.TestCase):
    def test_requires_active_figure_before_saving(self) -> None:
        """Reject save requests until the caller creates a figure."""
        with self.assertRaisesRegex(RuntimeError, "call new"):
            PyGMTPlotter().save("unused.png")

    def test_reset_restores_instance_defaults(self) -> None:
        """Restore constructor defaults after instance-level style changes."""
        plotter = PyGMTPlotter(defaults={"FONT_TITLE": "10p,Helvetica"})
        plotter.set_defaults(FONT_TITLE="20p,Helvetica-Bold")
        plotter.reset_defaults()
        self.assertEqual(plotter.defaults["FONT_TITLE"], "10p,Helvetica")


if __name__ == "__main__":
    unittest.main()
