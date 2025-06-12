# profile_extractor.py
import pandas as pd
import numpy as np
import pygmt
from pyproj import Geod
import rasterio
from osgeo import gdal


class ProfileExtractor:
    def __init__(self):
        pass

    def load_tif_to_grd(self, tif_path, grd_path, scale):
        """
        读取 TIF 文件，利用 rasterio 读取数据后直接对数值乘以 scale，
        保存为一个新的临时 TIF 文件，再利用 pygmt.grdcut 将该临时 TIF 转换为 GRD 文件。
        
        参数:
        tif_path: 原始 TIF 文件路径。
        grd_path: 输出的 GRD 文件路径。
        scale: 数值转换因子（默认为1）。
        
        返回:
        region: 区域范围 [xmin, xmax, ymin, ymax]。
        """
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
            region = [bounds.left, bounds.right, bounds.bottom, bounds.top]
            print("TIF 数据区域:", region)

            data = src.read(1).astype("float32")

            # 转换单位
            data_scaled = data * scale

            # 写入一个临时 TIF 文件（你可以指定一个临时文件路径）
            temp_tif = "temp_scaled.tif"
            profile = src.profile
            # 把原本的 nodata 像元替换为 0 后，不再把 0 当作 nodata，这样 0 会正常显示
            # profile.update(dtype=rasterio.float32, nodata=None)
            # 如果你反过来写 nodata=0，则所有等于 0 的像元又会被当作无数据（空白）显示
            profile.update(dtype=rasterio.float32, nodata=0)

            with rasterio.open(temp_tif, "w", **profile) as dst:
                dst.write(data_scaled.astype(rasterio.float32), 1)
                print("临时 TIF 文件已生成:", temp_tif)
        
        # 将临时 TIF 转换为 GRD 文件
        gdal.Translate(grd_path, temp_tif, format='GSBG')
        print("TIF 转换为 GRD 完成:", grd_path)

    def load_txt_to_grd(self, txt_path, grd_path, scale):
        """
        读取 TXT 数据（要求有表头且包含 'lon' 和 'lat' 列），对第三列数据乘以scale（单位转换），
        计算区域范围，并使用 pygmt.surface 将散点数据转换为 GRD 文件。
        返回一个元组：(region, df)。
        """
        df = pd.read_csv(txt_path, sep=r'\s+')

        # 单位转换
        df.iloc[:, 2] = df.iloc[:, 2] * scale
        
        region = [df["lon"].min(), df["lon"].max(), df["lat"].min(), df["lat"].max()]
        print("TXT 数据区域:", region)
        pygmt.xyz2grd(
            data=df, 
            region=region,
            spacing="0.0025",  # 设置网格间隔，单位为度
            outgrid=grd_path
        )
        print("TXT 转换为 GRD 完成:", grd_path)
        return region, df

    def extract_profile(self, grd_file, track, newcolname="z"):
        """
        根据 GRD 文件和给定的剖线轨迹（二维 NumPy 数组，每行 [lon, lat]）提取剖面数据，
        并计算沿轨迹的累计距离（单位：米）。
        返回的 DataFrame 包含 "lon", "lat", newcolname（例如 "z"）以及 "distance" 列。
        """
        profile = pygmt.grdtrack(points=track, grid=grd_file, newcolname=newcolname)
        # 如果 DataFrame 没有自动赋予列名，则手动重命名（假设顺序为 lon, lat, z）
        if not all(isinstance(col, str) for col in profile.columns):
            profile.columns = ["lon", "lat", newcolname]
        # 计算累计距离
        geod = Geod(ellps="WGS84")
        distances = [0]
        for i in range(1, len(profile)):
            lon_prev, lat_prev = profile["lon"].iloc[i-1], profile["lat"].iloc[i-1]
            lon_curr, lat_curr = profile["lon"].iloc[i], profile["lat"].iloc[i]
            _, _, d = geod.inv(lon_prev, lat_prev, lon_curr, lat_curr)
            distances.append(distances[-1] + d)
        profile["distance"] = distances
        return profile

if __name__ == "__main__":
    # 测试示例（可根据实际文件路径测试）
    extractor = ProfileExtractor()
    
    # 示例 TIF 数据转换
    tif_path = "S1_AS.tif"       # 替换为实际 TIF 文件路径
    grd_tif = "S1_AS.grd"
    region_tif = extractor.load_tif_to_grd(tif_path, grd_tif)
    
    # 示例 TXT 数据转换
    txt_path = "ALOS2_AS.tif.xyz"  # 替换为实际 TXT 文件路径
    grd_txt = "ALOS2_AS.grd"
    region_txt, df_txt = extractor.load_txt_to_grd(txt_path, grd_txt)
    
    # 示例剖线轨迹：从 (13.0, 42.7) 到 (13.4, 42.9)
    num_points = 100
    lons = np.linspace(13.0, 13.4, num_points)
    lats = np.linspace(42.7, 42.9, num_points)
    track = np.column_stack((lons, lats))
    
    profile = extractor.extract_profile(grd_tif, track)
    print("剖面数据预览:")
    print(profile.head())
