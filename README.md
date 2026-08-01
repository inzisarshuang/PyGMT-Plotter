# PyGMT-Plotter

PyGMT-Plotter is a configuration-driven toolkit for deformation maps, DEM or optical basemaps, and deformation profiles. It combines reusable, chainable PyGMT primitives with strict cfg files and bounded-memory geospatial preprocessing.

PyGMT-Plotter 是一个由配置文件驱动的科研绘图库，用于绘制形变、DEM 或光学底图以及形变剖面。仓库将可复用的 PyGMT 链式绘图功能、严格的 cfg 接口和低内存地理数据预处理组合在一起。

## Workflows / 工作流

- `plot_defo_dem_optic`: convert TIF/TXT deformation data to GRD and draw it over a DEM or optical basemap.<br>将 TIF/TXT 形变数据转换为 GRD，并叠加在 DEM 或光学底图上。
- `plot_defo_profile`: compare two deformation datasets on maps and along named profile tracks.<br>在地图和指定剖线上比较两套形变数据。
- `lib/pygmt_io.py`: strict cfg parsing, path resolution, temporary files, atomic replacement, and GDAL command wrappers.<br>严格配置解析、路径处理、临时文件、原子替换和 GDAL 命令封装。
- `lib/pygmt_geo.py`: bounded-memory raster arithmetic, grid conversion, track generation, and profile extraction.<br>低内存栅格运算、网格转换、轨迹生成和剖面提取。
- `lib/pygmt_visual.py`: figure state and chainable PyGMT drawing primitives.<br>绘图状态管理和可链式调用的 PyGMT 绘图原语。

## Repository Layout / 仓库结构

```text
PyGMT-Plotter/
├── AGENTS.md                         # coding baseline / 代码基线
├── CONTRIBUTING.md                   # contribution workflow / 开发流程
├── cpt/                              # shared color palettes / 公共色带
├── docs/development/                 # engineering rules / 工程规则
├── lib/
│   ├── pygmt_geo.py                  # spatial processing / 空间处理
│   ├── pygmt_io.py                   # config and file I/O / 配置与文件读写
│   └── pygmt_visual.py               # plotting / 绘图
├── plot_defo_dem_optic/
│   ├── data/                         # tracked example data / 已跟踪示例数据
│   ├── plot_defo_dem_optic.cfg
│   └── plot_defo_dem_optic.py
├── plot_defo_profile/
│   ├── data/                         # tracked example data / 已跟踪示例数据
│   ├── plot_defo_dem_profile.cfg
│   └── plot_defo_dem_profile.py
├── tests/
└── requirements.txt
```

The current example datasets are tracked so both workflows can be reproduced after cloning. Generated GRD files and figures are ignored.

当前示例数据已经纳入版本控制，克隆仓库后即可复现。新生成的 GRD 和图片不会提交到仓库。

## Installation / 安装

GMT and `gdal_translate` are native command-line dependencies; they are not Python packages in `requirements.txt`. Conda is the recommended installation route:

GMT 和 `gdal_translate` 属于原生命令行依赖，不应通过 `requirements.txt` 安装。推荐使用 Conda：

```bash
conda create -n envPlot -c conda-forge \
  python=3.10 pygmt=0.10 gmt gdal rasterio pyproj numpy pandas -y
conda activate envPlot

gmt --version
gdal_translate --version
```

The code targets Python 3.10 or newer. PyGMT `0.10.0` is the verified server version; later compatible versions can also be tested.

代码面向 Python 3.10 或更高版本。服务器已验证 PyGMT `0.10.0`，也可测试后续兼容版本。

## Usage / 使用方法

Paths inside a cfg file are resolved relative to that cfg file, not the shell's current directory. This makes project-specific cfg files portable.

cfg 中的相对路径始终以 cfg 文件所在目录为基准，与终端当前目录无关，便于迁移项目配置。

```bash
conda run -n envPlot python plot_defo_dem_optic/plot_defo_dem_optic.py \
  --config plot_defo_dem_optic/plot_defo_dem_optic.cfg

conda run -n envPlot python plot_defo_profile/plot_defo_dem_profile.py \
  --config plot_defo_profile/plot_defo_dem_profile.cfg
```

Each example cfg documents every supported option, its unit, and valid choices. Unknown or duplicate keys fail early instead of being silently ignored. Hex colors such as `#1f77b4` are supported directly.

每个示例 cfg 都列出了支持的参数、单位和可选值。未知键或重复键会直接报错；可直接使用 `#1f77b4` 一类十六进制颜色。

## Data Behavior / 数据行为

- TIF conversion reads raster blocks instead of loading the full scene.<br>TIF 转换按栅格块读取，不加载整景矩阵。
- TXT point tables are scaled and written to GMT in chunks (`*_chunk_rows`).<br>TXT 点表按 `*_chunk_rows` 分块缩放并写入 GMT。
- Grid scatter plots are passed to GMT through temporary XYZ files instead of a full Pandas DataFrame.<br>栅格散点通过临时 XYZ 文件交给 GMT，不构造完整 Pandas DataFrame。
- Temporary products use unique names; final grids and figures replace their destination only after success.<br>临时产品使用唯一名称，最终网格和图片仅在成功后替换目标文件。
- Display ranges such as `defo_bar_min` and `defo_bar_max` control color mapping only and do not modify source values.<br>`defo_bar_min`、`defo_bar_max` 等显示范围只控制颜色映射，不修改源数据。

These constraints reduce peak memory on large regions and prevent interrupted jobs from leaving partial files that appear valid.

这些约束用于降低大区域处理的峰值内存，并避免中断后留下看似完整、实际损坏的结果文件。

## Verification / 验证

```bash
python -m py_compile lib/*.py plot_defo_dem_optic/*.py plot_defo_profile/*.py
python -m unittest discover -s tests -v
git diff --check
```

Changes to shared plotting or I/O code should also run both example workflows and visually inspect their outputs.

修改公共绘图或数据读取逻辑后，还应完整运行两个示例并检查生成图片。

## Development Rules / 开发规则

Read [AGENTS.md](AGENTS.md) before adding code. Detailed ownership and scientific-data conventions are in [engineering_rules.md](docs/development/engineering_rules.md). Region-specific benchmark files are intentionally not part of this repository.

新增代码前请先阅读 [AGENTS.md](AGENTS.md)。更详细的模块边界和科学数据约定见 [engineering_rules.md](docs/development/engineering_rules.md)。仓库不维护与特定区域绑定的 benchmark。

## Author / 作者

Yilun Tan (谭逸伦), SIGM@3D Laboratory, School of Geosciences and Info-Physics, Central South University.

谭逸伦，中南大学地球科学与信息物理学院 SIGM@3D 实验室。

Email: csuyiluntan@gmail.com, yiluntancsu@qq.com
