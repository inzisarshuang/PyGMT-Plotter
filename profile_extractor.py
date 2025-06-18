# profile_extractor.py
from typing import List
import rasterio
import os
from osgeo import gdal
import pandas as pd
import numpy as np
import pygmt
from pyproj import Geod


class ProfileExtractor:
    def __init__(self):
        pass

    def load_tif_to_grd(
        self,
        tif_path: str,
        grd_path: str,
        scale: float = 1.0,
        nan_to_zero: bool = True
    ) -> List[float]:
        """
        加载 TIF 文件，应用缩放因子，并转换为 GRD 格式。
        Load a TIF file, apply a scale factor, and convert it to GRD format.

        参数 (Parameters)
        ----------
        tif_path : str
            原始 TIF 文件路径。
            Path to the source TIF file.
        grd_path : str
            输出 GRD 文件路径。
            Path where the output GRD file will be saved.
        scale : float, optional
            乘数因子，用于转换像素值（默认值为 1.0）。
            Scale factor to multiply the raster values (default is 1.0).
        nan_to_zero : bool, optional
            是否将 NaN 值替换为 0 并视为有效像元；否则保留 NaN（默认 True）。
            If True, replace NaN with 0 (treated as valid data); if False, preserve NaN (default True).

        返回 (Returns)
        -------
        region : List[float]
            栅格的空间范围 [xmin, xmax, ymin, ymax]。
            Spatial bounds of the raster in the form [xmin, xmax, ymin, ymax].
        """
        # 1. 打开原始 TIF 并获取边界 / Open source TIF and extract bounds
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
            # 计算空间范围 / Compute spatial bounds
            region = [bounds.left, bounds.right, bounds.bottom, bounds.top]
            print(f"TIF 数据区域 (bounds): {region}") # 打印区域范围 / print bounds

            # 2. 读取第一波段并转换为 float32 / Read first band as float32
            data = src.read(1).astype("float32")

            # 3. 应用缩放因子 / Apply scale factor
            data_scaled = data * scale

            # 4. 准备临时 TIF 的 profile，并根据 nan_to_zero 处理 NaN
            # Prepare profile for temporary output and handle NaN based on flag
            profile = src.profile.copy()
            profile.update(dtype=rasterio.float32)
            if nan_to_zero:
                profile.update(nodata=0)  # 将 0 视为有效数据 / treat 0 as valid data
                data_scaled = np.nan_to_num(data_scaled, nan=0.0)  # 将 NaN 替换为 0 / replace NaN with 0
            else:
                profile.update(nodata=None)  # 保留 NaN （显示为空白）/ preserve NaN as NoData

            temp_tif = "data/temp_scaled.tif"
            # 5. 写出临时 TIF / Write scaled data to temporary TIF
            with rasterio.open(temp_tif, "w", **profile) as dst:
                dst.write(data_scaled, 1)
                print(f"临时 TIF 已保存 (temp TIFF saved): {temp_tif}")

        # 6. 使用 GDAL 转换为 GRD 格式 / Convert temporary TIF to GRD using GDAL
        gdal.Translate(grd_path, temp_tif, format="GSBG")
        print(f"已转换为 GRD 文件 (converted to GRD): {grd_path}")

        # 7. 删除临时文件 / Remove temporary file
        try:
            os.remove(temp_tif)
            print(f"已删除临时文件 (temp file removed): {temp_tif}")
        except OSError as e:
            print(f"删除临时文件时出错 (error deleting temp file): {e}")

        return region

    def load_txt_to_grd(
        self, 
        txt_path: str, 
        grd_path: str, 
        scale: float = 1.0
    ) -> List[float]:
        """
        加载 TXT 文件，应用缩放因子，并转换为 GRD 格式。
        Load a TXT file, apply a scale factor to the third column, and convert it to a GRD file.

        参数 (Parameters)
        ----------
        txt_path : str
            原始 TXT 文件路径，要求包含 'lon' 和 'lat' 表头列。
            Path to the source TXT file. Requires a header with 'lon' and 'lat' columns.
        grd_path : str
            输出 GRD 文件路径。
            Path where the output GRD file will be saved.
        scale : float, optional
            乘数因子，用于转换第三列数据的单位（默认值为 1.0）。
            Scale factor to multiply the third column values (default is 1.0).

        返回 (Returns)
        -------
        region : List[float]
            数据范围 [xmin, xmax, ymin, ymax]。
            Spatial bounds of the data in the form [xmin, xmax, ymin, ymax].
        """
        # 1. 读取 TXT 数据，要求包含 'lon'、'lat' 和第三列数据
        # Read TXT data with 'lon', 'lat', and a third value column
        df = pd.read_csv(txt_path, sep=r'\s+')

        # 2. 单位转换：对第三列数据乘以 scale
        # Apply scale factor to the third column
        df.iloc[:, 2] = df.iloc[:, 2] * scale

        # 3. 计算空间范围
        # Compute spatial bounds
        region = [df["lon"].min(), df["lon"].max(), df["lat"].min(), df["lat"].max()]
        print(f"TXT 数据区域 (bounds): {region}")

        # 4. 使用 pygmt 将散点数据转换为 GRD
        # Convert scatter data to GRD using pygmt.xyz2grd
        pygmt.xyz2grd(
            data=df,
            region=region,
            spacing="0.0025",  # 网格分辨率，单位为度
            outgrid=grd_path
        )
        print(f"TXT 转换为 GRD 完成 (converted to GRD): {grd_path}")

        return region

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
    
    def add_tifs(tif1, tif2, out_tif, mode):
        """
        tif1, tif2: 输入两幅 GeoTIFF 路径
        out_tif: 输出路径
        mode: "any" 或 "all"
        - "any": 只要一方是 nodata 就掩 (mask = nan1 | nan2)
        - "all": 只有两方都是 nodata 才掩 (mask = nan1 & nan2)
        """
        with rasterio.open(tif1) as src1, rasterio.open(tif2) as src2:
            meta = src1.meta.copy()
            nd1 = src1.nodata
            nd2 = src2.nodata

            arr1 = src1.read(1).astype("float32")
            arr2 = src2.read(1).astype("float32")

        # 把 nodata 标记成 NaN
        if nd1 is not None:
            arr1[arr1 == nd1] = np.nan
        if nd2 is not None:
            arr2[arr2 == nd2] = np.nan

        # 构造掩膜
        nan1 = np.isnan(arr1)
        nan2 = np.isnan(arr2)
        if mode == "any":
            mask = nan1 | nan2
        elif mode == "all":
            mask = nan1 & nan2
        else:
            raise ValueError("mode must be 'any' or 'all'")

        # 相加，然后再掩膜
        sum_arr = arr1 + arr2
        sum_arr[mask] = np.nan

        # 写出
        meta.update(dtype="float32", nodata=np.nan)
        with rasterio.open(out_tif, "w", **meta) as dst:
            dst.write(sum_arr, 1)

