"""Focused tests for shared plotting utilities."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "lib"))

from pygmt_plotter import PyGMTPlotter


class TrackTests(unittest.TestCase):
    def test_generates_named_tracks(self) -> None:
        tracks = PyGMTPlotter.generate_tracks(
            start_coords=[(0.0, 1.0)],
            end_coords=[(2.0, 3.0)],
            num_points=3,
            pointnames=["A"],
        )
        np.testing.assert_allclose(tracks["A"], [[0, 1], [1, 2], [2, 3]])

    def test_rejects_silent_zip_truncation_and_duplicate_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "same length"):
            PyGMTPlotter.generate_tracks([(0, 0)], [], num_points=3)
        with self.assertRaisesRegex(ValueError, "unique"):
            PyGMTPlotter.generate_tracks(
                [(0, 0), (1, 1)], [(1, 1), (2, 2)], num_points=3, pointnames=["A", "A"]
            )

    def test_requires_active_figure_before_saving(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "call new"):
            PyGMTPlotter().save("unused.png")

    def test_reset_restores_instance_defaults(self) -> None:
        plotter = PyGMTPlotter(defaults={"FONT_TITLE": "10p,Helvetica"})
        plotter.set_defaults(FONT_TITLE="20p,Helvetica-Bold")
        plotter.reset_defaults()
        self.assertEqual(plotter.defaults["FONT_TITLE"], "10p,Helvetica")


class GridConversionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_converts_tif_by_windows_and_text_by_chunks(self) -> None:
        tif_path = self.root / "input.tif"
        with rasterio.open(
            tif_path,
            "w",
            driver="GTiff",
            width=2,
            height=2,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(10.0, 12.0, 1.0, 1.0),
            nodata=-9999.0,
        ) as dst:
            dst.write(np.array([[1.0, 2.0], [3.0, -9999.0]], dtype="float32"), 1)

        tif_grid = self.root / "from_tif.grd"
        region = PyGMTPlotter.tif2grd(str(tif_path), str(tif_grid), scale=2.0, nan_to_zero=False)
        self.assertEqual(region, [10.0, 12.0, 10.0, 12.0])
        self.assertTrue(tif_grid.is_file())

        text_path = self.root / "points.txt"
        text_path.write_text("lon lat value\n0 0 1\n1 0 2\n0 1 3\n1 1 4\n", encoding="utf-8")
        text_grid = self.root / "from_text.grd"
        text_region = PyGMTPlotter.txt2grd(
            str(text_path), str(text_grid), scale=0.5, space=1.0, chunk_rows=2
        )
        self.assertEqual(text_region, [0.0, 1.0, 0.0, 1.0])
        self.assertTrue(text_grid.is_file())
        self.assertEqual(list(self.root.glob(".pygmt_plotter_*")), [])


if __name__ == "__main__":
    unittest.main()
