# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 23:07:25 2025

@author: User
"""

from problem_instance import *
import copy
import json

class VesselState:
    def __init__(self, vessel: Vessel):
        self.vessel = vessel
        self.current_fuel_demand = vessel.fuel_demand #To identify the fuel demand of that specific vessel

class BargeState:
    def __init__(self, barge: Barge):
        self.barge = barge
        self.location = 0 #Initially, the barge starts on the Origin Point (0)
        self.current_fuel = barge.fuel_capacity #Initially, the barge starts with their total capacity fuel
        self.current_vessel_id = None #Initially, the barge isn't connected to any vessel
        self.setup_init_progress = None #Initially, the barge isn't connected to any vessel
        self.setup_end_progress = None #Initially, the barge isn't connected to any vessel
        self.action_queue = [] #Initially, the barge doesn't have any order to follow
        
    def get_speed_knots(self, direction, tide_speed):
        barge_speed_knots = direction * (self.barge.base_move_speed_knots - self.barge.move_speed_per_ton * self.current_fuel)
        return barge_speed_knots + tide_speed


class PortState:
    def __init__(self, problem_instance: ProblemInstance):
        self.time = 0  # Start at time 0
        self.vessel_states = [VesselState(v) for v in problem_instance.vessels]
        self.barge_states = [BargeState(b) for b in problem_instance.barges]
        self.problem_instance = problem_instance
       
    def get_possible_assignments(self):
        #if a barge is assigned to a vessel, other barges cannot go to that vessel
        #if a barge is assigned to a vessel, it cannot be assigned to other vessels
        #if a barge is empty, it cannot be assigned to any vessel
        #a barge cannot be assigned to a vessel that has not arrived or departs in less than 2*problem_instance.vessel_setup_time
        #if a vessel has a current fuel demand = 0, no barge can be assigned to it
        #return a list of possible assignments in a list of tuples format [(barge_id, vessel_id)]
        #if a barge has less than barge.min_fuel, it needs to go to the origin point [(barge_id, 'ORIGIN')] to completely refill
        
        assignments = []
        assigned_vessel_ids = set() #set = list without duplicates
        assigned_barge_ids = set()
    
        # Track currently assigned vessels and barges
        for barge_state in self.barge_states:
            if barge_state.current_vessel_id is not None:
                assigned_barge_ids.add(barge_state.barge.id)
                assigned_vessel_ids.add(barge_state.current_vessel_id)
    
        for barge_state in self.barge_states:
            if barge_state.barge.id in assigned_barge_ids:
                continue  # Skip already assigned barges
            if len(barge_state.action_queue) > 0:
                continue
            if barge_state.current_fuel < barge_state.barge.min_fuel: #compare against barge-specific threshold
                if not 'ORIGIN' in assigned_vessel_ids:
                    assignments.append((barge_state.barge.id, 'ORIGIN'))  #assign to ORIGIN if fuel is too low
                continue  # skip other assignments if not enough fuel (stay idle at the same place until it is free again)

    
            for vessel_state in self.vessel_states:
                vessel = vessel_state.vessel
                if vessel.id in assigned_vessel_ids:
                    continue  # Skip already assigned vessels
                if vessel_state.current_fuel_demand <= 0:
                    continue  # Vessel doesn't need fuel
                if not (vessel.arrival_time <= self.time < vessel.departure_time):
                    continue  # Vessel not at port
                if vessel.departure_time - self.time < 2 * self.problem_instance.vessel_setup_time:
                    continue  # Not enough time to serve
    
                assignments.append((barge_state.barge.id, vessel.id))
    
        return assignments #it returns the complete list with available assignments in that time
    
    def apply_assignment(self, barge_id, target):
        """
        Applies the assignment of a barge to either a vessel (by vessel_id) or to the ORIGIN for refueling.
        """
        barge = next((b for b in self.barge_states if b.barge.id == barge_id), None)
        if barge is None:
            print(f"Barge {barge_id} not found.")
            return
        if target == 'ORIGIN':
            # Assign the barge to return to origin to refill
            barge.current_vessel_id = target #
            barge.action_queue.append('GO:0')
            barge.action_queue.append('SETUP_INIT:ORIGIN')
            barge.action_queue.append('REFUEL')
            barge.action_queue.append('SETUP_END:ORIGIN')
            
        else:
            # Assign to a vessel
            vessel = next((v for v in self.vessel_states if v.vessel.id == target), None)
            if vessel is None:
                print(f"Vessel {target} not found.")
                return
            barge.current_vessel_id = target
            barge.action_queue.append(f'GO:{vessel.vessel.get_position()}')
            barge.action_queue.append(f'SETUP_INIT:{target}')
            barge.action_queue.append(f'FUEL:{target}')
            barge.action_queue.append(f'SETUP_END:{target}')

    def advance_one_minute(self):
        def advance_setup(progress, setup_time):
            return (progress + 1) if progress is not None else 1, (progress + 1) >= setup_time if progress is not None else False
        def knots_to_m_per_minute(knots):
            return knots * 1852 / 60 # conversion rate
        new_state = copy.deepcopy(self)

        # Handle each barge
        for barge_state in new_state.barge_states:
            if not barge_state.action_queue:
                continue  # No action to process
            
            current_action = barge_state.action_queue[0]
            tide_speed = self.problem_instance.get_tide_speed_at(self.time)
            parts = current_action.split(":")
            action = parts[0]

            if action == "GO":
                target = int(parts[1])
                distance_remaining = target - barge_state.location
                direction = 1 if distance_remaining > 0 else -1

                # Calculate effective speed (knots to m/min)
                barge_speed_knots = direction * (barge_state.barge.base_move_speed_knots - barge_state.barge.move_speed_per_ton * barge_state.current_fuel)
                total_speed_knots = barge_speed_knots + tide_speed
                total_speed_m_per_min = knots_to_m_per_minute(total_speed_knots)

                movement = direction * min(abs(distance_remaining), abs(total_speed_m_per_min)) # abs = absolute value = módulo
                barge_state.location += movement

                if abs(barge_state.location - target) < 1e-6: # handle possible floating-point errors, considering a very-small difference (epsilon)
                    barge_state.location = target
                    barge_state.action_queue.pop(0)

            elif action in ["SETUP_INIT", "SETUP_END"]:
                if parts[1] == "ORIGIN":
                    setup_time = self.problem_instance.origin_setup_time
                else:
                    setup_time = self.problem_instance.vessel_setup_time

                is_init = (action == "SETUP_INIT")
                progress_attr = "setup_init_progress" if is_init else "setup_end_progress"

                current_progress = getattr(barge_state, progress_attr)
                new_progress, finished = advance_setup(current_progress, setup_time)
                setattr(barge_state, progress_attr, new_progress)

                if finished: # when an action finishes, it gets removed immediately, so we can perform on another action in the next minute
                    setattr(barge_state, progress_attr, None)
                    if not is_init:
                        barge_state.current_vessel_id = None
                    barge_state.action_queue.pop(0)

            elif action == "REFUEL":
                flow = self.problem_instance.fuel_flow_rate_per_minute
                barge_state.current_fuel = min(barge_state.barge.fuel_capacity, barge_state.current_fuel + flow) # limits the current fuel to the fuel capacity
                if barge_state.current_fuel >= barge_state.barge.fuel_capacity:
                    barge_state.action_queue.pop(0)

            elif action == "FUEL":
                vessel_id = int(parts[1])
                vessel_state = next((v for v in new_state.vessel_states if v.vessel.id == vessel_id), None)
                if vessel_state is None:
                    continue  # Shouldn't happen

                flow = self.problem_instance.fuel_flow_rate_per_minute
                # the transferred volumed is determined between the lowest value among: flow (physical limit), fuel_demand (how much the vessel still needs) and current_fuel (how much the barge can still provide)
                transferred = min(flow, vessel_state.current_fuel_demand, barge_state.current_fuel)

                barge_state.current_fuel -= transferred
                vessel_state.current_fuel_demand -= transferred

                if vessel_state.current_fuel_demand <= 0 or barge_state.current_fuel <= 0 or vessel_state.vessel.departure_time-1 <= self.time + self.problem_instance.vessel_setup_time:
                    barge_state.action_queue.pop(0)

        # Finally, advance the time
        new_state.time += 1

        return new_state
    
    def to_dict(self):
        tide_speed = self.problem_instance.get_tide_speed_at(self.time)
        return {
            "time": self.time,
            "tide_speed": tide_speed,
            "barges": [
                {
                    "id": b.barge.id,
                    "location": b.location,
                    "current_fuel": b.current_fuel,
                    "fuel_capacity": b.barge.fuel_capacity,
                    "current_vessel_id": b.current_vessel_id,
                    "setup_init_progress": b.setup_init_progress,
                    "setup_end_progress": b.setup_end_progress,
                    "action_queue": b.action_queue,
                    "speed": b.get_speed_knots(1, tide_speed)
                }
                for b in self.barge_states
            ],
            "vessels": [
                {
                    "id": v.vessel.id,
                    "position": v.vessel.get_position(),
                    "current_fuel_demand": v.current_fuel_demand,
                    "fuel_demand": v.vessel.fuel_demand,
                    "arrival_time": v.vessel.arrival_time,
                    "departure_time": v.vessel.departure_time
                }
                for v in self.vessel_states
            ]
        }

import random
# Example usage:
if __name__ == "__main__":
    random.seed(6) #calling seed permits to have a fixed initial state
    problem_instance = ProblemInstance.generate()
    port_state = PortState(problem_instance)

