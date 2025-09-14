# profile_extractor.py
from typing import Dict, List, Tuple
import rasterio
import os
import pandas as pd
import numpy as np
import pygmt
from pyproj import Geod


class ProfileExtractor:
    def __init__(self):
        pass
    
    def generate_tracks(
        self,
        start_coords: List[Tuple[float, float]],
        end_coords: List[Tuple[float, float]],
        num_points: int = 100,
        pointnames: List[str] = None
    ) -> Dict[str, np.ndarray]:
        """
        生成剖线采样轨迹。
        Generate evenly‐spaced sampling tracks between start and end coordinates.

        参数 (Parameters)
        ----------
        start_coords : List[Tuple[float, float]]
            剖线起点经纬度列表，每项为 (lon, lat)。
            List of start coordinates as (lon, lat) tuples.
        end_coords : List[Tuple[float, float]]
            剖线终点经纬度列表，每项为 (lon, lat)。
            List of end coordinates as (lon, lat) tuples.
        num_points : int, optional
            每条剖线生成的采样点数量（默认 100）。
            Number of sampling points per track (default 100).
        pointnames : List[str], optional
            每条剖线的名称列表（默认 None，则自动生成 A, B, C…）。
            Names for each track (if None, generates ['A', 'B', ...]).

        返回 (Returns)
        -------
        Dict[str, np.ndarray]
            字典：键为剖线名称，值为形状 (num_points, 2) 的 [lon, lat] 数组。
            Dict mapping each name to an (num_points, 2) array of [lon, lat] points.
        """
        # 1. 如果未提供名称，则自动生成 A, B, C… / Auto‐generate names if not provided
        if pointnames is None:
            pointnames = [chr(ord("A") + i) for i in range(len(start_coords))]

        tracks: Dict[str, np.ndarray] = {}
        # 2. 对每条剖线，生成等间距经纬度并合并 / For each track, generate spaced lons/lats and stack
        for name, start, end in zip(pointnames, start_coords, end_coords):
            # 2.1 等间距插值经度 / interpolate longitudes
            lons = np.linspace(start[0], end[0], num_points)
            # 2.2 等间距插值纬度 / interpolate latitudes
            lats = np.linspace(start[1], end[1], num_points)
            # 2.3 合并为二维数组，每行 [lon, lat] / stack into (num_points, 2) array
            track = np.column_stack((lons, lats))
            tracks[name] = track

        return tracks

    def extract_profile(
        self,
        grd_file: str,
        track: np.ndarray,
        newcolname: str = "z"
    ) -> pd.DataFrame:
        """
        提取剖面并计算累计距离。
        Extract profile from a GRD along a given track and compute cumulative distance.

        参数 (Parameters)
        ----------
        grd_file : str
            输入 GRD 文件路径。
            Path to the source GRD file.
        track : np.ndarray
            剖线轨迹，二维数组，每行 [lon, lat]。
            2D array of points [[lon, lat], ...] defining the profile line.
        newcolname : str, optional
            提取值列名，默认 "z"。
            Name of the extracted value column (default "z").

        返回 (Returns)
        -------
        pd.DataFrame
            包含以下列的 DataFrame：
            - "lon", "lat"：轨迹点经纬度 / longitude and latitude  
            - newcolname：从 GRD 中提取的值 / extracted values  
            - "distance"：从起点累计的距离（米） / cumulative distance in meters  
        """
        # 1. 用 pygmt.grdtrack 提取剖面数据 / Extract profile data with pygmt.grdtrack
        profile: pd.DataFrame = pygmt.grdtrack(
            points=track,
            grid=grd_file,
            newcolname=newcolname
        )

        # 2. 如果没有自动列名，则重命名为 lon, lat, newcolname
        # Rename columns if they are unnamed
        if not all(isinstance(col, str) for col in profile.columns):
            profile.columns = ["lon", "lat", newcolname]

        # 3. 计算沿轨迹累积距离（米）/ Compute cumulative distances (meters)
        geod = Geod(ellps="WGS84")
        distances = [0.0]
        for i in range(1, len(profile)):
            lon0, lat0 = profile.loc[i - 1, "lon"], profile.loc[i - 1, "lat"]
            lon1, lat1 = profile.loc[i,     "lon"], profile.loc[i,     "lat"]
            _, _, d = geod.inv(lon0, lat0, lon1, lat1)
            distances.append(distances[-1] + d)
        profile["distance"] = distances

        return profile
    
    def add_tifs(
        self,
        tif1_path: str,
        tif2_path: str,
        out_tif: str,
        mask_any: bool = True
    ) -> None:
        """
        将两幅 GeoTIFF 按像元相加，并根据 nodata 掩膜结果。
        Add two GeoTIFF rasters pixel‐wise with nodata masking.

        参数 (Parameters)
        ----------
        tif1_path : str
            第一幅输入 GeoTIFF 文件路径。
            Path to the first input GeoTIFF.
        tif2_path : str
            第二幅输入 GeoTIFF 文件路径。
            Path to the second input GeoTIFF.
        out_tif : str
            输出 GeoTIFF 文件路径。
            Path where the output GeoTIFF will be saved.
        mask_any : bool, optional
            掩膜模式：
            - True：任一像元为 nodata 时输出 nodata（mask = nan1 | nan2）。
            - False：仅当两者均为 nodata 时才输出 nodata（mask = nan1 & nan2）。
            Mask mode: True to mask if any input is nodata, False to mask only if all inputs are nodata.

        返回 (Returns)
        -------
        None
        """
        print(f"Adding TIFFs:\n  1: {tif1_path}\n  2: {tif2_path}\nMask any nodata: {mask_any}")

        # 1. 打开两幅 TIF 并读取元数据与像元值 / Open both rasters and read metadata & arrays
        with rasterio.open(tif1_path) as src1, rasterio.open(tif2_path) as src2:
            meta = src1.meta.copy()             # 复制第一个文件的元数据 / copy metadata from first raster
            nodata1 = src1.nodata               # 第一个文件的 nodata 值 / nodata value of raster1
            nodata2 = src2.nodata               # 第二个文件的 nodata 值 / nodata value of raster2

            arr1 = src1.read(1).astype("float32")  # 读取第一波段并转换为 float32 / read band1 as float32
            arr2 = src2.read(1).astype("float32")  # 读取第一波段并转换为 float32 / read band1 as float32

        # 2. 将 nodata 值替换为 NaN，便于后续掩膜 / Convert nodata to NaN for masking
        if nodata1 is not None:
            arr1[arr1 == nodata1] = np.nan
        if nodata2 is not None:
            arr2[arr2 == nodata2] = np.nan

        # 3. 构造掩膜 / Build mask according to mask_any
        nan1 = np.isnan(arr1)
        nan2 = np.isnan(arr2)
        if mask_any:
            mask = nan1 | nan2  # 任一为 NaN 时掩膜 / mask if either is NaN
        else:
            mask = nan1 & nan2  # 仅全为 NaN 时掩膜 / mask if both are NaN

        # 4. 执行像元相加，再应用掩膜 / Perform pixel‐wise addition and apply mask
        result = arr1 + arr2
        result[mask] = np.nan  # 将掩膜位置置为 NaN / set masked locations to NaN

        # 5. 更新元数据并写出结果 / Update metadata and write output
        meta.update(dtype="float32", nodata=np.nan)
        with rasterio.open(out_tif, "w", **meta) as dst:
            dst.write(result, 1)
        print(f"Output saved to: {out_tif}")


