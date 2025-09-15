# PyGMT-Plotter

A lightweight plotting toolkit built on PyGMT. It provides a chainable plotting class for general geographic plotting. Task-specific scripts are organized in separate folders and shared library live in `lib/`.   
基于 PyGMT 的轻量级绘图工具箱。提供一个可链式调用的绘图类，用于通用地理绘图。任务脚本按功能分文件夹组织，共享库置于 `lib/`。

---

## Features 功能

- Chainable plotting class (compose basemap, grdimage, colorbar, scale, markers, profiles, etc.).  
链式绘图类，选择 pygmt.Figure 作为类对象，通过链式调用逐个叠加绘制好的图形要素。

- Static helper tools for data preprocessing and raster conversion (TIF/TXT → GRD).  
用于数据预处理与转换的静态辅助工具（如转换 TIF/TXT 格式到 GRD 格式）。

- Project organized by task folders to ease maintenance and reuse.  
项目按任务文件夹组织，便于维护与复用。

---

## Repository overview 仓库总览

- `lib/` — shared utilities (e.g. `pygmt_plotter.py`) containing reusable classes and functions.  
`lib/` — 共享工具（例如 `pygmt_plotter.py`），包含可复用的类与函数。

- `defo_dem/` — task scripts for deformation + DEM plotting (contains `data/` and `result/`).  
`defo_dem/` — 形变 + DEM 绘图任务脚本（包含 `data/` 与 `result/`）。

- `defo_dem_profile/` — task scripts for deformation/DEM + profile extraction and plotting (contains `data/` and `result/`).  
`defo_dem_profile/` — 形变/DEM 与剖面抽取绘图任务（包含 `data/` 与 `result/`）。

- `.vscode/`, `.env` — optional editor / runtime configs for local development.  
`.vscode/`、`.env` — 可选的编辑器 / 运行时配置，供本地开发使用。

- `environment.yml` — environment specification (dependencies).  
`environment.yml` — 环境依赖说明文件。

> Note: `data/` and `result/` often contain large files; include them in `.gitignore`.  
> 说明：`data/` 与 `result/` 通常包含大文件，建议在 `.gitignore` 中忽略。

---

## Install 安装

Use a virtual environment (conda or pip).  
使用虚拟环境管理依赖（conda 或 pip）。

Example (conda):  
示例（conda）：

```bash
conda env create -f environment.yml
conda activate envPlot
```

---

## Usage
使用（简短指引）

Import the shared library and use the chainable API in your scripts.
在脚本中导入共享库并使用链式 API 组合绘图。

Example:
示例：

```bash
from pygmt_plotter import PyGMTPlotter
plotter = PyGMTPlotter()
```

Detailed examples are provided in each task folder.
详细示例请参考各任务文件夹内的演示脚本。

---

## Author 作者 

Name: Yilun Tan
姓名：谭逸伦

Email: csuyiluntan@gmail.com, yiluntancsu@qq.com
邮箱：csuyiluntan@gmail.com，yiluntancsu@qq.com

Affiliation: SIGMA3D Lab, School of Geosciences and Info-Physics, Central South University
单位：中南大学地球科学与信息物理学院 SIGMA3D 实验室

Created: 2025-09-15
创建时间：2025-09-15

Short summary: A thin wrapper PyGMT plotter enabling chain-style composition and export.
简短说明：该类为封装的 PyGMT 绘图器，通过链式调用完成图形的组合绘制与保存。