if __name__ == "__main__":
    # 测试示例（可根据实际文件路径测试）
    extractor = ProfileExtractor()
    
    # 示例 TIF 数据转换
    tif_path = "data/S1_AS.tif"     # 替换为实际 TIF 文件路径
    grd_tif = "data/S1_AS.grd"
    region_tif = extractor.load_tif_to_grd(tif_path, grd_tif)
    
    # 示例 TXT 数据转换
    txt_path = "data/ALOS2_AS.txt"  # 替换为实际 TXT 文件路径
    grd_txt = "data/ALOS2_AS.grd"
    region_txt, df_txt = extractor.load_txt_to_grd(txt_path, grd_txt)
    
    # 示例剖线轨迹：从 (13.0, 42.7) 到 (13.4, 42.9)
    num_points = 100
    lons = np.linspace(13.0, 13.4, num_points)
    lats = np.linspace(42.7, 42.9, num_points)
    track = np.column_stack((lons, lats))
    
    profile = extractor.extract_profile(grd_tif, track)
    print("剖面数据预览:")
    print(profile.head())

    # 示例 TIF 影像相加
    add_tifs("S1_AS_Norcia.tif", "S1_AS_Visso.tif", "S1_AS_Add.tif", mode="any")
    add_tifs("S1_AS_Norcia.tif", "S1_AS_Visso.tif", "S1_AS_Add.tif", mode="all")
    with rasterio.open("S1_AS_Add.tif") as src:
        arr = src.read(1).astype(">f4")    # 读一波段并转为 大端float32

    # 如果原来有 nodata，还可 data[arr == src.nodata] = np.nan
    # 直接写出最纯二进制流（按行连续、无 header）
    arr.tofile("/media/user/新加卷1/20241205_IGEO_paper1/S1Reault_draw/ascending/Norcia_as/1/mean_v_dinsar.utm")