if __name__ == "__main__":
    
    # 测试示例（可根据实际文件路径测试）
    extractor = ProfileExtractor()

    # 示例 TIF 影像相加
    extractor.add_tifs("data/S1_AS_Norcia.tif", "data/S1_AS_Visso.tif", "data/S1_AS_Add.tif", mask_any="True")
    extractor.add_tifs("data/S1_AS_Norcia.tif", "data/S1_AS_Visso.tif", "data/S1_AS_Add.tif", mask_any="False")
    with rasterio.open("data/S1_AS_Add.tif") as src:
        arr = src.read(1).astype(">f4")    # 读一波段并转为 大端float32
    # 输出对应的二进制文件流（按行连续、无 header）
    arr.tofile("data/S1_AS_Add.bin")
    
    # 示例 TIF 数据转换
    tif_path = "data/S1_AS_Add.tif"     # 替换为实际 TIF 文件路径
    grd_tif = "data/S1_AS_Add.grd"
    region_tif = extractor.load_tif_to_grd(tif_path, grd_tif)
    
    # 示例 TXT 数据转换
    txt_path = "data/ALOS2_AS.txt"  # 替换为实际 TXT 文件路径
    grd_txt = "data/ALOS2_AS.grd"
    region = extractor.load_txt_to_grd(txt_path, grd_txt)
    
    # 示例剖线轨迹生成与提取
    start_coords = [
        (12.97, 42.91),
        (12.97, 42.85),
        (12.97, 42.799),
        (12.97, 42.75)
    ]
    end_coords = [
        (13.35, 42.93),
        (13.35, 42.87),
        (13.35, 42.819),
        (13.35, 42.77)
    ]
    # 每条剖线需要生成的采样点数量
    num_points = 100  
    # 剖线名称列表
    pointnames = ["A", "B", "C", "D"]
    # 生成剖线轨迹
    tracks = extractor.generate_tracks(start_coords=start_coords, end_coords=end_coords, num_points=num_points, pointnames=pointnames)
    # 提取生成的剖线数据
    profile = extractor.extract_profile(grd_tif, tracks["A"])
    # 打印生成的剖线轨迹
    print("剖面数据预览:")
    print(profile.head(10)) # 打印前十行

    os.system('rm -f *.xml')
