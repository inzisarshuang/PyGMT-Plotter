
import sys
from pathlib import Path

lib_path = Path(__file__).resolve().parents[1] / "lib" # 自定义库路径
cpt_path = Path(__file__).resolve().parents[1] / "cpt" # 自定义库路径
sys.path.append(str(lib_path)) # 添加自定义库路径到系统路径

from pygmt_plotter import PyGMTPlotter

# ===================== 1) 数据预处理与文件参数设置 =========================
# 形变速率数据
tif_sbas1 = "data/mean_v_sbas1.utm.tif"
tif_sbas2 = "data/mean_v_sbas2.utm.tif"
# 转换后的 grd 数据文件
grd_sbas1 = "mean_v_sbas1.utm.grd"
grd_sbas2 = "mean_v_sbas2.utm.grd"
# TIF -> GRD
region_sbas = PyGMTPlotter.tif2grd(tif_path=tif_sbas1, grd_path=grd_sbas1)
region_sbas = PyGMTPlotter.tif2grd(tif_path=tif_sbas2, grd_path=grd_sbas2)

# 光学数据
tif_optic = "data/shizhuyuan.tif"

# 色标文件
cpt_saga = cpt_path/"saga-22-tyl3.cpt"


# 图片输出路径
(Path(__file__).resolve().parent / "result").mkdir(parents=True, exist_ok=True)
output_sbas1 = "result/mean_v_sbas1.utm.png"
output_sbas2 = "result/mean_v_sbas2.utm.png"


# ===================== 2) 初始化绘图器 & 设置默认样式 =====================
plotter = PyGMTPlotter()

region_sbas = [ 113.05, 113.25, 25.65, 25.85 ]

# 设置首次默认绘图样式参数
plotter.set_defaults(
    FONT_TITLE="24p,Helvetica-Bold",
    FONT_ANNOT_PRIMARY="12p,Helvetica-Bold",
    FONT_LABEL="20p,Helvetica-Bold",
)

# 画布大小
projection  = "M8i"

# ===================== 3) 出图（光学 底图 + 形变叠加 + 指北针 + 比例尺 + 色标） =====================

# 修改全局的默认绘图参数
plotter.set_defaults(
    FONT_TITLE="28p,Helvetica-Bold",     # 标题更大
    FONT_ANNOT_PRIMARY="14p,Helvetica-Bold",  # 轴注/比例尺刻度更大
    FONT_LABEL="28p,Helvetica-Bold", # 图例标签更大
)
(plotter
    .new()  
    .draw_geo_basemap(region=region_sbas, projection=projection, title="Deformation: SBAS")
    .draw_optic(
        optic_tif = tif_optic,
        region = region_sbas,
        projection = projection,
        transparency = 0,
    )
    .draw_defo_scatter(        
        data_grd = grd_sbas1,
        cpt = cpt_saga,
        region = region_sbas,
        projection = projection,
        bar_min=-0.05, bar_max=0.05,
        transparency = 25
    )   
    .add_colorbar()
    .add_scale(region=region_sbas, projection=projection)
    .add_rose(region=region_sbas, projection=projection)
    .save(output_sbas1)
)

(plotter
    .new()  
    .draw_geo_basemap(region=region_sbas, projection=projection, title="Deformation: SBAS")
    .draw_optic(
        optic_tif = tif_optic,
        region = region_sbas,
        projection = projection,
        transparency = 0,
    )
    .draw_defo_scatter(        
        data_grd = grd_sbas2,
        cpt = cpt_saga,
        region = region_sbas,
        projection = projection,
        bar_min=-0.05, bar_max=0.05,
        transparency = 25
    )   
    .add_colorbar()
    .add_scale(region=region_sbas, projection=projection)
    .add_rose(region=region_sbas, projection=projection)
    .save(output_sbas2)
)



