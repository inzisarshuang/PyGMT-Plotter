# Scientific Conventions

## Values And Units

- `*_scale` 在写入 GRD 前乘到原始值上；cfg 的标题、颜色条单位和显示范围必须与缩放后的单位一致。
- `defo_bar_min/max` 只控制 CPT 映射，不截断、不重写原始形变值。
- 零值是有效数值，除非某个参数明确规定把 NaN/nodata 转为零。

## Nodata

- TIF 转 GRD 时，`*_nan_to_zero = true` 才允许将 nodata/NaN 写为零。
- `add_tifs(mask_any=true)`：任一输入为空则输出为空。
- `add_tifs(mask_any=false)`：单侧空值按零参与相加，仅双侧均为空时输出为空。

## Coordinates And Grids

- 像元运算前必须核对尺寸、仿射变换和 CRS。
- cfg 坐标顺序为 `lon,lat`，地图范围顺序为 `west,east,south,north`。
- TXT 网格上界按 `space` 向外对齐，避免 GMT 的区域与间距不兼容；不会移动输入点。
- 剖线距离使用 WGS84 椭球测地距离并从起点累计，单位为米。

## Visual Validation

- 地图应检查形变覆盖范围、nodata 透明区、CPT 方向、颜色条单位和剖线位置。
- 剖面图应检查两套数据使用相同轨迹，图例与画布不重叠，折线和散点样式符合 cfg。
- 图像成功生成不等于科学语义正确；共享绘图改动必须至少人工查看一张地图和一张剖面图。
