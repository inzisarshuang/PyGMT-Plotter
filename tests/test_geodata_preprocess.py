"""Tests for bounded-memory raster preprocessing behavior."""

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

from geodata_preprocess import add_tifs


class AddTifsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write_raster(self, name: str, data: np.ndarray, x_origin: float = 0.0) -> Path:
        path = self.root / name
        profile = {
            "driver": "GTiff",
            "width": data.shape[1],
            "height": data.shape[0],
            "count": 1,
            "dtype": "float32",
            "crs": "EPSG:4326",
            "transform": from_origin(x_origin, 2.0, 1.0, 1.0),
            "nodata": -9999.0,
        }
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(data.astype("float32"), 1)
        return path

    def test_mask_modes_have_distinct_documented_behavior(self) -> None:
        first = self.write_raster("first.tif", np.array([[1, -9999], [-9999, -9999]]))
        second = self.write_raster("second.tif", np.array([[2, 3], [4, -9999]]))

        any_output = self.root / "any.tif"
        add_tifs(str(first), str(second), str(any_output), mask_any=True)
        with rasterio.open(any_output) as src:
            any_result = src.read(1)
        np.testing.assert_allclose(any_result[0, 0], 3.0)
        self.assertTrue(np.isnan(any_result[0, 1]))
        self.assertTrue(np.isnan(any_result[1, 0]))

        all_output = self.root / "all.tif"
        add_tifs(str(first), str(second), str(all_output), mask_any=False)
        with rasterio.open(all_output) as src:
            all_result = src.read(1)
        np.testing.assert_allclose(all_result[0, 1], 3.0)
        np.testing.assert_allclose(all_result[1, 0], 4.0)
        self.assertTrue(np.isnan(all_result[1, 1]))

    def test_rejects_misaligned_rasters_without_creating_output(self) -> None:
        first = self.write_raster("first.tif", np.ones((2, 2)))
        second = self.write_raster("second.tif", np.ones((2, 2)), x_origin=1.0)
        output = self.root / "output.tif"

        with self.assertRaisesRegex(ValueError, "transform"):
            add_tifs(str(first), str(second), str(output))

        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
