from port_state import ProblemInstance, PortState
import random
import json
import os
import datetime


class RandomAlgorithm:
    def choose(self, assignments, state: PortState):
        return random.choice(assignments) #to choose a random assignment
    
class GreedyAlgorithm:
    def choose(self, assignments, state: PortState):
        best_score = None
        best_assignment = None
    
        for barge_id, vessel_id in assignments:
            # if a barge must go to the origin, it doesn't need to compete. we just allow it to go.
            if vessel_id == 'ORIGIN':
                return (barge_id, vessel_id)
            
            barge_state = next(b for b in state.barge_states if b.barge.id == barge_id)
            vessel_state = next(v for v in state.vessel_states if v.vessel.id == vessel_id)
    
            remaining_time = vessel_state.vessel.departure_time - state.time # how much time left we have to supply this vessel
            fuel_ratio = vessel_state.current_fuel_demand / max(remaining_time, 1) # to determine the vessel's demand/remaining_time ratio
            can_fully_supply = barge_state.current_fuel >= vessel_state.current_fuel_demand # to understand if the barge has enough fuel to supply the vessel
            distance = abs(barge_state.location - vessel_state.vessel.get_position()) # to get the barge that's closest to the vessel
    
            # Build a scoring tuple (higher is better)
            # Use negatives where lower is better (like distance)
            score = (
                fuel_ratio,                    # 1. higher is better
                int(can_fully_supply),         # 2. full supply: 1 > 0
                barge_state.current_fuel if not can_fully_supply else 0,  # 3. more fuel if can't fully supply
                -distance                     # 4. closer is better
            )
    
            if best_score is None or score > best_score:
                best_score = score
                best_assignment = (barge_id, vessel_id)
    
        return best_assignment

def main():
    instances_folder = 'instances'
    solutions_folder = 'solutions'
    os.makedirs(solutions_folder, exist_ok=True)  # Ensure the output folder exists
    algorithm = GreedyAlgorithm()
    
    start_time = datetime.datetime.now()
    
    for filename in sorted(os.listdir(instances_folder)):
        if filename.endswith('.json'):
            instance_path = os.path.join(instances_folder, filename)
            solution_filename = f"solution_{filename.split('_')[-1]}"
            solution_path = os.path.join(solutions_folder, solution_filename)
    
            print(f"Running simulation for {filename}")
            with open(instance_path) as file:
                instance = ProblemInstance.from_json(json.load(file))
            port_state = PortState(instance)
            states = []
            
            max_time = max(v.departure_time for v in instance.vessels)
    
            while port_state.time <= max_time:  # Simulate until the last vessel departs
                states.append(port_state.to_dict())
                assignments = port_state.get_possible_assignments()
    
                while assignments:
                    assignment_choice = algorithm.choose(assignments, port_state)
                    # print(f't={port_state.time} {assignment_choice}')
                    port_state.apply_assignment(assignment_choice[0], assignment_choice[1])
                    assignments = port_state.get_possible_assignments()
    
                port_state = port_state.advance_one_minute()
    
            with open(solution_path, 'w') as solution_file:
                json.dump(states, solution_file)
            print(f"Saved solution to {solution_path}")
        
        end_time = datetime.datetime.now()
        
        with open("./times.txt", 'w') as times_file:
            times_file.write("\n".join([
                f"Started at {start_time}",
                f"Finished at {end_time}",
                f"Total runtime: {end_time - start_time}",
                ]))
            

if __name__ == "__main__":
    main()