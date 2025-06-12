import pygmt
import numpy as np  
import re
from osgeo import gdal
import os   

class ProfilePlotter:
    def __init__(self):
        # 设置全局字体和排版配置
        pygmt.config(
            FONT_TITLE="20p,Helvetica-Bold", 
            FONT_ANNOT_PRIMARY="12p,Helvetica-Bold", 
            FONT_LABEL="20p,Helvetica-Bold"
        )
    
    def plot_profile(self, profile, output_file, label, title):
        """
        绘制单个剖面图：
          - 横坐标为累计距离（profile["distance"]）
          - 纵坐标为提取的数值（profile["z"]）
        
        参数:
          profile: 包含 "distance" 和 "z" 列的 DataFrame
          output_file: 输出图像文件名
          label: 图例标签，用于描述该剖面
        """
        x_min = profile["distance"].min()
        x_max = profile["distance"].max()
        y_min = profile["z"].min()
        y_max = profile["z"].max()
        # 为 y 轴添加一定边距
        y_gap = (y_max - y_min) * 0.1
        y_min -= y_gap
        y_max += y_gap

        fig = pygmt.Figure()
        fig.basemap(
            region=[x_min, x_max, y_min, y_max],
            frame=["xaf+lDistance (m)", "yaf+lDeformation (m)", f"+t{title}"]
        )
        fig.plot(
            x=profile["distance"],
            y=profile["z"],
            pen="2p,blue",
            label=label
        )
        fig.legend(position="JTR+o0.2c/-0.7c", box="+gwhite+p1.2p")
        fig.savefig(output_file)
        print("剖面图已保存为", output_file)
    
    def plot_multiple_profiles(self, profiles, labels, output_files, title):
        """
        绘制多个剖面对比图：
        - 横坐标为累计距离（单位：米）
        - 纵坐标为提取的剖面数值（存储在 profile["z"] 列中）
        
        参数:
        profiles: 一个列表，每个元素为一个剖面 DataFrame，要求每个 DataFrame 必须包含 "distance" 和 "z" 两列，
                    其中 "distance" 表示累计距离，"z" 表示对应的剖面数值。
        labels: 一个与 profiles 数量相同的字符串列表或元组，用于图例显示，如 ("Dataset 1", "Dataset 2", …)。
        output_file: 输出图像的文件名（字符串），例如 "multi_profile.png"。
        title: 图形标题字符串，例如 "Profile Comparison"，将在图形上方显示。
        
        返回:
        无返回值。该函数将绘制的图形保存到 output_file，并在终端打印保存信息。
        """
        # 检查 profiles 和 labels 数量是否匹配
        if len(profiles) != len(labels):
            raise ValueError("profiles 的数量必须与 labels 的数量一致。")
        
        # 计算所有剖面数据的全局横坐标（累计距离）范围
        x_min = min(profile["distance"].min() for profile in profiles)
        x_max = max(profile["distance"].max() for profile in profiles)
        # 计算所有剖面数据的全局纵坐标（数值）范围
        y_min = min(profile["z"].min() for profile in profiles)
        y_max = max(profile["z"].max() for profile in profiles)
        # 为纵坐标添加一定的边距（防止图形边界过紧）
        y_gap = (y_max - y_min) * 0.1
        y_min -= y_gap
        y_max += y_gap

        # 预设一些颜色，用于区分不同剖面
        colors = ["blue", "red", "green", "purple", "orange", "cyan", "magenta"]

        # 创建 PyGMT 图形对象，并设置地图框架与轴标签、标题
        fig1 = pygmt.Figure()
        fig1.basemap(
            region=[x_min, x_max, y_min, y_max],
            frame=["xaf+lDistance (m)", "yaf+lDeformation (m)", f"+t{title}"]
        )
        
        # 循环绘制每个剖面数据
        for i, profile in enumerate(profiles):
            color = colors[i % len(colors)]
            fig1.plot(
                x=profile["distance"],
                y=profile["z"],
                pen=f"2p,{color}",
                label=labels[i]
            )
        
        # 添加图例，并设置图例位置与样式
        fig1.legend(position="JTR+o0.2c/-1.2c", box="+gwhite+p1.2p")
        # 保存图形到指定文件
        fig1.savefig(output_files[0])
        print("多剖面图已保存为", output_files[0])

        fig2 = pygmt.Figure()
        # 重复 basemap
        fig2.basemap(
            region=[x_min, x_max, y_min, y_max],
            frame=["xaf+lDistance (m)", "yaf+lDeformation (m)", f"+t{title}"]
        )
        # 循环画散点并打图例标签
        for i, profile in enumerate(profiles):
            color = colors[i % len(colors)]
            fig2.plot(
                x=profile["distance"],
                y=profile["z"],
                style="c0.4c",     # 点大小
                fill=color,
                pen="0p",
                transparency=60,    # 透明度
                label=labels[i],
            )
            
            # 对散点拟合曲线
            # x = profile["distance"].to_numpy()
            # y = profile["z"].to_numpy()
            # # 先把 any NaN 的点过滤掉
            # mask = ~np.isnan(x) & ~np.isnan(y)
            # x_clean = x[mask]
            # y_clean = y[mask]

            # # 再做多项式拟合
            # coeffs = np.polyfit(x_clean, y_clean, deg=7)
            # # 拟合曲线数据
            # x_fit = np.linspace(x_clean.min(), x_clean.max(), 200)
            # y_fit = np.polyval(coeffs, x_fit)
            # # 绘制拟合曲线
            # fig2.plot(
            #     x=x_fit, y=y_fit,
            #     pen=f"5p,{color}",
            #     label=f"{labels[i]} fit"
            # )
    
        # 放置散点图例
        fig2.legend(position="JTR+o0.2c/-1.2c", box="+gwhite+p1.2p")
        # 保存
        fig2.savefig(output_files[1])
        print("多剖面散点图已保存为", output_files[1])

    def plot_basemap_profile(self, data_grd, cpt, dem_tif, tracks, output_file, title):
        """
        使用 PyGMT 绘制以 GRD 文件为底图的剖线图，并在每条剖线的起点和终点添加注释。
        此函数要求传入的所有剖线数据及其对应的名称已组合成一个字典，
        字典的键为注释名称（例如 "A"），值为完整采样轨迹数组（二维数组，每行 [lon, lat]，
        且顺序必须从起点到终点）。
        
        参数:
        grd_file: 字符串，包含形变速率数据的 GRD 文件路径。
        profile_dict: 字典，键为剖线注释名称（如 "A"），值为对应的完整轨迹数组（二维数组，每行为 [lon, lat]）。
        output_file: 输出图像的文件名（例如 "profile_on_rate.png"）。
        title: 图形标题字符串（默认 "Profile on Deformation Rate"），将在图形上方显示。
        
        返回:
        无返回值。该函数将图形保存到 output_file，并在终端打印提示信息。
        """
        # 获取 GRD 文件的区域信息。使用 pygmt.grdinfo 返回的信息可能为字典或字符串
        info_text = pygmt.grdinfo(grid=data_grd)
        # 提取区域范围信息
        def extract_region(text):
            # 使用正则表达式查找 x_min 和 x_max
            x_match = re.search(r"x_min:\s*([\d\.-]+)\s+x_max:\s*([\d\.-]+)", text)
            # 查找 y_min 和 y_max
            y_match = re.search(r"y_min:\s*([\d\.-]+)\s+y_max:\s*([\d\.-]+)", text)
            
            if x_match and y_match:
                x_min = float(x_match.group(1))
                x_max = float(x_match.group(2))
                y_min = float(y_match.group(1))
                y_max = float(y_match.group(2))
                return [x_min, x_max, y_min, y_max]
            else:
                raise ValueError("无法解析区域范围信息")

        region_full = extract_region(info_text)
        region_full = [12.9089530228813, 13.6527531042483, 42.5619969725113, 43.1762388777668]

        # 创建 PyGMT 图形对象
        fig = pygmt.Figure()
        projection = "M8i"  # 设置投影方式和图形宽度
        MAP_FRAME_WIDTH="6p" # 设置边框宽度
        MAP_FRAME_PEN="3p" # 设置边框线条宽度
        MAP_TICK_PEN="3p" # 设置刻度线条宽度
        
        # 绘制图形的基础框架
        with pygmt.config(MAP_FRAME_TYPE="fancy", MAP_FRAME_WIDTH="6p", FONT_ANNOT = "18p,1", MAP_FRAME_PEN="3p",    
                          MAP_TICK_PEN="3p", FORMAT_GEO_MAP="ddd:mm:ss"):
            factor = 3     # 经纬度标注间隔因子
            # 计算纬度和经度标注间隔（stride）
            x_stride = round((region_full[1] - region_full[0]) / factor, 4)  # 纬度标注间隔
            y_stride = round((region_full[3] - region_full[2]) / factor, 4)  # 经度标注间隔
            y_anno = f"a{y_stride}fg"  # 纬度的标注格式
            x_anno = f"a{x_stride}fg"  # 经度的标注格式
            fig.basemap(
                region=region_full,
                projection=projection,  # 图宽8英寸，根据需要调整
                frame=[f"x{x_anno}", f"y{y_anno}", f"+t{title}"],
            )

        # 绘制 DEM 底图
        dem_grd = "DEM.grd"
        demgradient_grd = "DEMgradiant.grd"
        if not os.path.exists(demgradient_grd):
            # 转换 DEM 的栅格数据格式
            gdal.Translate(dem_grd, dem_tif, format='GSBG')
            # 计算 DEM 的梯度
            pygmt.grdgradient(
                grid=dem_grd,
                outgrid=demgradient_grd,
                azimuth=0
            )
        # 创建颜色表（根据你的 shell 脚本来生成）
        pygmt.makecpt(cmap="gray", series=[-6000, 6000, 300], reverse=True)  # 使用灰度色表
        # 绘制 DEM 底图
        fig.grdimage(
            grid=dem_grd,
            region=region_full, 
            projection=projection,
            cmap=True,  # 使用之前生成的颜色表
            shading=demgradient_grd,  # 使用 DEM 梯度计算结果进行阴影处理
        )

        # 生成 CPT 文件
        cpt_data = cpt  # 手动选择cpt
        bar_min = -0.2
        bar_max = 0.2
        pygmt.makecpt(cmap=cpt_data, series=[bar_min, bar_max], background=True, reverse=True)  # 对选择的色带进行数值映射
        # 绘制形变速率底图
        fig.grdimage(
            grid=data_grd,
            region=region_full,
            projection=projection,
            cmap=True,  # 使用刚才生成的颜色映射
            transparency=25    # 设置透明度（例如 50%）
        )
        
        # 绘制 colorbar
        with pygmt.config(FONT_ANNOT_PRIMARY="20p", FONT_ANNOT_SECONDARY="24p, Helvetica-Bold"):
            # 模式1
            fig.colorbar(
                cmap=True, 
                position="JBR+o2.5c/-2c+w10c/0.5c+h",  # 将 colorbar 放置在右下角并设置偏移
                frame=["xa0.1f0.1+lDeformation", "y+lm"],  # 设置刻度
                box="-F+p2p+gwhite+c6p/5p"
            )
            # 模式2
            fig.colorbar(
                cmap=True, 
                frame=["xa0.1f0.1+lDeformation", "y+lm"]  # 设置刻度
            )

        # 绘制比例尺
        with pygmt.config(MAP_SCALE_HEIGHT="20p", FONT_ANNOT_PRIMARY="20p"):
            fig.basemap(
                region=region_full,
                projection=projection,
                map_scale="JCR+o3c/0c+w10k+f+u",  # 添加比例尺
                box="F+gWHITE+p2p+c8p/5p",  # 添加边框
            )

        # 绘制玫瑰图
        fig.basemap(
            region=region_full,
            projection=projection,
            rose="JRT+jCM+o6c/-5c+w5c+l+f1", # 添加指北针
            box="F+gwhite+p2p+c1.5c" # 添加边框
        )
        
        # 遍历字典中所有的剖线
        for name, track in tracks.items():
            # 确保当前的 track 是 NumPy 数组
            track = np.array(track)
            # 绘制完整的轨迹（所有采样点）
            fig.plot(
                x=track[:, 0],
                y=track[:, 1],
                pen="2p,black"
            )
 
            # 利用字典键生成注释：起点注释直接为键值；终点注释为键值加上撇号
            start_annotation = name
            end_annotation = name + "'"
            # 在起点添加文本注释，假设文字右上对齐
            fig.text(
                x=[track[0, 0]],
                y=[track[0, 1]],
                text=start_annotation,
                font="20p,Helvetica-Bold",
                justify="BR"
            )
            # 在终点添加文本注释，假设文字左上对齐
            fig.text(
                x=[track[-1, 0]],
                y=[track[-1, 1]],
                text=end_annotation,
                font="20p,Helvetica-Bold",
                justify="BL"
            )

            fig.plot(
                x=[13.12],
                y=[42.84],
                style="a16p",      # a = star, 大小 16p
                pen="2p,black"     # 边框 2p 黑色
                )

        
        # 保存图形到指定文件
        fig.savefig(output_file)
        print(f"剖线图已保存为 {output_file}")


