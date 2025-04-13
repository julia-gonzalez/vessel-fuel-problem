import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def main():
    instances_folder = "instances"
    charts_folder = "instance_charts"
    
    os.makedirs(charts_folder, exist_ok=True)
    sns.set(style="whitegrid")
    
    # Data containers
    vessel_counts = []
    fuel_demands = []
    peak_vessel_counts = []
    vessel_timeline_records = []
    
    # Load and analyze instances
    for file_name in os.listdir(instances_folder):
        with open(os.path.join(instances_folder, file_name)) as json_file:
            instance = json.load(json_file)
    
        vessels = instance["vessels"]
        vessel_counts.append(len(vessels))
        fuel_demands.append(sum(v["fuel_demand"]/1000 for v in vessels))
    
        if vessels:
            max_departure = max(v["departure_time"] for v in vessels)
        else:
            max_departure = 0
    
        timeline = np.zeros(max_departure + 1, dtype=int)
    
        for vessel in vessels:
            timeline[vessel["arrival_time"]:vessel["departure_time"]] += 1
    
        peak_vessel_counts.append(timeline.max())
        vessel_timeline_records.append(timeline)
    
    # Normalize timelines
    global_max_time = max(len(tl) for tl in vessel_timeline_records)
    for i in range(len(vessel_timeline_records)):
        pad_len = global_max_time - len(vessel_timeline_records[i])
        if pad_len > 0:
            vessel_timeline_records[i] = np.pad(vessel_timeline_records[i], (0, pad_len))
    
    vessel_timelines = np.array(vessel_timeline_records)
    time_axis = np.arange(global_max_time)
    sns.set()
    sns.set_palette("bright")
    
    # --- Chart 1: Vessel Count Distribution ---
    plt.figure(figsize=(8, 5))
    bins = range(min(vessel_counts), max(vessel_counts) + 2)
    sns.histplot(vessel_counts, bins=bins, discrete=True)
    plt.xticks(bins[::2])
    plt.title("Distribution of Number of Vessels per Instance")
    plt.xlabel("Number of Vessels")
    plt.ylabel("Number of Instances")
    plt.tight_layout()
    plt.savefig(os.path.join(charts_folder, "vessel_count_distribution.pdf"))
    plt.close()
    
    # --- Chart 2: Active Vessels Over Time ---
    mean_active = vessel_timelines.mean(axis=0)
    # median_active = np.median(vessel_timelines, axis=0)
    std_active = vessel_timelines.std(axis=0)
    
    plt.figure(figsize=(8, 5))
    sns.lineplot(x=time_axis, y=mean_active, label="Mean")
    # sns.lineplot(x=time_axis, y=median_active, label="Median", color="orange")
    plt.fill_between(time_axis, mean_active - std_active, mean_active + std_active, alpha=0.3, label="±1 Std Dev")
    plt.title("Average Vessel Presence Over Time")
    plt.xlabel("Time (minutes)")
    plt.ylabel("Number of Active Vessels")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(charts_folder, "vessel_activity_over_time.pdf"))
    plt.close()
    
    # --- Chart 3: Fuel Demand Distribution ---
    plt.figure(figsize=(8, 5))
    sns.histplot(fuel_demands, bins=20, kde=False, color="C1")
    plt.title("Distribution of Total Fuel Demand per Instance")
    plt.xlabel("Total Fuel Demand (kt)")
    plt.ylabel("Number of Instances")
    plt.tight_layout()
    plt.savefig(os.path.join(charts_folder, "fuel_demand_distribution.pdf"))
    plt.close()
    
    # --- Chart 4: Peak Vessel Count ---
    plt.figure(figsize=(8, 5))
    bins = range(min(peak_vessel_counts), max(peak_vessel_counts) + 2)
    sns.histplot(peak_vessel_counts, bins=bins, discrete=True, kde=False, color="C2")
    plt.xticks(bins)
    plt.title("Distribution of Peak Vessel Count per Instance")
    plt.xlabel("Peak Number of Vessels Simultaneously Present")
    plt.ylabel("Number of Instances")
    plt.tight_layout()
    plt.savefig(os.path.join(charts_folder, "peak_vessel_count_distribution.pdf"))
    plt.close()
    
    print("✅ Charts saved to:", charts_folder)

if __name__ == "__main__":
    main()