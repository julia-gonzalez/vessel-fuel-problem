import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def main():
    # Configuration
    solution_folder = "solutions"
    
    def get_delivered_fuel_percentage(state, total_demand):
        if total_demand == 0:
            return 1
        current_demand = sum(vessel['current_fuel_demand'] for vessel in state['vessels'])
        delivered_demand = total_demand - current_demand
        return delivered_demand / total_demand
    
    instance_stats = []
    
    instances_with_zero = []
    
    for file in os.listdir(solution_folder):
        print("Reading file", file)
        file_path = os.path.join(solution_folder, file)
    
        with open(file_path) as json_file:
            solution = json.load(json_file)
        initial_state = solution[0]
    
        # Get initial vessel demands
        total_demand = sum(vessel['current_fuel_demand'] for vessel in initial_state['vessels'])
        if total_demand == 0:
            instances_with_zero.append(file)
        delivered_over_time = [get_delivered_fuel_percentage(state, total_demand) for state in solution]
    
    
        instance_stats.append({
            "delivered_over_time": delivered_over_time,
            "total_delivery": delivered_over_time[-1] # -1 represent the last state of the list
        })
    
    sns.set()
    total_deliveries = [100*s['total_delivery'] for s in instance_stats]
    
    delivered_df = pd.DataFrame([{"minute": minute, "delivered":100*delivered, "instance_id": instance_id} for (instance_id, s) in enumerate(instance_stats) for (minute, delivered) in enumerate(s['delivered_over_time'])])
    
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    # ==== Visualization ====
    # Histogram of delivery ratios
    plt.figure(figsize=(10, 4))
    plt.hist(total_deliveries, bins=20)
    plt.title('Distribution of Delivered Fuel (%)')
    plt.xlabel('Delivered Fuel (%)')
    plt.ylabel('Number of Instances')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'total_delivered_fuel.pdf'))
    
    # # Line plot of delivery ratio across instances
    plt.figure(figsize=(10, 4))
    # Using standard deviation: https://seaborn.pydata.org/tutorial/error_bars.html#standard-error-bars
    sns.lineplot(data=delivered_df, x='minute', y='delivered', errorbar="sd")
    plt.title('Delivered Fuel (%) Per Minute')
    plt.xlabel('Time (min)')
    plt.ylabel('Delivered Fuel (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'delivery_over_time.pdf'))
    
    ranges = [(0,25), (25,50), (50,75), (75, 100)]
    latex_table = []
    latex_table.append("\\begin{table}[htb]")
    latex_table.append("\\centering")
    latex_table.append("\\begin{tabular}{rr}")
    latex_table.append("\\toprule")
    latex_table.append("\\textbf{Range (\\%)} & \\textbf{Number of instances} \\\\")
    latex_table.append("\\midrule")
    
    for (lower, upper) in ranges:
        count = sum(lower < v <= upper for v in total_deliveries)
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
        for iid, v in enumerate(total_deliveries):
            if lower < v <= upper:
                examples.append(f"Range{(lower, upper)}, Instance: {iid}, Percentage: {round(v)}")
                break
    for iid, v in enumerate(total_deliveries):
        if v == 100:
            examples.append(f"100%, Instance: {iid}, Percentage: {round(v)}")
            break
    with open(os.path.join(results_dir, 'examples.tex'), "w") as f:
        f.write("\n".join(examples))
    
    print("Instances with no demand", instances_with_zero)

if __name__ == "__main__":
    main()