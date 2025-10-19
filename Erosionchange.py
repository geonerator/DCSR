
import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import re
from collections import defaultdict

# plotting %change graph of erosion from baseline
input_folder = "" # file containing all corrected GCMs
baseline_path = ".tif" # baseline erosion risk estimate file
#labelling purpose
scenario_map = {
    "126": "SSP 1-2.6",
    "245": "SSP2-4.5",
    "370": "SSP3-7.0",
    "585": "SSP 5-8.5"
}
year_map = {
    "2140": "2021–2040",
    "4160": "2041–2060",
    "6180": "2061–2080",
    "8110": "2081–2100"
}


with rasterio.open(baseline_path) as base_src:
    baseline = base_src.read(1).astype(np.float32)
    nodata = base_src.nodata
    baseline[baseline == nodata] = np.nan
    pixel_size = abs(base_src.transform[0]) * abs(base_src.transform[4])
    pixel_area_ha = pixel_size / 10_000
    total_baseline = np.nansum(baseline * pixel_area_ha)


erosion_by_scenario = {}

for filename in sorted(os.listdir(input_folder)):
    if not filename.lower().endswith(".tif"):
        continue
  
        ssp_code, year_code = match.groups()
        scenario = scenario_map.get(ssp_code)
        year = int(year_code)
        period = year_map.get(year_code, year_code)
        if scenario:
            full_path = os.path.join(input_folder, filename)
            with rasterio.open(full_path) as src:
                data = src.read(1).astype(np.float32)
                data[data == src.nodata] = np.nan
                total_erosion = np.nansum(data * pixel_area_ha)
                pct_change = ((total_erosion - total_baseline) / total_baseline) * 100

                erosion_by_scenario.setdefault(scenario, []).append((year, period, pct_change))


plt.figure(figsize=(10, 6), dpi=600)
for scenario, records in erosion_by_scenario.items():
    records.sort(key=lambda x: x[0])  # sort by year code
    years = [r[1] for r in records]
    pct_values = [r[2] for r in records]
    plt.plot(years, pct_values, marker='o', label=scenario)

plt.axhline(0, color='gray', linestyle='--', linewidth=0.8, label="Baseline Erosion")
plt.title(" % Change in Total Erosion from Baseline (using reference raster)", fontsize=14)
plt.ylabel("Percent Change in Total Erosion (%)")
plt.xlabel("Time Period")
plt.grid(True, linestyle=':', alpha=0.5)
plt.legend(title="Scenario")
plt.tight_layout()
plt.show()

# Plotting erosion difference plots w.r.t baseline
files_info = []
for filename in sorted(os.listdir(input_folder)):
    if not filename.lower().endswith(".tif"):
        continue

        ssp_code, year_code = match.groups()
        scenario = scenario_map.get(ssp_code, f"SSP{ssp_code}")
        period = year_map.get(year_code, year_code)
        full_path = os.path.join(input_folder, filename)
        files_info.append((scenario, period, full_path))

# Sort: SSP1 first, then SSP5, and years in order
files_info.sort(key=lambda x: (x[0], x[1]))

 
fig, axes = plt.subplots(2, 4, figsize=(18, 9), constrained_layout=True, dpi=600)
axes = axes.flatten()

# Set manual color range for visual contrast
vmin, vmax = -500, 500  # Adjust based on actual erosion ranges
cmap = "nipy_spectral"

#PLOT EACH DIFFERENCE MAP 
for ax, (scenario, period, path) in zip(axes, files_info):
    with rasterio.open(path) as src:
        future = src.read(1).astype(np.float32)
        future[future == src.nodata] = np.nan

    diff = future - baseline

    img = ax.imshow(diff, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_title(f"{scenario}\n{period}", fontsize=12)
    #ax.axis('off')
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.5)
        spine.set_edgecolor("black")
    
    # Keep ticks hidden
    ax.set_xticks([])
    ax.set_yticks([])
    

cbar = fig.colorbar(img, ax=axes.tolist(), orientation="vertical", shrink=0.75)
cbar.set_label("Change in Erosion (tons/ha/year)")

plt.show()