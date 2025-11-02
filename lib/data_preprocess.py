    
import rasterio
import numpy as np  



def add_tifs(
    tif1_path: str,
    tif2_path: str,
    out_tif: str,
    mask_any: bool = True
) -> None:
    """
    将两幅 GeoTIFF 按像元相加，并根据 nodata 掩膜结果。
    Add two GeoTIFF rasters pixel‐wise with nodata masking.

    参数 (Parameters)
    ----------
    tif1_path : str
        第一幅输入 GeoTIFF 文件路径。
        Path to the first input GeoTIFF.
    tif2_path : str
        第二幅输入 GeoTIFF 文件路径。
        Path to the second input GeoTIFF.
    out_tif : str
        输出 GeoTIFF 文件路径。
        Path where the output GeoTIFF will be saved.
    mask_any : bool, optional
        掩膜模式：
        - True：任一像元为 nodata 时输出 nodata（mask = nan1 | nan2）。
        - False：仅当两者均为 nodata 时才输出 nodata（mask = nan1 & nan2）。
        Mask mode: True to mask if any input is nodata, False to mask only if all inputs are nodata.

    返回 (Returns)
    -------
    None
    """
    print(f"Adding TIFFs:\n  1: {tif1_path}\n  2: {tif2_path}\nMask any nodata: {mask_any}")

    # 1. 打开两幅 TIF 并读取元数据与像元值 / Open both rasters and read metadata & arrays
    with rasterio.open(tif1_path) as src1, rasterio.open(tif2_path) as src2:
        meta = src1.meta.copy()             # 复制第一个文件的元数据 / copy metadata from first raster
        nodata1 = src1.nodata               # 第一个文件的 nodata 值 / nodata value of raster1
        nodata2 = src2.nodata               # 第二个文件的 nodata 值 / nodata value of raster2

        arr1 = src1.read(1).astype("float32")  # 读取第一波段并转换为 float32 / read band1 as float32
        arr2 = src2.read(1).astype("float32")  # 读取第一波段并转换为 float32 / read band1 as float32

    # 2. 将 nodata 值替换为 NaN，便于后续掩膜 / Convert nodata to NaN for masking
    if nodata1 is not None:
        arr1[arr1 == nodata1] = np.nan
    if nodata2 is not None:
        arr2[arr2 == nodata2] = np.nan

    # 3. 构造掩膜 / Build mask according to mask_any
    nan1 = np.isnan(arr1)
    nan2 = np.isnan(arr2)
    if mask_any:
        mask = nan1 | nan2  # 任一为 NaN 时掩膜 / mask if either is NaN
    else:
        mask = nan1 & nan2  # 仅全为 NaN 时掩膜 / mask if both are NaN

    # 4. 执行像元相加，再应用掩膜 / Perform pixel‐wise addition and apply mask
    result = arr1 + arr2
    result[mask] = np.nan  # 将掩膜位置置为 NaN / set masked locations to NaN

    # 5. 更新元数据并写出结果 / Update metadata and write output
    meta.update(dtype="float32", nodata=np.nan)
    with rasterio.open(out_tif, "w", **meta) as dst:
        dst.write(result, 1)
    print(f"Output saved to: {out_tif}")