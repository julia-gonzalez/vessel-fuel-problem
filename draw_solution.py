import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import os


from port_state import *

def draw_state(ax, data):
    ax.clear()
    max_distance_km = 25
    point_spacing_km = 0.37  # 370 meters
    barge_count = len(data['barges'])
    barge_ys = list(reversed([i * 0.6 for i in range(barge_count)]))  # increased spacing

    # Draw 370m markers
    for x in range(0, int(max_distance_km / point_spacing_km) + 1):
        ax.axvline(x * point_spacing_km, color='lightgray', linestyle='--', linewidth=0.5)

    # Tide speed indicator (with arrow)
    tide = data['tide_speed']
    tide_color = 'blue' if tide > 0 else 'red' if tide < 0 else 'gray'
    tide_arrow_dx = 0.5 if tide > 0 else -0.5 if tide < 0 else 0
    ax.arrow(max_distance_km / 2, barge_ys[0] + 1.8, tide_arrow_dx, 0, head_width=0.15, head_length=0.2, fc=tide_color, ec=tide_color)
    ax.text(max_distance_km / 2, barge_ys[0] + 2.1, f"Tide: {tide:+.2f} kn", color=tide_color, fontsize=12, fontweight='bold', ha='center')

    # Plot vessels
    vessel_y = barge_ys[0] + 0.9
    for i, vessel in enumerate(data['vessels']):
        if vessel['arrival_time'] > data['time'] or vessel['departure_time'] <= data['time']:
            continue
        x = vessel['position'] / 1000
        ax.plot(x, vessel_y, marker='s', markersize=14, color='black')
        ax.text(x, vessel_y-0.05, vessel['id'], ha='center', fontsize=9, color='white', fontweight='bold')

        total = vessel['fuel_demand']
        remaining = vessel['current_fuel_demand']
        demand_ratio = remaining / total if total > 0 else 0
        ax.add_patch(patches.Rectangle((x - 0.25, vessel_y - 0.25), 0.5, 0.05, color='lightgray'))
        ax.add_patch(patches.Rectangle((x - 0.25, vessel_y - 0.25), 0.5 * demand_ratio, 0.05, color='teal'))
        
        # Clock showing minutes until departure
        total_time = vessel['departure_time'] - vessel['arrival_time']
        time_left = vessel['departure_time'] - data['time']
        if total_time > 0:
            ratio = max(0, min(1, time_left / total_time))
            clock_radius = 0.12
            # Background circle
            ax.add_patch(patches.Circle((x, vessel_y + 0.3), clock_radius, color='lightgray'))
            # Wedge for remaining time
            angle = 360 * ratio
            face_color = 'lime' if time_left > 120 else 'orange'
            ax.add_patch(patches.Wedge((x, vessel_y + 0.3), clock_radius, 90, 90 - angle, facecolor=face_color))
            ax.text(x, vessel_y + 0.26, f"{time_left/60:.0f}h", ha='center', color="black", fontsize=7)

    # Plot barges
    action_colors = {
        'GO': 'orange',
        'SETUP_INIT': 'green',
        'SETUP_END': 'red',
        'REFUEL': 'blue',
        'FUEL': 'purple',
        'IDLE': 'gray'
    }

    for i, barge in enumerate(data['barges']):
        x = barge['location'] / 1000
        y = barge_ys[i]

        capacity = barge['fuel_capacity']
        fuel_ratio = barge['current_fuel'] / capacity if capacity > 0 else 0
        action = barge['action_queue'][0].split(':')[0] if barge['action_queue'] else 'IDLE'
        color = action_colors.get(action.upper(), 'gray')

        # Draw barge marker with full opacity color by action
        ax.plot(x, y, marker='o', markersize=10, color=color)

        # Show barge ID
        ax.text(x, y + 0.25, f"B{barge['id']}", ha='center', fontsize=9, fontweight='bold')

        # Show current action
        ax.text(x, y - 0.35, action, ha='center', fontsize=8)

        # Fuel bar
        ax.add_patch(patches.Rectangle((x - 0.25, y+0.15), 0.5, 0.05, color='lightgray'))
        ax.add_patch(patches.Rectangle((x - 0.25, y+0.15), 0.5 * fuel_ratio, 0.05, color=color))

        # Speed
        speed = barge['speed']
        ax.text(x + 0.5, y-0.1, f"{speed:.1f} kn", fontsize=7, ha='center', color='black')
        
        # Connection visualization
        if barge.get('current_vessel_id') is not None:
            vessel = next((v for v in data['vessels'] if v['id'] == barge['current_vessel_id']), None)
            if vessel:
                vessel_x = vessel['position'] / 1000
                vessel_y = barge_ys[0] + 0.9
                progress = 0
                if action == 'SETUP_INIT':
                    progress = min(1.0, (barge.get('setup_init_progress') or 0) / 60)
                elif action == 'SETUP_END':
                    progress = min(1.0, (barge.get('setup_end_progress') or 0) / 60)
                if action in ['SETUP_INIT', 'SETUP_END']:
                    ax.plot([x, vessel_x], [y, y + (vessel_y-y)*progress], color=color, linestyle='-', linewidth=2)
                elif action == 'FUEL':
                    ax.plot([x, vessel_x], [y, vessel_y], color=color, linestyle='-', linewidth=2)

    ax.set_xlim(-1, max_distance_km)
    ax.set_ylim(-1, barge_ys[0] + 2.5)
    ax.set_xlabel("Distance from Origin (km)")
    ax.set_yticks([])
    # Add secondary x-axis at the top for docking point labels
    secax = ax.secondary_xaxis('top')
    num_points = 68
    tick_positions = [i * point_spacing_km for i in range(num_points)]
    tick_labels = [f"D{i}" if i > 0 else "Origin" for i in range(num_points)]
    secax.set_xticks(tick_positions)
    secax.set_xticklabels(tick_labels, rotation=45, fontsize=8)
    secax.set_xlabel("Docking Point Index")

    ax.set_title(f"Port State at Minute {data['time']}", fontsize=14)
    plt.tight_layout()


def main(solution_id = 6):
    os.makedirs("animations", exist_ok=True)
    solution_file = f'solutions/solution_{solution_id:04d}.json'
    animation_file = f'animations/animation_{solution_id:04d}.gif'
    states = json.load(open(solution_file, 'r'))
    def update(frame):
        print("%.2f" % (100*frame/len(states)), '%')
        draw_state(ax, states[frame])
    
    fig, ax = plt.subplots(figsize=(16, 6))
    anim = FuncAnimation(fig, update, frames=len(states), interval=200)  # interval in ms
    # fps = frames per second = simulation minutes per real second - in this example, 1sec=5min
    anim.save(animation_file, fps=5) # saving the gif animation representing the json file


if __name__ == "__main__":
    main()