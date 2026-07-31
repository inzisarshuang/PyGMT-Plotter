# Python Rules

## Module Responsibilities

- 配置语法、路径解析和通用校验放在 `lib/plot_config.py`。
- 数据转换、剖面抽取和通用绘图原语放在 `lib/pygmt_plotter.py`。
- 与图幅布局无关的栅格运算放在 `lib/geodata_preprocess.py`。
- `plot_*` 入口只组织参数和调用，不复制公共 TIF/TXT 分支。

## Interfaces

- 每个生产函数和方法（包括私有辅助函数与入口编排函数）都在函数开头用简洁 docstring 说明作用；公共科学接口按需要补充中英文参数、返回值和单位。
- 运行时输入错误使用 `ValueError`、`FileNotFoundError` 或 `RuntimeError`，不用 `assert`。
- 外部命令必须使用参数列表和 `subprocess.run(..., check=True)`，不拼接 shell 字符串。
- 路径使用 `pathlib.Path`；公开接口可接收字符串以方便 cfg 调用。

## Resource Control

- GeoTIFF 使用 `block_windows` 读取；文本点云使用 `chunksize`。
- GMT 能读取文件时，不先转换为完整 Pandas DataFrame。
- 所有数据集句柄使用上下文管理器关闭。
- 临时文件使用唯一名称并保证异常时清理；最终输出成功后再原子替换。

## Checks

```bash
python -m py_compile lib/*.py plot_defo_dem_optic/*.py plot_defo_profile/*.py
python -m unittest discover -s tests -v
```
