# main.py
import numpy as np
import rasterio
from profile_extractor import ProfileExtractor
from profile_plotter import ProfilePlotter

def main():

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

    # # 使用示例
    # #add_tifs("S1_AS_Norcia.tif", "S1_AS_Visso.tif", "S1_AS_Add.tif", mode="any")
    # add_tifs("S1_AS_Norcia.tif", "S1_AS_Visso.tif", "S1_AS_Add.tif", mode="all")
    # with rasterio.open("S1_AS_Add.tif") as src:
    #     arr = src.read(1).astype(">f4")    # 读一波段并转为 大端float32

    # # 如果原来有 nodata，还可 data[arr == src.nodata] = np.nan

    # # 直接写出最纯二进制流（按行连续、无 header）
    # arr.tofile("/media/user/新加卷1/20241205_IGEO_paper1/S1Reault_draw/ascending/Norcia_as/1/mean_v_dinsar.utm")


    # 初始化剖面提取器
    extractor = ProfileExtractor()
    
    # ----------------------------
    # 1. 数据加载与转换
    # ----------------------------
    # TIF 数据转换：读取 TIF 文件并转换为 GRD 文件
    S1_LOS = "S1_AS_Norcia.tif"
    S1_LOS ="S1_AS_Visso.tif"
    S1_LOS = "S1_AS_All.tif"
    S1_LOS = "S1_AS_Add.tif"
    S1_LOS = "data/S1_AS_Mask.tif"
    S1_LOS_grd = "S1_AS_Norcia.grd"     # 输出 GRD 文件名
    S1_LOS_grd = "S1_AS_Visso.grd"
    S1_LOS_grd = "S1_AS_All.grd"
    S1_LOS_grd = "S1_AS_Add.grd"
    S1_LOS_grd = "data/S1_AS_Mask.grd"
    region = extractor.load_tif_to_grd(S1_LOS, S1_LOS_grd, scale=1)
    
    # TXT 数据转换：读取 TXT 文件并转换为 GRD 文件（单位转换在模块内处理） ``
    ALOS2_LOS = "data/ALOS2_AS.tif.xyz"   # 替换为实际的 TXT 文件路径
    ALOS2_LOS_grd = "data/ALOS2_AS.grd"       # 输出 GRD 文件名（TXT数据）
    region = extractor.load_txt_to_grd(ALOS2_LOS, ALOS2_LOS_grd, scale=0.01)

    # # 读取POT结果
    # S1_POT = "S1_AS_POT.tif"       
    # S1_POT_grd = "S1_AS_POT.grd" 
    # region = extractor.load_tif_to_grd(S1_POT, S1_POT_grd, scale=100)
    
    # ----------------------------
    # 2. 定义剖线轨迹
    # ----------------------------
    # 剖线起点和终点坐标
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
    # 字典存储轨迹采样点数组，键是剖线名称
    tracks = {}
    for name, start, end in zip(pointnames, start_coords, end_coords):
        # 分别对经度和纬度生成等间距采样点
        lons = np.linspace(start[0], end[0], num_points)
        lats = np.linspace(start[1], end[1], num_points)
        # 合并为二维数组，每行 [lon, lat]
        track = np.column_stack((lons, lats))
        tracks[name] = track


    # # ----------------------------
    # # 3. 绘制单条剖面变化图
    # # ----------------------------
    # # 初始化绘图器
    plotter = ProfilePlotter()
    # # 绘制单个剖面图
    # # AA
    # profileAA = extractor.extract_profile(S1_LOS_grd, tracks["A"])
    # plotter.plot_profile(profileAA, output_file="S1_AS_profileAA.png", label="S1", title="Profile Curve Line AA")
    # profileAA = extractor.extract_profile(ALOS2_LOS_grd, tracks["A"])
    # plotter.plot_profile(profileAA, output_file="ALOS2_AS_profileAA.png", label="ALOS2", title="Profile Curve Line AA")
    # # BB
    # profileBB = extractor.extract_profile(S1_LOS_grd, tracks["B"])
    # plotter.plot_profile(profileBB, output_file="S1_AS_profileBB.png", label="S1", title="Profile Curve Line BB")
    # profileBB = extractor.extract_profile(ALOS2_LOS_grd, tracks["B"])
    # plotter.plot_profile(profileBB, output_file="ALOS2_AS_profileBB.png", label="ALOS2", title="Profile Curve Line BB")
    # # CC
    # profileCC = extractor.extract_profile(S1_LOS_grd, tracks["C"])
    # plotter.plot_profile(profileCC, output_file="S1_AS_profileCC.png", label="S1", title="Profile Curve Line CC") 
    # profileCC = extractor.extract_profile(ALOS2_LOS_grd, tracks["C"])
    # plotter.plot_profile(profileCC, output_file="ALOS2_AS_profileCC.png", label="ALOS2", title="Profile Curve Line CC")
    # # DD
    # profileDD = extractor.extract_profile(S1_LOS_grd, tracks["D"])
    # plotter.plot_profile(profileDD, output_file="S1_AS_profileDD.png", label="S1" ,title="Profile Curve Line DD") 
    # profileDD = extractor.extract_profile(ALOS2_LOS_grd, tracks["D"])
    # plotter.plot_profile(profileDD, output_file="ALOS2_AS_profileDD.png", label="ALOS2", title="Profile Curve Line DD")
    
    # ----------------------------
    # 4. 绘制同一条剖线在不同形变结果上面的对比变化图
    # ----------------------------
    # # 绘制多条剖面对比图
    # grd_files = ["S1_AS.grd", "ALOS2_AS.grd", "S1_AS_POT.grd"]
    # grd_files = [ S1_LOS_grd, ALOS2_LOS_grd ]
    # profiles_AA = []
    # profiles_BB = []
    # profiles_CC = []
    # profiles_DD = []
    # for grd_file in grd_files:
    #     profile_AA = extractor.extract_profile(grd_file, tracks["A"])
    #     profile_BB = extractor.extract_profile(grd_file, tracks["B"])
    #     profile_CC = extractor.extract_profile(grd_file, tracks["C"])
    #     profile_DD = extractor.extract_profile(grd_file, tracks["D"])   
    #     profiles_AA.append(profile_AA)
    #     profiles_BB.append(profile_BB)
    #     profiles_CC.append(profile_CC)
    #     profiles_DD.append(profile_DD)
    
    # # 定义每个剖面的图例标签
    # labels = ["S1", "ALOS2"]
    # # 绘制多条剖面对比图
    # output_filesAA=["S1_ALOS2_profileAA.png","S1_ALOS2_profileAA_scatter.png"]
    # plotter.plot_multiple_profiles(profiles=profiles_AA, labels=labels, output_files=output_filesAA, title="S1_ALOS2_profileAA")
    # output_filesBB=["S1_ALOS2_profileBB.png","S1_ALOS2_profileBB_scatter.png"]
    # plotter.plot_multiple_profiles(profiles=profiles_BB, labels=labels, output_files=output_filesBB, title="S1_ALOS2_profileBB")
    # output_filesCC=["S1_ALOS2_profileCC.png","S1_ALOS2_profileCC_scatter.png"]
    # plotter.plot_multiple_profiles(profiles=profiles_CC, labels=labels, output_files=output_filesCC, title="S1_ALOS2_profileCC")
    # output_filesDD=["S1_ALOS2_profileDD.png","S1_ALOS2_profileDD_scatter.png"]
    # plotter.plot_multiple_profiles(profiles=profiles_DD, labels=labels, output_files=output_filesDD, title="S1_ALOS2_profileDD")


    # ----------------------------
    # 5. 绘制剖面位置图
    # ---------------------------- 
    dem_tif= "DEM.tif"
    cpt = "seismic.cpt"  
    plotter.plot_basemap_profile(ALOS2_LOS_grd, cpt, dem_tif, tracks, output_file="ALOS2_defo.png", title="Profile Location")
    plotter.plot_basemap_profile(S1_LOS_grd, cpt, dem_tif, tracks, output_file="S1_defo.png", title="Profile Location")

    
if __name__ == "__main__":
    main()
