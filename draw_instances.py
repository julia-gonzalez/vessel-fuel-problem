import matplotlib.pyplot as plt
from problem_instance import ProblemInstance
import os
import json

# To visualize the instances

def plot_gantt_chart(vessels, chart_path, instance_id):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for vessel in vessels:
        bar = ax.barh(
            y=vessel.point, 
            width=(vessel.departure_time - vessel.arrival_time) / 60,  # Convert minutes to hours
            left=vessel.arrival_time / 60,  # Convert minutes to hours
            color="skyblue"
        )
        
        # Place vessel number inside the bar
        ax.text(
            vessel.arrival_time / 60 + (vessel.departure_time - vessel.arrival_time) / 120,  # Centered inside the bar
            vessel.point, 
            vessel.id,  # Vessel number
            va='center', ha='center', fontsize=9, color='black', fontweight='bold'
        )

    ax.set_xlabel("Time (Hours)")
    ax.set_ylabel("Points")
    ax.set_title(f"Vessel Arrival and Departure Schedule by Points (Instance {instance_id})")
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.savefig(chart_path)
    plt.close(fig)
    

def main():
    instances_folder = 'instances'
    gantt_folder = 'gantt_charts'
    os.makedirs(gantt_folder, exist_ok=True)
    
    for filename in sorted(os.listdir(instances_folder)):
        if filename.endswith('.json'):
            instance_path = os.path.join(instances_folder, filename)
            instance = ProblemInstance.from_json(json.load(open(instance_path)))
            instance_id = filename.split('_')[-1].replace('.json', '')
    
            print(f"Generating Gantt chart for {filename}")
            chart_filename = f"gantt_{instance_id}.png"
            chart_path = os.path.join(gantt_folder, chart_filename)
            plot_gantt_chart(instance.vessels, chart_path,  instance_id)


if __name__ == "__main__":
    main()