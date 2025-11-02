# -*- coding: utf-8 -*-
"""
Author: Yilun Tan csuyiluntan@gmail.com yiluntan@qq.com
Affiliation: SIGM@3-D Laboratory, School of Geosciences and Information Physics, Central South University
作者：谭逸伦 csuyiluntan@gmail.com yiluntan@qq.com
单位：中南大学地球科学与信息物理学院 SIGM@-3D 实验室

Created: 2025-09-11
创建日期：2025-09-11

Summary: This class is a thin wrapper around PyGMT; it draws a figure via chainable (fluent) calls and saves the output.
摘要：该类为封装的一个 PyGMT 绘图器，通过链式调用完成一张图的绘制与保存。

"""

from typing import List, Tuple, Dict, Sequence, Optional
import os
import re
import pygmt
import rasterio
import numpy as np
import pandas as pd
from osgeo import gdal
from pyproj import Geod

# 默认基础绘图参数
DEFAULTS = dict(
    FONT_TITLE="20p,Helvetica-Bold",
    FONT_ANNOT_PRIMARY="12p,Helvetica-Bold",
    FONT_LABEL="20p,Helvetica-Bold",
)


class PyGMTPlotter:
    """
    基于 pygmt 的绘图器，初始化设置为 Figure 对象与默认绘图参数 config 。

    参数 (Parameters)
    ----------
    defaults : dict, optional
        初始化时用于覆盖默认绘图参数的字典（键为 GMT 配置项，如 FONT_TITLE 等）。
        若为 None，则使用原有的默认 DEFAULTS 的备份 。

    属性 (Attributes)
    ----------
    fig : pygmt.Figure or None
        当前绘图对象。调用 new() 前为 None，new() 后为有效对象。
    _base_defaults : dict
        默认样式的副本，用于 reset_defaults() 恢复到初始参数设置。
    defaults : dict
        当前实例的可修改默认样式；new() 时会一次性应用到 GMT 会话。
    """

    def __init__(self, defaults: dict | None = None):
        self.fig = None
        self._base_defaults = DEFAULTS.copy()
        self.defaults = (defaults or self._base_defaults).copy()

    # ------------------------- 默认绘图参数更新方法 -------------------------

    def new(self) -> "PyGMTPlotter":
        """
        开始一张“全新”的图：新建 Figure 并应用当前默认样式到 GMT 会话。
        Start a new figure and apply current defaults to the GMT session.

        步骤 (What it does)
        -------------------
        1) self.fig = pygmt.Figure()
        2) pygmt.config(**self.defaults) 一次性写入当前默认样式（字体等）

        注意 (Notes)
        ------------
        - 想让 set_defaults() 的修改生效，需在下一次绘图前调用 new()。
        - 建议每张图都先调用一次 new() 以确保样式可控、可复现。

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        self.fig = pygmt.Figure()
        pygmt.config(**self.defaults)
        return self

    def set_defaults(self, **kwargs) -> "PyGMTPlotter":
        """
        更新当前实例的默认样式（不会立刻影响已开启的图，会在下一次 new() 生效）。
        Update defaults for this instance; will take effect on next `new()`.

        参数 (Parameters)
        ----------
        **kwargs :
            形如 FONT_TITLE="24p,Helvetica-Bold" 等 GMT 配置项键值。

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        self.defaults.update(kwargs)
        return self

    def reset_defaults(self) -> "PyGMTPlotter":
        """
        将当前实例的绘图默认参数恢复为原始设置。
        Reset this instance's defaults back to baseline.

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        self.defaults = self._base_defaults.copy()
        return self

    def save(self, output_file: str) -> "PyGMTPlotter":
        """
        保存当前图像到文件。
        Save current figure to file.

        参数 (Parameters)
        ----------
        output_file : str
            输出文件路径（例如 "SBAS_AllRegion.png"）。
            Output file path (e.g., "SBAS_AllRegion.png").

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        assert self.fig is not None, "请先调用 new() 并完成绘制后再保存"
        self.fig.savefig(output_file)
        print(f"图像已保存：{output_file}")
        return self

    # ------------------------- 预处理与实用工具方法 -------------------------

    @staticmethod
    def region_from_grd(grid_path: str) -> List[float]:
        """
        从栅格文件中解析出区域范围 region = [xmin, xmax, ymin, ymax]。
        Parse region [xmin, xmax, ymin, ymax] from a grid via pygmt.grdinfo.

        参数 (Parameters)
        ----------
        grid_path : str
            栅格文件路径，传入给 pygmt.grdinfo 进行解析。
            Path to grid file for pygmt.grdinfo.

        返回 (Returns)
        -------
        region : List[float]
            形如 [xmin, xmax, ymin, ymax] 的列表。
            Region as [xmin, xmax, ymin, ymax].

        异常 (Raises)
        -------------
        ValueError
            当无法从 grdinfo 输出中解析到坐标范围时抛出。
        """
        info_text = pygmt.grdinfo(grid=grid_path)
        x_match = re.search(r"x_min:\s*([\d\.-]+)\s+x_max:\s*([\d\.-]+)", info_text)
        y_match = re.search(r"y_min:\s*([\d\.-]+)\s+y_max:\s*([\d\.-]+)", info_text)
        if x_match and y_match:
            return [
                float(x_match.group(1)),
                float(x_match.group(2)),
                float(y_match.group(1)),
                float(y_match.group(2)),
            ]
        raise ValueError("无法解析区域范围信息")

    @staticmethod
    def tif2grd(
        tif_path: str,
        grd_path: str,
        scale: float = 1.0,
        nan_to_zero: bool = True,
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
        # 1) 打开 TIF，读取范围与数据
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
            region = [bounds.left, bounds.right, bounds.bottom, bounds.top]
            data = src.read(1).astype("float32")

            # 2) 缩放
            data_scaled = data * scale

            # 3) 写临时 TIF（按需处理 NaN）
            profile = src.profile.copy()
            profile.update(dtype=rasterio.float32)
            if nan_to_zero:
                profile.update(nodata=0)
                data_scaled = np.nan_to_num(data_scaled, nan=0.0)
            else:
                profile.update(nodata=None)

        temp_tif = "temp_scaled.tif"
        with rasterio.open(temp_tif, "w", **profile) as dst:
            dst.write(data_scaled, 1)
            print(f"临时 TIF 已保存: {temp_tif}")

        # 4) 转 GRD (GSBG)
        gdal.Translate(grd_path, temp_tif, format="GSBG")
        print(f"已转换为 GRD: {grd_path}")

        # 5) 清理临时文件
        try:
            os.remove(temp_tif)
            print(f"已删除临时文件: {temp_tif}")
        except OSError as e:
            print(f"删除临时文件时出错: {e}")

        return region

    @staticmethod
    def txt2grd(
        txt_path: str,
        grd_path: str,
        scale: float = 1.0,
        space: float = 0.0005,
    ) -> List[float]:
        """
        加载 TXT 文件，应用缩放因子，并转换为 GRD 格式。
        Load a TXT file, apply a scale factor to the third column, and convert it to a GRD file.

        参数 (Parameters)
        ----------
        txt_path : str
            原始 TXT 文件路径，要求包含 'lon' 和 'lat' 表头列。
            Path to the source TXT file. Requires header with 'lon' and 'lat'.
        grd_path : str
            输出 GRD 文件路径。
            Path where the output GRD file will be saved.
        scale : float, optional
            乘数因子，用于转换第三列数据的单位（默认值为 1.0）。
            Scale factor to multiply the third column values (default is 1.0).
        space : float, optional
            生成网格的空间分辨率（度）。
            Grid spacing in degrees (default 0.0005).

        返回 (Returns)
        -------
        region : List[float]
            数据范围 [xmin, xmax, ymin, ymax]。
            Spatial bounds of the data as [xmin, xmax, ymin, ymax].
        """
        # 1) 读入文本（假设空白分隔，且表头含 lon/lat）
        df = pd.read_csv(txt_path, sep=r"\s+")
        # 2) 第三列按比例缩放
        df.iloc[:, 2] = df.iloc[:, 2] * scale
        # 3) 计算范围
        region = [df["lon"].min(), df["lon"].max(), df["lat"].min(), df["lat"].max()]
        print(f"TXT 数据区域: {region}")
        # 4) 散点转栅格
        pygmt.xyz2grd(
            data=df,
            region=region,
            spacing=space,
            outgrid=grd_path,
        )
        print(f"TXT 转换为 GRD 完成: {grd_path}")
        return region
    
    @staticmethod
    def generate_tracks(
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
    
    @staticmethod
    def extract_profile(
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

    # ------------------------- 绘图步骤方法（无返回值） -------------------------

    def draw_geo_basemap(
        self,
        region: List[float],
        projection: str,
        title: str,
    ) -> "PyGMTPlotter":
        """
        绘制底图框（花式边框 + 三等分轴注 + 标题）。
        Draw map frame with fancy border, 3-part ticks, and title.

        参数 (Parameters)
        ----------
        region : List[float]
            地图区域范围 [xmin, xmax, ymin, ymax]。
        projection : str
            投影字符串，例如 "M8i"（墨卡托，宽 8 英寸）。
        title : str
            图幅标题，将显示在图上方。

        返回 (Returns)
        -------
        None
        """
        factor = 3
        x_stride = round((region[1] - region[0]) / factor, 4)
        y_stride = round((region[3] - region[2]) / factor, 4)
        x_anno = f"a{x_stride}fg"
        y_anno = f"a{y_stride}fg"
        with pygmt.config(
            MAP_FRAME_TYPE="fancy",
            MAP_FRAME_WIDTH="6p",
            FONT_ANNOT="18p,Helvetica-Bold",
            MAP_FRAME_PEN="3p",
            MAP_TICK_PEN="3p",
            FORMAT_GEO_MAP="ddd:mm:ss",
        ):
            self.fig.basemap(
                region=region,
                projection=projection,
                frame=[f"x{x_anno}", f"y{y_anno}", f"+t{title}"],
            )

        return self

    def draw_dem(
        self,
        dem_tif: str,
        region: List[float],
        projection: str,
        cpt: str = "gray",
        bar_min: float = 700,
        bar_max: float = 2500,
        dem_grd: str = "DEM.grd",
        demgradient_grd: str = "DEMgradiant.grd",
    ) -> "PyGMTPlotter":
        """
        绘制 DEM 灰度底图并叠加阴影（hillshade）。
        Render DEM in grayscale with hillshade.

        参数 (Parameters)
        ----------
        dem_tif : str
            DEM 的 GeoTIFF 文件路径。
        region : List[float]
            地图区域范围 [xmin, xmax, ymin, ymax]。
        projection : str
            投影字符串，例如 "M8i"。
        dem_grd : str, optional
            中间产物：DEM 的 GSBG（GMT grid）路径，不存在时自动生成。
        demgradient_grd : str, optional
            中间产物：DEM 阴影（梯度）GSBG 路径，不存在时自动生成。

        返回 (Returns)
        -------
        None
        """
        if not os.path.exists(demgradient_grd):
            if not os.path.exists(dem_grd):
                gdal.Translate(dem_grd, dem_tif, format="GSBG")
            pygmt.grdgradient(grid=dem_grd, outgrid=demgradient_grd, azimuth=0)

        pygmt.makecpt(
            cmap=cpt,
            series=[bar_min, bar_max],
            background=True,
            reverse=True,
        )
        self.fig.grdimage(
            grid=dem_grd,
            region=region,
            projection=projection,
            cmap=True,
            shading=demgradient_grd,
        )

        return self
    
    def draw_optic(
        self,
        optic_tif: str,
        region: List[float],
        projection: str,
        transparency: int = 0,
    ) -> "PyGMTPlotter":
        """
        绘制光学（影像）底图（直接使用 GeoTIFF / RGB 文件，无需转换为 GRD）。
        Render an optical/raster basemap directly from a GeoTIFF/RGB file (no GRD conversion).

        参数 (Parameters)
        ----------
        optic_tif : str
            光学影像文件路径（GeoTIFF 或其他 GDAL 可识别的影像，支持多波段 RGB）。
            Path to the optical image (GeoTIFF or any GDAL-readable raster, including RGB).
        region : List[float]
            地图区域范围 [xmin, xmax, ymin, ymax]。
        projection : str
            投影字符串，例如 "M8i"。
        transparency : int, optional
            图层整体透明度（0=不透明，100=完全透明），默认 0。
            Layer transparency (0..100).

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        try:
            # 直接绘制影像；不指定 cmap，保留原始色彩；NaN/NoData 透明可见底图
            self.fig.grdimage(
                grid=optic_tif,
                region=region,
                projection=projection,
                nan_transparent=True,
                transparency=transparency,
            )
        except Exception as e:
            raise RuntimeError(f"使用 pygmt 绘制光学影像时出错: {e}")

        return self


    def draw_defo_grd(
        self,
        data_grd: str,
        cpt: str,
        region: List[float],
        projection: str,
        bar_min: float = -0.06,
        bar_max: float = 0.06,
        alpha: int = 25,
    ) -> "PyGMTPlotter":
        """
        绘制形变量网格（外部 CPT + 指定数值范围 + NaN 透明 + 整层透明度）。
        Render deformation grid using external CPT; map to [bar_min, bar_max]; NaN transparent.

        参数 (Parameters)
        ----------
        data_grd : str
            形变量网格（GRD/GSBG/GeoTIFF 等 GMT 可识别）路径。
        cpt : str
            外部 CPT 文件路径（保留原配色，只做数值映射）。
        region : List[float]
            地图区域范围 [xmin, xmax, ymin, ymax]。
        projection : str
            投影字符串，例如 "M8i"。
        bar_min : float, optional
            颜色映射下界。
        bar_max : float, optional
            颜色映射上界。
        alpha : int, optional
            网格整层透明度（0=不透明，100=完全透明）。

        返回 (Returns)
        -------
        None
        """
        pygmt.makecpt(
            cmap=cpt,
            series=[bar_min, bar_max],
            background=True,
            reverse=True,
        )
        self.fig.grdimage(
            grid=data_grd,
            region=region,
            projection=projection,
            cmap=True,
            nan_transparent=True,
            transparency=alpha,
        )

        return self
    
    def draw_defo_scatter(
        self,
        data_grd: str,
        cpt: str,
        region: List[float],
        projection: str,
        bar_min: float = -0.06,
        bar_max: float = 0.06,
        style: str = "c0.08c",
        pen: str = "0.01p,white",
        transparency: int = 0,
    ) -> "PyGMTPlotter":
        """
        基于栅格直接绘制散点形变图（输入为 GRD/GeoTIFF 等 GMT 可读栅格）。
        Render deformation as colored scatter points directly from a grid (GRD/GeoTIFF).

        参数 (Parameters)
        ----------
        data_grd : str
            单波段形变栅格（GRD/GeoTIFF/NetCDF 等 GMT 可读）。
        cpt : str
            外部 CPT 文件路径（用作颜色映射）。
        region : List[float]
            地图范围 [xmin, xmax, ymin, ymax]。
        projection : str
            投影字符串，例如 "M8i"。
        bar_min, bar_max : float
            颜色映射范围，与 draw_deformation 一致。
        style : str
            点样式（默认 "c0.08c"）。
        pen : str
            点边框画笔（默认 "0.25p,black"）。
        transparency : int
            图层透明度（0=不透明，100=完全透明）。

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        # 1) 栅格转散点 (x, y, z)，直接在内存中完成
        df = pygmt.grd2xyz(grid=data_grd, region=region, output_type="pandas").dropna()

        # 2) 颜色表（与 draw_deformation 保持一致）
        pygmt.makecpt(
            cmap=cpt,
            series=[bar_min, bar_max],
            background=True,
            #reverse=True,
        )

        # 3) 绘制散点（以 z 作为颜色值）
        self.fig.plot(
            data=df,
            region=region,
            projection=projection,
            style=style,
            #pen=pen,
            cmap=True,
            transparency=transparency,
        )

        return self


    def add_colorbar(self) -> "PyGMTPlotter":
        """
        添加颜色条（底部居中 + 下移；白底 + 边框 + 内边距）。
        Add colorbar at bottom center with outward offset, white background & padding.

        参数 (Parameters)
        ----------
        None

        返回 (Returns)
        -------
        None
        """
        with pygmt.config(
            FONT_ANNOT_PRIMARY="20p",
            FONT_ANNOT_SECONDARY="24p, Helvetica-Bold",
        ):
            self.fig.colorbar(
                cmap=True,
                position="JBC+o0c/4c+w12c/0.6c+h",
                frame=["xa0.05f0.025+lDeformation", "y+lm/yr"],
                box="F+gWHITE+p2p+c20p/20p",
            )

        return self

    def add_scale(
        self,
        region: List[float],
        projection: str,
    ) -> "PyGMTPlotter":
        """
        添加比例尺（上方居中 + 上移；白底 + 边框 + 内边距）。
        Add map scale at top center with outward offset.

        参数 (Parameters)
        ----------
        region : List[float]
            地图区域范围 [xmin, xmax, ymin, ymax]。
        projection : str
            投影字符串，例如 "M8i"。

        返回 (Returns)
        -------
        None
        """
        with pygmt.config(MAP_SCALE_HEIGHT="20p", FONT_ANNOT_PRIMARY="20p"):
            self.fig.basemap(
                region=region,
                projection=projection,
                map_scale="JTC+o0c/4c+w10k+f+u",
                box="F+gWHITE+p2p+c20p/20p",
            )
        
        return self

    def add_rose(
        self,
        region: List[float],
        projection: str,
    ) -> "PyGMTPlotter":
        """
        添加玫瑰图/指北针（右侧居中 + 右移；白底 + 边框 + 内边距）。
        Add compass rose at right middle with outward offset.

        参数 (Parameters)
        ----------
        region : List[float]
            地图区域范围 [xmin, xmax, ymin, ymax]。
        projection : str
            投影字符串，例如 "M8i"。

        返回 (Returns)
        -------
        None
        """
        self.fig.basemap(
            region=region,
            projection=projection,
            rose="JMR+jCM+o10c/0c+w5c+l+f1",
            box="F+gwhite+p2p+c1.5c",
        )

        return self
    
    def draw_profile_tracks(
        self,
        tracks: Dict[str, Sequence[Sequence[float]]],
        line_pen: str = "2p,black",
        start_label_font: str = "20p,Helvetica-Bold",
        end_label_font: str | None = None,
        start_justify: str = "BR",
        end_justify: str = "BL",
        end_suffix: str = "'",
    ) -> "PyGMTPlotter":
        """
        绘制多条剖面轨迹，并在每条轨迹的起点/终点加注记。
        Plot multiple profile tracks and label start/end points.

        参数 (Parameters)
        ----------
        tracks : Dict[str, Sequence[Sequence[float]]]
            键为注记名（如 "A"），值为二维序列/数组（每行 [lon, lat]，顺序：起点→终点）。
        line_pen : str, optional
            轨迹线型（GMT pen 字符串），默认 "2p,black"。
        start_label_font : str, optional
            起点注记字体（默认 "20p,Helvetica-Bold"）。
        end_label_font : str or None, optional
            终点注记字体；为 None 时与起点相同。
        start_justify : str, optional
            起点注记对齐方式（默认 "BR"）。
        end_justify : str, optional
            终点注记对齐方式（默认 "BL"）。
        end_suffix : str, optional
            终点注记后缀（默认在字母后加撇号 "'").

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        if end_label_font is None:
            end_label_font = start_label_font

        for name, track in tracks.items():
            arr = np.asarray(track, dtype=float)
            # 轨迹线
            self.fig.plot(x=arr[:, 0], y=arr[:, 1], pen=line_pen)
            # 起点注记
            self.fig.text(
                x=[arr[0, 0]], y=[arr[0, 1]],
                text=name, font=start_label_font, justify=start_justify
            )
            # 终点注记
            self.fig.text(
                x=[arr[-1, 0]], y=[arr[-1, 1]],
                text=name + end_suffix, font=end_label_font, justify=end_justify
            )
        return self

    def add_marker(
        self,
        lon: float,
        lat: float,
        style: str = "a16p",
        pen: str = "2p,black",
        fill: str | None = None,
    ) -> "PyGMTPlotter":
        """
        绘制单个标记点（可多次调用叠加多个点）。
        Plot a single marker. Call repeatedly to add multiple points.

        参数 (Parameters)
        ----------
        lon : float
            经度（x）。
        lat : float
            纬度（y）。
        style : str, optional
            GMT 点样式（默认 "a16p" 星形，大小 16p）。
        pen : str, optional
            标记边框画笔（默认 "2p,black"）。
        fill : str or None, optional
            填充色（如 "red"）。None 表示不显式指定填充。

        返回 (Returns)
        -------
        self : PyGMTPlotter
            支持链式调用。
        """
        kwargs = dict(x=[float(lon)], y=[float(lat)], style=style, pen=pen)
        if fill is not None:
            kwargs["fill"] = fill
        self.fig.plot(**kwargs)
        return self
    
    def draw_math_basemap(
        self,
        profiles: 'pd.DataFrame | Sequence[pd.DataFrame]',
        title: str = "Profile_Curve",
        x_label: str = "Distance (m)",
        y_label: str = "Deformation (m)",
        padding: float = 0.1,
    )-> "PyGMTPlotter":
        """
        初始化剖面坐标轴：根据单个或多个剖面数据自动计算绘图范围，并绘制坐标框架。
        - 横坐标为累计距离（列名 "distance"）
        - 纵坐标为剖面数值（列名 "z"）

        参数:
        profiles_or_single: 单个 DataFrame（含 "distance"/"z"）或 DataFrame 列表/元组
        title: 图形标题
        x_label: 横轴标题（默认 "Distance (m)"）
        y_label: 纵轴标题（默认 "Deformation (m)"）
        padding: 纵轴上下边距比例（默认 0.1）

        返回:
        self（支持链式调用）
        """
        if isinstance(profiles, (list, tuple)):
            profiles = profiles
        else:
            profiles = [profiles]

        x_min = min(p["distance"].min() for p in profiles)
        x_max = max(p["distance"].max() for p in profiles)
        y_min = min(p["z"].min() for p in profiles)
        y_max = max(p["z"].max() for p in profiles)

        if x_max == x_min:
            x_min -= 1.0; x_max += 1.0
        if y_max == y_min:
            y_min -= 1.0; y_max += 1.0

        y_gap = (y_max - y_min) * float(padding)
        y_min -= y_gap; y_max += y_gap

        self.fig.basemap(
            region=[x_min, x_max, y_min, y_max],
            frame=[f"xaf+l{x_label}", f"yaf+l{y_label}", f"+t{title}"]
        )
        return self


    def draw_line_2d(
        self,
        profile: 'pd.DataFrame',
        label: str,
        pen: str = "2p,blue",
    ) -> "PyGMTPlotter":    

        """
        在当前剖面坐标轴上添加一条折线剖面。

        参数:
        profile: DataFrame，包含 "distance" 和 "z" 两列
        label: 图例标签
        pen: 线型（默认 "2p,blue"）

        返回:
        self（支持链式调用）
        """
        self.fig.plot(x=profile["distance"], y=profile["z"], pen=pen, label=label)
        return self


    def draw_scatter_2d(
        self,
        profile: 'pd.DataFrame',
        label: str,
        style: str = "c0.4c",
        fill: Optional[str] = None,
        pen: str = "0p",
        transparency: int = 60,
        alpha: Optional[int] = None,
    ) -> "PyGMTPlotter":
        """
        在当前剖面坐标轴上添加一条散点剖面。

        参数:
        profile: DataFrame，包含 "distance" 和 "z" 两列
        label: 图例标签
        style: 点样式（默认 "c0.4c" 圆点 0.4cm）
        fill: 填充色（如 "blue"）；None 表示不显式指定
        pen: 点边框画笔（默认 "0p"）
        transparency: 透明度 0~100（默认 60）
        alpha: 透明度别名；若给定，则覆盖 transparency

        返回:
        self（支持链式调用）
        """
        if alpha is not None:
            transparency = alpha
        kw = dict(x=profile["distance"], y=profile["z"],
                style=style, pen=pen, transparency=transparency, label=label)
        if fill is not None:
            kw["fill"] = fill
        self.fig.plot(**kw)
        return self
    
    def add_legend(
    self,
    position: str = "JTR+o0.5c/-1.2c",
    box: str = "+gwhite+p1.5p",
    ) -> "PyGMTPlotter":
        """
        添加剖面图例。

        参数:
        position: 图例位置与偏移，默认 "JTR+o0.2c/-1.2c"
        box: 图例面板样式（白底+边框），默认 "+gwhite+p1.2p"

        返回:
        self（支持链式调用）
        """
        self.fig.legend(position=position, box=box)
        return self

