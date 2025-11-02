
import sys
from pathlib import Path

lib_path = Path(__file__).resolve().parents[1] / "lib" # 自定义库路径
cpt_path = Path(__file__).resolve().parents[1] / "cpt" # 自定义库路径
sys.path.append(str(lib_path)) # 添加自定义库路径到系统路径

from pygmt_plotter import PyGMTPlotter

# ===================== 1) 数据预处理 =========================
# 形变速率数据
tif_sbas_allregion = "data/SBAS_AllRegion.tif"
tif_sbas = "data/SBAS.tif"
txt_psi = "data/PSI.txt"
# 转换后的 grd 数据文件
grd_sbas_allregion = "SBAS_AllRegion.grd"
grd_sbas = "SBAS.grd"
grd_psi = "PSI.grd"

# TIF -> GRD
region_all  = PyGMTPlotter.tif2grd(tif_path=tif_sbas_allregion, grd_path=grd_sbas_allregion)
region_sbas = PyGMTPlotter.tif2grd(tif_path=tif_sbas, grd_path=grd_sbas)

# TXT -> GRD
region_psi   = PyGMTPlotter.txt2grd(txt_path=txt_psi, grd_path=grd_psi, space=0.0005)

# ===================== 2) 初始化绘图器 & 设置默认样式 =====================
plotter = PyGMTPlotter()

# 设置首次默认绘图样式参数
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
cpt_saga = cpt_path/"saga-01.cpt"
cpt_dem = "gray"
# 图片输出路径
(Path(__file__).resolve().parent / "result").mkdir(parents=True, exist_ok=True)
output_sbas_allregion = "result/SBAS_AllRegion.png"
output_sbas = "result/SBAS.png"
output_psi = "result/PSI.png"

# ===================== 4) 出图（DEM 底图 + 形变叠加 + 指北针 + 比例尺 + 色标） =====================
# 保持全局的默认绘图参数
region_sbas_allregion = plotter.region_from_grd(grd_sbas_allregion)
(plotter
    .new()  # 新建 Figure，并一次性应用刚才 set_defaults 的默认样式
    .draw_geo_basemap(region=region_sbas_allregion, projection=projection, title="Deformation: SBAS_AllRegion")
    .draw_dem(
        dem_tif=tif_dem, 
        cpt=cpt_dem,
        region=region_sbas_allregion, 
        projection=projection,
        bar_min=700, bar_max=2300,   # 色带显示范围
    )   
    .draw_defo_grd(
        data_grd=grd_sbas_allregion,
        cpt=cpt_saga,
        region=region_sbas_allregion,
        projection=projection,
        bar_min=-0.06, bar_max=0.06,   # 色带显示范围
        alpha=25                       # 图层透明度（0~100）
    )
    .add_colorbar()
    .add_scale(region=region_sbas_allregion, projection=projection)
    .add_rose(region=region_sbas_allregion, projection=projection)
    .save(output_sbas_allregion)
)

# 修改全局的默认绘图参数
plotter.set_defaults(
    FONT_TITLE="28p,Helvetica-Bold",     # 标题更大
    FONT_ANNOT_PRIMARY="14p,Helvetica-Bold",  # 轴注/比例尺刻度更大
    FONT_LABEL="28p,Helvetica-Bold", # 图例标签更大
)
region_sbas = plotter.region_from_grd(grd_sbas)
(plotter
    .new()  
    .draw_geo_basemap(region=region_sbas, projection=projection, title="Deformation: SBAS")
    .draw_dem(
        dem_tif=tif_dem, 
        cpt=cpt_dem,
        region=region_sbas, 
        projection=projection,
        bar_min=700, bar_max=2300,   # 色带显示范围
    )   
    .draw_defo_grd(
        data_grd=grd_sbas,
        cpt=cpt_saga,
        region=region_sbas,
        projection=projection,
        bar_min=-0.06, bar_max=0.06,
        alpha=25
    )
    .add_colorbar()
    .add_scale(region=region_sbas, projection=projection)
    .add_rose(region=region_sbas, projection=projection)
    .save(output_sbas)
)


# 恢复原有的默认绘图参数
plotter.reset_defaults() # 又回到初始默认样式
region_psi = plotter.region_from_grd(grd_psi)
(plotter
    .new()  # 应用新的默认样式
    .draw_geo_basemap(region=region_psi, projection=projection, title="Deformation: PSI")
    .draw_dem(
        dem_tif=tif_dem, 
        cpt=cpt_dem,
        region=region_psi, 
        projection=projection,
        bar_min=700, bar_max=2300,   # 色带显示范围
    )   
    .draw_defo_grd(
        data_grd=grd_psi,
        cpt=cpt_saga,
        region=region_psi,
        projection=projection,
        bar_min=-0.06, bar_max=0.06,
        alpha=25
    )
    .add_colorbar()
    .add_scale(region=region_psi, projection=projection)
    .add_rose(region=region_psi, projection=projection)
    .save(output_psi)
)

