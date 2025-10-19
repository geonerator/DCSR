
import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
from rasterio.enums import Resampling
from scipy.stats import spearmanr
# -------------------------------------------------------------------
# 1.  User settings –  file names & column names 
# -------------------------------------------------------------------
MODELS_RASTER = ".tif"           # 7-band GCM raster
OBS_SHP      = ".shp"     # validation in our case IMD points 

OBS_COLS = [""]  # column name having mean rain(observation/IMD) 


# -------------------------------------------------------------------
# 2.  Read observation points
# -------------------------------------------------------------------
gdf = gpd.read_file(OBS_SHP)
# Check if all required columns exist
if not set(OBS_COLS).issubset(gdf.columns):
    raise ValueError(f"One or more OBS_COLS not found in {OBS_SHP}")

# Drop points where **any of the observed rainfall values is zero or missing**
gdf = gdf.dropna(subset=OBS_COLS)                        # Drop NaNs
gdf = gdf[(gdf[OBS_COLS] != 0).all(axis=1)]              # Drop rows with any 0 in observed columns


if not set(OBS_COLS).issubset(gdf.columns):
    raise ValueError(f"One or more OBS_COLS not found in {OBS_SHP}")



# -------------------------------------------------------------------
# 3.  Open the raster and re-project points if needed
# -------------------------------------------------------------------
with rasterio.open(MODELS_RASTER) as src:
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)      # re-project in-memory
    
    coords = [(geom.x, geom.y) for geom in gdf.geometry]

    # sample the 6 bands at those points (bilinear avoids stair-steps)
    samples = list(
    src.sample(
        coords,
        indexes=range(1, 8)         # uses nearest-neighbor by default
    )
)


# samples → array shape (n_points, 6)
pred = np.array(samples)

invalid_mask = (np.isnan(pred).all(axis=1)) | ((pred == 0).all(axis=1))

# Only keep valid points (at least one band non-zero and non-NaN)
valid_mask = ~invalid_mask

# Filter data
valid_points = gdf[valid_mask].copy()
valid_preds  = pred[valid_mask]

gdf = valid_points
pred = valid_preds

# -------------------------------------------------------------------
# 4.  Metric helpers
# -------------------------------------------------------------------


def mape(x, y):
    mask = np.isnan(x) | np.isnan(y) | (y == 0)
    return (np.abs((x[~mask] - y[~mask]) / y[~mask]) * 100).mean()

def spearman(x, y):
    r_spearman, _ = spearmanr(y, x)
    return r_spearman

# -------------------------------------------------------------------
# 5.  Evaluate each model band
# -------------------------------------------------------------------
records = []

for b in range(7):
        mape_vals, spevals = [], []
        model_vals = pred[:, b]
        for col in OBS_COLS:
            obs = gdf[col].to_numpy()
            mape_vals.append(mape(model_vals, obs))
            spevals.append(spearman(model_vals, obs))
        records.append(
            {
                "model_band": b + 1,
                "MAPE_%":     np.nanmean(mape_vals),
                "Spearman":   np.nanmean(spevals)
            }
        )

# -------------------------------------------------------------------
# 6.  Rank and show
# -------------------------------------------------------------------

df = pd.DataFrame(records)
pd.set_option('display.float_format', '{:.4f}'.format)
print(df)