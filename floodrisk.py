import numpy as np
import matplotlib.pyplot as plt
import rasterio

# Path to your raster file
raster_path = ".tif"  # Replace with your actual path(rasters of recorded+GCMs+Risk)
nodata_value = -9999  # Define the no-data value used in your raster



# Read raster bands
with rasterio.open(raster_path) as src:
    present_rainfall = src.read(1).astype(float)
    future_rainfall_bands = [src.read(i).astype(float) for i in range(2, 10)]

# Create a mask where all values are valid
valid_mask = present_rainfall != nodata_value
for band in future_rainfall_bands:
    valid_mask &= band != nodata_value

# Set fixed color scale range
vmin, vmax = -200, 500  # in mm(our case range)

# Plot
fig, axs = plt.subplots(2, 4, figsize=(20, 12))
fig.suptitle("Rainfall Differences (Future - Present)\nValid Pixels Only, Fixed Scale [-200 mm, +500 mm]", fontsize=16)

for i, future_band in enumerate(future_rainfall_bands):
    diff = np.where(valid_mask, future_band - present_rainfall, np.nan)

    ax = axs[i // 4, i % 4]
    im = ax.imshow(diff, cmap="coolwarm", vmin=vmin, vmax=vmax)
    ax.set_title(f"Model {i+1} (Band {i+2})")
    ax.axis("off")
    fig.colorbar(im, ax=ax, shrink=0.7)

plt.tight_layout()
plt.show()



with rasterio.open(raster_path) as src:
    present_risk = src.read(10).astype(float)
    present_rain = src.read(1).astype(float)
    future_rain_bands = [src.read(i).astype(float) for i in range(2, 10)]
    profile = src.profile

# Valid mask
valid_mask = (present_risk != nodata_value) & (present_rain != nodata_value)
for band in future_rain_bands:
    valid_mask &= band != nodata_value

# Container for future risk maps
future_risk_maps = []

# Loop through future rainfall bands
for idx, future_rain in enumerate(future_rain_bands):
    rainfall_diff = future_rain - present_rain
    adjusted_risk = present_risk.copy()

    # Calculate dynamic thresholds (per pixel)
    plus_15 = present_rain * 0.15
    plus_10 = present_rain * 0.10
    plus_5  = present_rain * 0.05

    minus_5  = -present_rain * 0.05
    minus_10 = -present_rain * 0.10
    minus_15 = -present_rain * 0.15

    # Apply rules based on % difference
    increase_3 = (rainfall_diff >= plus_15) & valid_mask
    increase_2 = ((rainfall_diff >= plus_10) & (rainfall_diff < plus_15)) & valid_mask
    increase_1 = ((rainfall_diff >= plus_5) & (rainfall_diff < plus_10)) & valid_mask
    decrease_1 = ((rainfall_diff <= minus_5) & (rainfall_diff > minus_10)) & valid_mask
    decrease_2 = (rainfall_diff <= minus_10) & valid_mask
    
    adjusted_risk[increase_3] += 3
    adjusted_risk[increase_2] += 2
    adjusted_risk[increase_1] += 1
    adjusted_risk[decrease_1] -= 1
    adjusted_risk[decrease_2] -= 2

    # Optionally ensure risk stays between 1 and 5
   # adjusted_risk = np.clip(adjusted_risk, 1, 5)

    # Keep invalid pixels as no data
    adjusted_risk[~valid_mask] = nodata_value
    
    valid_values = adjusted_risk[valid_mask]
    print(f"Band {idx+2} → Min Risk: {np.min(valid_values)}, Max Risk: {np.max(valid_values)}")

    future_risk_maps.append(adjusted_risk.astype(np.int32))

# Stack all adjusted future risk layers
future_risk_stack = np.stack(future_risk_maps)

# Save output raster
output_path = ".tif" #give output path
profile.update({
    "count": 8,
    "dtype": rasterio.int32,
    "nodata": nodata_value
})

with rasterio.open(output_path, "w", **profile) as dst:
    for i in range(8):
        dst.write(future_risk_stack[i], i + 1)

print(f"Saved updated risk class maps with rainfall sensitivity to {output_path}")
#code to display the output(optional)
import rasterio
import matplotlib.pyplot as plt
import numpy as np

with rasterio.open(raster_path) as src:
    image = src.read()
    nodata = src.nodata

present_risk = image[9]  # Band 1
adjusted_risk_file = ".tif" #output file path(paste here)

with rasterio.open(adjusted_risk_file) as src:
    adjusted_risks = src.read()

# Plot original + 6 future risk maps
fig, axs = plt.subplots(2, 4, figsize=(24, 12), constrained_layout=True, dpi=600)

# Plot original
cmap = plt.get_cmap("RdYlGn_r")
vmin = np.nanmin(adjusted_risks[adjusted_risks != nodata])
vmax = np.nanmax(adjusted_risks[adjusted_risks != nodata])

#axs[0, 0].imshow(np.where(present_risk == nodata, np.nan, present_risk), cmap=cmap, vmin=vmin, vmax=vmax)
#axs[0, 0].set_title("Original Risk Map")
#axs[0, 0].axis("off")

# Load the predicted risk map (6 bands)
#risk_map_path = "D:/cc_data/Deep_Flood/aligned_rasters1/Deep/all/future_risk_class_maps.tif"

titles = [
    "Future Ensemble 2021-40(126)",
    "Future Ensemble 2041-60(126)",
    "Future Ensemble 2061-80(126)",
    "Future Ensemble 2081-10(126)",
    "Future Ensemble 2021-40(585)",
    "Future Ensemble 2041-60(585)",
    "Future Ensemble 2061-80(585)",
    "Future Ensemble 2081-10(585)"
]

for i in range(8):
    ax = axs[(i)//4, (i)%4]
    data = np.where(adjusted_risks[i] == nodata, np.nan, adjusted_risks[i])
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_title(titles[i], fontsize=14)
    ax.axis("off")


fig.colorbar(im, ax=axs, orientation='horizontal', shrink=0.6, label="Risk Level")

plt.suptitle(" Future Adjusted Risk Maps", fontsize=16)

plt.show()