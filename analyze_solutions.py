import pickle
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
    
def get_delivered_fuel_percentage(state, total_demand):
    if total_demand == 0:
        return 1
    current_demand = sum(vessel['current_fuel_demand'] for vessel in state['vessels'])
    delivered_demand = total_demand - current_demand
    return delivered_demand / total_demand

def get_stats(solution_path):
    print("Reading file", solution_path)
    with open(solution_path, 'rb') as solution_file:
        solution = pickle.load(solution_file)
    initial_state = solution[0]

    # Get initial vessel demands
    total_demand = sum(vessel['current_fuel_demand'] for vessel in initial_state['vessels'])
    delivered_over_time = [get_delivered_fuel_percentage(state, total_demand) for state in solution]
    
    max_departure = len(solution)
    
    timeline = np.zeros(max_departure + 1, dtype=int)
    for vessel in solution[0]['vessels']:
        timeline[vessel["arrival_time"]:vessel["departure_time"]] += 1
    peak_vessel_count = timeline.max()

    return {
        "max_departure": max_departure,
        "peak_vessel_count": peak_vessel_count,
        "delivered_over_time": delivered_over_time,
        "total_delivery": delivered_over_time[-1] # -1 represent the last state of the list
    }
    

def main():
    # Configuration
    greedy_folder = "solutions_greedy"
    random_folder = "solutions_random"
    
    greedy_stats = [get_stats(os.path.join(greedy_folder, file)) for file in os.listdir(greedy_folder)]
    random_stats = [get_stats(os.path.join(random_folder, file)) for file in os.listdir(random_folder)]
    
    sns.set()
    sns.set_palette("bright")
    greedy_total_deliveries = [100*s['total_delivery'] for s in greedy_stats]
    random_total_deliveries = [100*s['total_delivery'] for s in random_stats]
    
    max_departures = [s['max_departure']/60 for s in greedy_stats]
    peak_vessel_counts = [s['peak_vessel_count'] for s in greedy_stats]
    
    delivered_df = pd.DataFrame([{"minute": minute, "delivered":100*delivered, "instance_id": instance_id} for (instance_id, s) in enumerate(greedy_stats) for (minute, delivered) in enumerate(s['delivered_over_time'])])
    delivered_random = pd.DataFrame([{"minute": minute, "delivered":100*delivered, "instance_id": instance_id} for (instance_id, s) in enumerate(random_stats) for (minute, delivered) in enumerate(s['delivered_over_time'])])
    
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    # ==== Visualization ====
    # Correlation between total delivery and peak vessel count
    plt.figure(figsize=(10, 4))
    # plt.scatter(x=peak_vessel_counts ,y=greedy_total_deliveries)
    sns.boxplot(x=peak_vessel_counts ,y=greedy_total_deliveries, color="white")
    plt.title("Correlation between Peak Vessel and Delivered Fuel")
    plt.xlabel("Peak Number of Vessels Simultaneously Present")
    plt.ylabel('Delivered Fuel (%)')
    # plt.xticks(np.arange(min(peak_vessel_counts), max(peak_vessel_counts)+1, 1))
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'delivery_x_peak_vessel.pdf'))
    
    # Correlation between total delivery and max departure time
    plt.figure(figsize=(10, 4))
    plt.scatter(x=max_departures ,y=greedy_total_deliveries)
    plt.title("Correlation between Simulated Time and Delivered Fuel")
    plt.xlabel("Simulated Time (h)")
    plt.ylabel('Delivered Fuel (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'delivery_x_total_time.pdf'))
    
    # Histogram of delivery ratios
    plt.figure(figsize=(10, 4))
    plt.hist(greedy_total_deliveries, bins=20, label="Greedy")
    plt.title('Distribution of Delivered Fuel (%)')
    plt.xlabel('Delivered Fuel (%)')
    plt.ylabel('Number of Instances')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'total_delivered_fuel.pdf'))
    
    # Histogram of delivery ratios
    plt.figure(figsize=(10, 4))
    plt.hist(greedy_total_deliveries, bins=20, label="Greedy")
    plt.hist(random_total_deliveries, bins=20, color="C1", label="Random", alpha=0.5)
    plt.title('Distribution of Delivered Fuel (%)')
    plt.xlabel('Delivered Fuel (%)')
    plt.ylabel('Number of Instances')
    plt.tight_layout()
    plt.legend(loc='lower right')
    plt.savefig(os.path.join(results_dir, 'total_delivered_fuel_vs_random.pdf'))
    
    # # Line plot of delivery ratio across instances
    plt.figure(figsize=(10, 4))
    # Using standard deviation: https://seaborn.pydata.org/tutorial/error_bars.html#standard-error-bars
    sns.lineplot(data=delivered_df, x='minute', y='delivered', errorbar="sd")
    plt.title('Delivered Fuel (%) Per Minute')
    plt.xlabel('Time (min)')
    plt.ylabel('Delivered Fuel (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'delivery_over_time.pdf'))
    
    # # Line plot of delivery ratio across instances
    plt.figure(figsize=(10, 4))
    # Using standard deviation: https://seaborn.pydata.org/tutorial/error_bars.html#standard-error-bars
    sns.lineplot(data=delivered_df, x='minute', y='delivered', errorbar="sd", label="Greedy")
    sns.lineplot(data=delivered_random, x='minute', y='delivered', errorbar="sd", color="C1", label="Random")
    plt.title('Delivered Fuel (%) Per Minute')
    plt.xlabel('Time (min)')
    plt.ylabel('Delivered Fuel (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'delivery_over_time_vs_random.pdf'))
    
    ranges = [(0,25), (25,50), (50,75), (75, 100)]
    latex_table = []
    latex_table.append("\\begin{table}[htb]")
    latex_table.append("\\centering")
    latex_table.append("\\begin{tabular}{rr}")
    latex_table.append("\\toprule")
    latex_table.append("\\textbf{Range (\\%)} & \\textbf{Number of instances} \\\\")
    latex_table.append("\\midrule")
    
    for (lower, upper) in ranges:
        count = sum(lower < v <= upper for v in greedy_total_deliveries)
        latex_table.append(f"({lower}, {upper}] & {count} \\\\")
    
    latex_table.append("\\bottomrule")
    latex_table.append("\\end{tabular}")
    latex_table.append("\\caption{Distribution of Delivery Percentages Across Ranges}")
    latex_table.append("\\label{tab:delivery_distribution}")
    latex_table.append("\\end{table}")
    with open(os.path.join(results_dir, 'ranges.tex'), "w") as f:
        f.write("\n".join(latex_table))
    
    examples = []
    for (lower, upper) in ranges:
        for iid, v in enumerate(greedy_total_deliveries):
            if lower < v <= upper:
                examples.append(f"Range{(lower, upper)}, Instance: {iid}, Percentage: {round(v)}")
                break
    for iid, v in enumerate(greedy_total_deliveries):
        if v == 100:
            examples.append(f"100%, Instance: {iid}, Percentage: {round(v)}")
            break
    with open(os.path.join(results_dir, 'examples.tex'), "w") as f:
        f.write("\n".join(examples))

if __name__ == "__main__":
    main()