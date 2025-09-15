# PyGMT-Plotter
# PyGMT-Plotter

A lightweight plotting toolkit built on PyGMT.  
基于 PyGMT 的轻量级绘图工具箱。

It provides a chainable plotting class for general geographic plotting.  
提供一个可链式调用的绘图类，用于通用地理绘图。

Task-specific scripts are organized in separate folders and shared utilities live in `lib/`.  
任务脚本按功能分文件夹组织，共享工具置于 `lib/`。

---

## Features
## 功能

- Chainable plotting class (compose basemap, grdimage, colorbar, scale, markers, profiles, etc.).  
- 链式绘图类（可组合 basemap、grdimage、colorbar、比例尺、标记、剖面等）。

- Static helper tools for data preprocessing and raster conversion (TIF/TXT → GRD).  
- 用于数据预处理与栅格转换的静态辅助工具（TIF/TXT → GRD）。

- Project organized by task folders to ease maintenance and reuse.  
- 项目按任务文件夹组织，便于维护与复用。

---

## Repository overview
## 仓库总览

- `lib/` — shared utilities (e.g. `pygmt_plotter.py`) containing reusable classes and functions.  
- `lib/` — 共享工具（例如 `pygmt_plotter.py`），包含可复用的类与函数。

- `defo_dem/` — task scripts for deformation + DEM plotting (contains `data/` and `result/`).  
- `defo_dem/` — 形变 + DEM 绘图任务脚本（包含 `data/` 与 `result/`）。

- `defo_dem_profile/` — task scripts for deformation/DEM + profile extraction and plotting (contains `data/` and `result/`).  
- `defo_dem_profile/` — 形变/DEM 与剖面抽取绘图任务（包含 `data/` 与 `result/`）。

- `.vscode/`, `.env` — optional editor / runtime configs for local development.  
- `.vscode/`、`.env` — 可选的编辑器 / 运行时配置，供本地开发使用。

- `environment.yml` — environment specification (dependencies).  
- `environment.yml` — 环境依赖说明文件。

> Note: `data/` and `result/` often contain large files; include them in `.gitignore`.  
> 说明：`data/` 与 `result/` 通常包含大文件，建议在 `.gitignore` 中忽略。

---

## Install
## 安装

Use a virtual environment (conda or pip).  
使用虚拟环境管理依赖（conda 或 pip）。

Example (conda):  
示例（conda）：

```bash
conda env create -f environment.yml
conda activate envPlot
