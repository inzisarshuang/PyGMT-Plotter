"""
pygmt_geo
=========

功能概述:
    集中提供低内存地理栅格运算、GeoTIFF/TXT 到 GMT GRD 转换、
    网格范围读取、剖面轨迹生成和空间采样功能。

函数说明:
    ``_validate_matching_grids``:
        校验两幅栅格的尺寸、仿射变换和坐标参考系是否一致。
    ``add_tifs``:
        按窗口相加两幅共网格单波段 GeoTIFF，并按配置传播空值。
    ``region_from_grd``:
        从 GMT 可读网格提取 xmin、xmax、ymin、ymax 范围。
    ``tif2grd``:
        按窗口读取、缩放 GeoTIFF，并转换为 GMT GRD。
    ``txt2grd``:
        分块读取经纬度点表，缩放数值并转换为 GMT GRD。
    ``prepare_grid``:
        根据输入类型统一调度 TIF 或 TXT 网格转换。
    ``prepare_dataset_grid``:
        根据公共数据集配置结构准备 GMT GRD。
    ``generate_tracks``:
        在多组起止坐标之间生成命名的等间距剖面轨迹。
    ``extract_profile``:
        沿指定轨迹采样网格，并计算 WGS84 累计距离。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pygmt
import rasterio
from pyproj import Geod

from pygmt_io import gdal_translate, replace_dataset, temporary_path


def _validate_matching_grids(src1: rasterio.io.DatasetReader, src2: rasterio.io.DatasetReader) -> None:
    """Ensure two rasters share the same pixel grid before arithmetic."""
    mismatches = []
    if (src1.width, src1.height) != (src2.width, src2.height):
        mismatches.append("dimensions")
    if src1.transform != src2.transform:
        mismatches.append("transform")
    if src1.crs != src2.crs:
        mismatches.append("CRS")
    if mismatches:
        raise ValueError(f"input rasters do not share the same grid: {', '.join(mismatches)}")


def add_tifs(
    tif1_path: str,
    tif2_path: str,
    out_tif: str,
    mask_any: bool = True,
) -> None:
    """Add two single-band GeoTIFFs using bounded-memory window reads.

    将两幅共网格单波段 GeoTIFF 按像元相加，并使用分块读取限制内存占用。

    Parameters
    ----------
    tif1_path, tif2_path : str
        Input GeoTIFF paths. Their dimensions, transform, and CRS must match.
        输入文件路径；两者的尺寸、仿射变换和坐标系必须一致。
    out_tif : str
        Output GeoTIFF path. The file is replaced only after a complete write.
        输出路径；仅在完整写入成功后替换目标文件。
    mask_any : bool, default=True
        If True, output nodata when either input is nodata. If False, treat one
        missing operand as zero and output nodata only when both are nodata.
        为 True 时任一输入为空即输出空值；为 False 时单侧空值按零处理，
        仅两侧均为空时输出空值。
    """
    source1 = Path(tif1_path).expanduser().resolve()
    source2 = Path(tif2_path).expanduser().resolve()
    output = Path(out_tif).expanduser().resolve()
    for source in (source1, source2):
        if not source.is_file():
            raise FileNotFoundError(f"input GeoTIFF not found: {source}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with temporary_path(output.parent, output.suffix or ".tif") as temporary_output:
        with rasterio.open(source1) as src1, rasterio.open(source2) as src2:
            if src1.count < 1 or src2.count < 1:
                raise ValueError("both input rasters must contain at least one band")
            _validate_matching_grids(src1, src2)

            profile = src1.profile.copy()
            profile.update(count=1, dtype="float32", nodata=np.nan)
            with rasterio.open(temporary_output, "w", **profile) as dst:
                for _, window in src1.block_windows(1):
                    arr1 = src1.read(1, window=window, masked=True).filled(np.nan).astype("float32")
                    arr2 = src2.read(1, window=window, masked=True).filled(np.nan).astype("float32")
                    nan1 = np.isnan(arr1)
                    nan2 = np.isnan(arr2)

                    if mask_any:
                        result = arr1 + arr2
                        result[nan1 | nan2] = np.nan
                    else:
                        result = np.nan_to_num(arr1, nan=0.0) + np.nan_to_num(arr2, nan=0.0)
                        result[nan1 & nan2] = np.nan
                    dst.write(result.astype("float32", copy=False), 1, window=window)

        replace_dataset(temporary_output, output)

    print(f"Output saved to: {output}")


def region_from_grd(grid_path: str) -> List[float]:
    """Return a GMT-readable grid region as ``[xmin, xmax, ymin, ymax]``."""
    info_text = pygmt.grdinfo(grid=grid_path, per_column="n")
    values = np.fromstring(info_text, sep=" ")
    if values.size < 4:
        raise ValueError(f"cannot parse grid region: {grid_path}")
    return values[:4].astype(float).tolist()


def tif2grd(
    tif_path: str,
    grd_path: str,
    scale: float = 1.0,
    nan_to_zero: bool = True,
) -> List[float]:
    """Convert one GeoTIFF band to a scaled GMT grid using windowed reads."""
    source = Path(tif_path).expanduser().resolve()
    output = Path(grd_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"input GeoTIFF not found: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(source) as src:
        if src.count < 1:
            raise ValueError(f"input GeoTIFF has no raster bands: {source}")
        bounds = src.bounds
        region = [bounds.left, bounds.right, bounds.bottom, bounds.top]
        profile = src.profile.copy()
        profile.update(count=1, dtype=rasterio.float32, nodata=0 if nan_to_zero else np.nan)

        with temporary_path(output.parent, ".tif") as temporary_tif:
            with rasterio.open(temporary_tif, "w", **profile) as dst:
                for _, window in src.block_windows(1):
                    data = src.read(1, window=window, masked=True).astype("float32")
                    scaled = data.filled(np.nan) * np.float32(scale)
                    if nan_to_zero:
                        scaled = np.nan_to_num(scaled, nan=0.0)
                    dst.write(scaled.astype("float32", copy=False), 1, window=window)

            with temporary_path(output.parent, output.suffix or ".grd") as temporary_grd:
                gdal_translate(str(temporary_tif), str(temporary_grd), fmt="GSBG")
                replace_dataset(temporary_grd, output)

    print(f"Converted to GRD: {output}")
    return region


def txt2grd(
    txt_path: str,
    grd_path: str,
    scale: float = 1.0,
    space: float = 0.0005,
    chunk_rows: int = 250_000,
) -> List[float]:
    """Convert a lon/lat/value text table to a GMT grid using chunked reads."""
    source = Path(txt_path).expanduser().resolve()
    output = Path(grd_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"input text file not found: {source}")
    if space <= 0:
        raise ValueError(f"space must be positive; got {space}")
    if chunk_rows <= 0:
        raise ValueError(f"chunk_rows must be positive; got {chunk_rows}")
    output.parent.mkdir(parents=True, exist_ok=True)

    bounds = [np.inf, -np.inf, np.inf, -np.inf]
    row_count = 0
    with temporary_path(output.parent, ".xyz") as temporary_xyz:
        for chunk in pd.read_csv(source, sep=r"\s+", chunksize=chunk_rows):
            if len(chunk.columns) < 3 or "lon" not in chunk or "lat" not in chunk:
                raise ValueError(
                    f"text input must contain lon/lat headers and at least three columns: {source}"
                )
            value_column = chunk.columns[2]
            selected = chunk.loc[:, ["lon", "lat", value_column]].copy()
            selected["lon"] = pd.to_numeric(selected["lon"], errors="raise")
            selected["lat"] = pd.to_numeric(selected["lat"], errors="raise")
            selected[value_column] = pd.to_numeric(selected[value_column], errors="raise") * scale
            selected = selected[np.isfinite(selected["lon"]) & np.isfinite(selected["lat"])]
            if selected.empty:
                continue

            bounds[0] = min(bounds[0], float(selected["lon"].min()))
            bounds[1] = max(bounds[1], float(selected["lon"].max()))
            bounds[2] = min(bounds[2], float(selected["lat"].min()))
            bounds[3] = max(bounds[3], float(selected["lat"].max()))
            selected.to_csv(
                temporary_xyz,
                sep="\t",
                columns=["lon", "lat", value_column],
                header=False,
                index=False,
                mode="a",
            )
            row_count += len(selected)

        if row_count == 0:
            raise ValueError(f"text input contains no valid coordinate rows: {source}")

        data_region = [float(value) for value in bounds]
        x_steps = max(1, int(np.ceil((data_region[1] - data_region[0]) / space)))
        y_steps = max(1, int(np.ceil((data_region[3] - data_region[2]) / space)))
        region = [
            data_region[0],
            data_region[0] + x_steps * space,
            data_region[2],
            data_region[2] + y_steps * space,
        ]
        with temporary_path(output.parent, output.suffix or ".grd") as temporary_grd:
            pygmt.xyz2grd(
                data=str(temporary_xyz),
                region=region,
                spacing=space,
                outgrid=str(temporary_grd),
            )
            replace_dataset(temporary_grd, output)

    print(f"Converted text to GRD: {output}")
    return region


def prepare_grid(
    input_type: str,
    input_path: str,
    grd_path: str,
    scale: float = 1.0,
    space: float = 0.0005,
    nan_to_zero: bool = True,
    chunk_rows: int = 250_000,
) -> List[float]:
    """Convert a supported raster or point table into a GMT grid."""
    normalized_type = input_type.strip().lower()
    if normalized_type == "tif":
        return tif2grd(input_path, grd_path, scale, nan_to_zero)
    if normalized_type == "txt":
        return txt2grd(input_path, grd_path, scale, space, chunk_rows)
    raise ValueError(f"unsupported input_type: {input_type}; choose from tif, txt")


def prepare_dataset_grid(dataset: Dict[str, object]) -> List[float]:
    """Prepare a GMT grid from the shared plotting dataset schema."""
    required = ("input_type", "input_path", "grd_path", "scale", "space", "nan_to_zero")
    missing = [key for key in required if key not in dataset]
    if missing:
        raise ValueError(f"dataset configuration is missing: {', '.join(missing)}")
    return prepare_grid(
        input_type=str(dataset["input_type"]),
        input_path=str(dataset["input_path"]),
        grd_path=str(dataset["grd_path"]),
        scale=float(dataset["scale"]),
        space=float(dataset["space"]),
        nan_to_zero=bool(dataset["nan_to_zero"]),
        chunk_rows=int(dataset.get("chunk_rows", 250_000)),
    )


def generate_tracks(
    start_coords: List[Tuple[float, float]],
    end_coords: List[Tuple[float, float]],
    num_points: int = 100,
    pointnames: Optional[List[str]] = None,
) -> Dict[str, np.ndarray]:
    """Generate named, evenly spaced profile tracks between coordinate pairs."""
    if len(start_coords) != len(end_coords):
        raise ValueError(
            "start_coords and end_coords must have the same length; "
            f"got {len(start_coords)} and {len(end_coords)}"
        )
    if not start_coords:
        raise ValueError("at least one profile track is required")
    if num_points < 2:
        raise ValueError(f"num_points must be at least 2; got {num_points}")

    if pointnames is None:
        pointnames = [chr(ord("A") + index) for index in range(len(start_coords))]
    if len(pointnames) != len(start_coords):
        raise ValueError(
            "pointnames must match the number of profile tracks; "
            f"got {len(pointnames)} names and {len(start_coords)} tracks"
        )
    if len(set(pointnames)) != len(pointnames):
        raise ValueError("pointnames must be unique")

    tracks: Dict[str, np.ndarray] = {}
    for name, start, end in zip(pointnames, start_coords, end_coords):
        lons = np.linspace(start[0], end[0], num_points)
        lats = np.linspace(start[1], end[1], num_points)
        tracks[name] = np.column_stack((lons, lats))
    return tracks


def extract_profile(
    grd_file: str,
    track: np.ndarray,
    newcolname: str = "z",
) -> pd.DataFrame:
    """Sample a GMT grid along a track and append WGS84 cumulative distance."""
    track_array = np.asarray(track, dtype=float)
    if track_array.ndim != 2 or track_array.shape[1] != 2 or len(track_array) < 2:
        raise ValueError("track must have shape (n, 2) with at least two lon/lat points")

    profile: pd.DataFrame = pygmt.grdtrack(
        points=track_array,
        grid=grd_file,
        newcolname=newcolname,
    )
    if profile.shape[1] < 3:
        raise ValueError(f"grdtrack returned fewer than three columns for {grd_file}")
    profile = profile.iloc[:, :3].copy()
    profile.columns = ["lon", "lat", newcolname]
    if len(profile) == 0:
        profile["distance"] = pd.Series(dtype=float)
        return profile

    geod = Geod(ellps="WGS84")
    lons = profile["lon"].to_numpy(dtype=float)
    lats = profile["lat"].to_numpy(dtype=float)
    _, _, segment_distances = geod.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])
    profile["distance"] = np.concatenate(([0.0], np.cumsum(segment_distances)))
    return profile
