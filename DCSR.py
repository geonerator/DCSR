
import numpy as np
import rasterio
import matplotlib.pyplot as plt

# Input raster file with 8 bands (1 observed + 7 GCM models)
input_file = ".tif"
# Output raster file with redistributed GCM rainfall (7 bands)
output_file = ".tif"

# Step 1: Load the input raster file
with rasterio.open(input_file) as src:
    # Read all bands
    observed_rainfall = src.read(1)  # Band 1: Observed rainfall
    cc_rainfall = [src.read(i) for i in range(2, 9)]  # Bands 2-7: CC models
    profile = src.profile  # Metadata for input raster
    profile.update(count=7)  # Update profile for 7 output bands

# Replace no-data values (-9999) with NaN for observed rainfall
observed_rainfall[observed_rainfall == -9999] = np.nan

# Calculate relative spatial weights from observed rainfall
observed_sum = np.nansum(observed_rainfall)
relative_weights = observed_rainfall / observed_sum

# Initialize an array to store the redistributed bands
redistributed_bands = []

# Step 2: Redistribute each CC model band based on observed weights
for band in cc_rainfall:
    # Replace no-data values with NaN
    band[band == -9999] = np.nan
    
    # Calculate total rainfall in the CC model band
    band_total = np.nansum(band)
    
    # Redistribute rainfall
    redistributed_band = relative_weights * band_total
    
    # Append redistributed band to the list
    redistributed_bands.append(redistributed_band)
import matplotlib.pyplot as plt
from rasterio.plot import show
from rasterio.transform import xy
# Ensure to follow order of rasters stacked-these names are the final ensemble based on our work
model_names = [
    "MIROC",
    "GFDL",
    "IPSL",
    "MRI",
    "EC",
    "INM",
    "MPI"
]

with rasterio.open(output_file, "w", **profile) as dst:
    for i, band in enumerate(redistributed_bands, start=1):
        dst.write(np.nan_to_num(band, nan=-9999), i)



# Create 4x4 figure
fig, axes = plt.subplots(4, 4, figsize=(18, 12), dpi=600)
axes = axes.ravel()

# Observed Rainfall (Top-left)
im = axes[0].imshow(observed_rainfall, cmap="Blues")
axes[0].set_title("Historical Rainfall(IMD)")
fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04)
axes[0].axis("off")

# Models (Original & Redistributed)
for i, model in enumerate(model_names):
    # Original
    im_orig = axes[i + 1].imshow(cc_rainfall[i], cmap="BuPu")
    axes[i + 1].set_title(f"{model} (Original)")
    fig.colorbar(im_orig, ax=axes[i + 1], fraction=0.046, pad=0.04)
    axes[i + 1].axis("off")

    # Redistributed
    im_redist = axes[i + 9].imshow(redistributed_bands[i], cmap="BuPu")
    axes[i + 9].set_title(f"{model} (Redistributed)")
    fig.colorbar(im_redist, ax=axes[i + 9], fraction=0.046, pad=0.04)
    axes[i + 9].axis("off")

# Repeat historicl Rainfall in last slot to fill
im_repeat = axes[8].imshow(observed_rainfall, cmap="BuPu")
axes[8].set_title("Historical Rainfall(IMD)")
fig.colorbar(im_repeat, ax=axes[8], fraction=0.046, pad=0.04)
axes[8].axis("off")

plt.tight_layout()
plt.show()
