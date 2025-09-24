
import sys
from pathlib import Path
from profile_extractor import ProfileExtractor

cpt_path = Path(__file__).resolve().parents[1] / "cpt" # 自定义库路径
lib_path = Path(__file__).resolve().parents[1] / "lib" # 自定义库路径

from pygmt_plotter import PyGMTPlotter # 从库中导入绘图类

# ===================== 1) 数据预处理 =========================
# 形变速率数据
tif_s1_as_norcia = "data/S1_AS_Norcia.tif"
txt_alos2_as = "data/ALOS2_AS.txt"
# 转换后的 grd 数据文件
grd_s1_as_norcia = "S1_AS_Norcia.grd"
grd_alos2_as = "ALOS2_AS.grd"
# 提取 grd 数据
region_s1_as_norcia = PyGMTPlotter.load_tif_to_grd(tif_path=tif_s1_as_norcia, grd_path=grd_s1_as_norcia, scale=1)
region_alos2_as  = PyGMTPlotter.load_txt_to_grd(txt_path=txt_alos2_as, grd_path=grd_alos2_as, scale=0.01, space=0.003)


# 定义剖线轨迹
start_coords = [   # 剖线起点和终点坐标
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
extractor = ProfileExtractor()
tracks = extractor.generate_tracks(start_coords=start_coords, end_coords=end_coords, num_points=num_points, pointnames=pointnames)
# 从 grd 提取生成的剖线数据
grd_files = [ grd_s1_as_norcia, grd_alos2_as ]
profiles_AA = []
profiles_BB = []
profiles_CC = []
profiles_DD = []
for grd_file in grd_files:
    profile_AA = extractor.extract_profile(grd_file, tracks["A"])
    profile_BB = extractor.extract_profile(grd_file, tracks["B"])
    profile_CC = extractor.extract_profile(grd_file, tracks["C"])
    profile_DD = extractor.extract_profile(grd_file, tracks["D"])   
    profiles_AA.append(profile_AA)
    profiles_BB.append(profile_BB)
    profiles_CC.append(profile_CC)
    profiles_DD.append(profile_DD)

# 打印生成的剖线轨迹
print("剖面数据预览:")
print(profiles_AA[0].head(10)) # 打印前十行


# ===================== 2) 初始化绘图器 & 设置默认样式 =====================
plotter = PyGMTPlotter()
plotter.set_defaults(
    FONT_TITLE="24p,Helvetica-Bold",
    FONT_ANNOT_PRIMARY="12p,Helvetica-Bold",
    FONT_LABEL="20p,Helvetica-Bold",
)

# ===================== 3) 局部绘图参数设置 =====================
projection  = "M8i"
# 地形数据
tif_dem = "data/DEM.tif"
# 色标文件
cpt_seismic = cpt_path/"seismic.cpt"
cpt_dem = "gray"
# 图片输出路径
(Path(__file__).resolve().parent / "result").mkdir(parents=True, exist_ok=True) # 创建结果目录
output_s1_as_norcia = "result/S1_AS_Norcia.png"
output_alos2_as = "result/ALOS2_AS.png"
output_profileAA_line = "result/Profile_AA_line.png"
output_profileAA_scatter = "result/Profile_AA_scatter.png"
output_profileBB_line = "result/Profile_BB_line.png"
output_profileBB_scatter = "result/Profile_BB_scatter.png"
output_profileCC_line = "result/Profile_CC_line.png"
output_profileCC_scatter = "result/Profile_CC_scatter.png"
output_profileDD_line = "result/Profile_DD_line.png"
output_profileDD_scatter = "result/Profile_DD_scatter.png"


# ===================== 4) 出图（DEM 底图 + 形变叠加 + 指北针 + 比例尺 + 色标） =====================
(plotter
    .new()  # 新建 Figure，并一次性应用刚才 set_defaults 的默认样式
    .draw_basemap(region=region_s1_as_norcia, projection=projection, title="Deformation: S1_AS_Norcia")
    .draw_dem(
        dem_tif=tif_dem, 
        cpt=cpt_dem,
        region=region_s1_as_norcia, 
        projection=projection,
        bar_min=700, bar_max=2300,   # 色带显示范围
    )   
    .draw_deformation(
        data_grd=grd_s1_as_norcia,
        cpt=cpt_seismic,
        region=region_s1_as_norcia,
        projection=projection,
        bar_min=-0.1, bar_max=0.1,   # 色带显示范围
        alpha=25                       # 图层透明度（0~100）
    )
    .draw_profile_tracks(tracks=tracks)
    .add_marker(lon=13.12, lat=42.84)
    .add_colorbar_bottom()
    .add_scale_top(region=region_s1_as_norcia, projection=projection)
    .add_rose_right(region=region_s1_as_norcia, projection=projection)
    .save(output_s1_as_norcia)
)

(plotter
    .new()  # 新建 Figure，并一次性应用刚才 set_defaults 的默认样式
    .draw_basemap(region=region_alos2_as, projection=projection, title="Deformation: ALOS2_AS")
    .draw_dem(
        dem_tif=tif_dem, 
        cpt=cpt_dem,
        region=region_alos2_as, 
        projection=projection,
        bar_min=700, bar_max=2300,   # 色带显示范围
    )   
    .draw_deformation(
        data_grd=grd_alos2_as,
        cpt=cpt_seismic,
        region=region_alos2_as,
        projection=projection,
        bar_min=-0.1, bar_max=0.1,   # 色带显示范围
        alpha=25                       # 图层透明度（0~100）
    )
    .draw_profile_tracks(tracks=tracks)
    .add_marker(lon=13.12, lat=42.84)
    .add_colorbar_bottom()
    .add_scale_top(region=region_alos2_as, projection=projection)
    .add_rose_right(region=region_alos2_as, projection=projection)
    .save(output_alos2_as)
)

# 绘制折线图
(plotter
    .new()
    .profile_new_axes(profiles=profiles_AA, title="Profile_AA")
    .profile_add_line(profile=profiles_AA[0], label="S1", pen="2p,red")
    .profile_add_line(profile=profiles_AA[1], label="ALOS2", pen="2p,blue")
    .profile_legend()
    .save(output_profileAA_line)
)
(plotter
    .new()
    .profile_new_axes(profiles=profiles_BB, title="Profile_BB")
    .profile_add_line(profile=profiles_BB[0], label="S1", pen="2p,red")
    .profile_add_line(profile=profiles_BB[1], label="ALOS2", pen="2p,blue")
    .profile_legend()
    .save(output_profileBB_line)
)
(plotter
    .new()
    .profile_new_axes(profiles=profiles_CC, title="Profile_CC")
    .profile_add_line(profile=profiles_CC[0], label="S1", pen="2p,red")
    .profile_add_line(profile=profiles_CC[1], label="ALOS2", pen="2p,blue")
    .profile_legend()
    .save(output_profileCC_line)
)
(plotter
    .new()
    .profile_new_axes(profiles=profiles_DD, title="Profile_DD")
    .profile_add_line(profile=profiles_DD[0], label="S1", pen="2p,red")
    .profile_add_line(profile=profiles_DD[1], label="ALOS2", pen="2p,blue")
    .profile_legend()
    .save(output_profileDD_line)
)


# 绘制散点图
(plotter
    .new()
    .profile_new_axes(profiles=profiles_AA, title="Profile_AA")
    .profile_add_scatter(profile=profiles_AA[0], label="S1", pen="0.5p,red", fill="red")
    .profile_add_scatter(profile=profiles_AA[1], label="ALOS2", pen="0.5p,blue", fill="blue")
    .profile_legend()
    .save(output_profileAA_scatter)
)
(plotter
    .new()
    .profile_new_axes(profiles=profiles_BB, title="Profile_BB")
    .profile_add_scatter(profile=profiles_BB[0], label="S1", pen="0.5p,red", fill="red")
    .profile_add_scatter(profile=profiles_BB[1], label="ALOS2", pen="0.5p,blue", fill="blue")
    .profile_legend()
    .save(output_profileBB_scatter)
)
(plotter
    .new()
    .profile_new_axes(profiles=profiles_CC, title="Profile_CC")
    .profile_add_scatter(profile=profiles_CC[0], label="S1", pen="0.5p,red", fill="red")
    .profile_add_scatter(profile=profiles_CC[1], label="ALOS2", pen="0.5p,blue", fill="blue")
    .profile_legend()
    .save(output_profileCC_scatter)
)
(plotter
    .new()
    .profile_new_axes(profiles=profiles_DD, title="Profile_DD")
    .profile_add_scatter(profile=profiles_DD[0], label="S1", pen="0.5p,red", fill="red")
    .profile_add_scatter(profile=profiles_DD[1], label="ALOS2", pen="0.5p,blue", fill="blue")
    .profile_legend()
    .save(output_profileDD_scatter)
)