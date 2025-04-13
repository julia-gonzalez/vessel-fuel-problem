import random
import json
from typing import List, Self
import math

DISTANCE_BETWEEN_POINTS_IN_METERS = 370
NUMBER_OF_POINTS = 67 # total 68, as 0 is the source

VESSEL_MIN_STAY_TIME_MINUTES = 6*60 # 6 hours
VESSEL_MAX_STAY_TIME_MINUTES = 12*60 # 12 hours

VESSEL_MIN_FUEL_DEMAND = 1000 # in tons
VESSEL_MAX_FUEL_DEMAND = 2000 # in tons

BARGE_BASE_MOVE_SPEED = 4 # the move speed, in knots, of an EMPTY barge with NO TIDE influence
MOVE_SPEED_PER_TON = -0.001 # for each ton of fuel carried by the barge, how much does it impact its speed in ABSOLUTE terms

BARGE_FUEL_CAPACITY_OPTIONS = [2500, 5000] # in tons

TIDE_AMPLITUDE = 2
TIDE_PERIOD = 24 * 60  # minutes in a day
FUEL_FLOW_RATE_PER_MINUTE = 500 / 60
ORIGIN_SETUP_TIME = 60
VESSEL_SETUP_TIME = 60

NUM_BARGES = 7 #according to https://transpetro.com.br/transpetro-institucional/noticias/transpetro-lucra-r-866-milhoes-em-2024-e-mira-expansao-dos-negocios.htm#:~:text=Transpetro%20lucra%20R%24%20866%20milh%C3%B5es%20em%202024%20e%20mira%20expans%C3%A3o%20dos%20neg%C3%B3cios,-27%2F02%2F2025&text=A%20Transpetro%20registrou%20lucro%20de,mais%20que%20no%20ano%20anterior.

MEAN_VESSELS = 30 #mu (mean) is the average number of vessels.

STD_VESSELS = 5 #sigma (standard deviation) controls the spread of values.

MIN_FUEL = 0.05 #if a barge has less than this amount, it must refuel

class Vessel:
    def __init__(self, vessel_id: int, arrival_time: int, departure_time: int, fuel_demand: int, point: int):
        self.id = vessel_id
        self.name = f"vessel_{self.id}"
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.fuel_demand = fuel_demand
        self.point = point
    
    def get_position(self):
        """
        Gets the distance between the vessel's point and the origin
        """
        return self.point * DISTANCE_BETWEEN_POINTS_IN_METERS
    
    # @staticmethod comes from python's standard library to declare a class method, instead of an instance method
    @staticmethod
    def generate(vessel_id: int, min_time: int, max_time: int, existing_vessels: list[Self]):
        arrival_time = random.randint(min_time, max_time)
        while True:
            generated = Vessel(
                vessel_id=vessel_id,
                arrival_time=arrival_time,
                departure_time=arrival_time + random.randint(VESSEL_MIN_STAY_TIME_MINUTES, VESSEL_MAX_STAY_TIME_MINUTES),
                fuel_demand=random.randint(VESSEL_MIN_FUEL_DEMAND, VESSEL_MAX_FUEL_DEMAND),
                point=random.randint(1, NUMBER_OF_POINTS)
            )
            has_collision = False
            for vessel in existing_vessels:
                if generated.collides(vessel):
                    has_collision = True
                    break
            if not has_collision:
                return generated
    
    def collides(self, other: Self):
        return self.get_position() == other.get_position() \
                and self.departure_time > other.arrival_time \
                and self.arrival_time < other.departure_time
    
    # JSON is a format that can be saved to a text file
    def to_json(self):
        return json.dumps(self.__dict__, indent=4)
    
    @staticmethod
    def from_json(data: str | dict) -> Self:
        if isinstance(data, str):
            data = json.loads(data)
    
        return Vessel(
            vessel_id=data["id"],
            arrival_time=data["arrival_time"],
            departure_time=data["departure_time"],
            fuel_demand=data["fuel_demand"],
            point=data["point"]
        )


class Barge:
    def __init__(self, barge_id: int, fuel_capacity: int):
        self.id = barge_id
        self.name = f"barge_{self.id}"
        self.fuel_capacity = fuel_capacity
        self.min_fuel = fuel_capacity*MIN_FUEL  #if a barge has less than this amount, it must refuel
        self.base_move_speed_knots = BARGE_BASE_MOVE_SPEED
        self.move_speed_per_ton = MOVE_SPEED_PER_TON
    
    @staticmethod
    def generate(barge_id: int):
        return Barge(
            barge_id=barge_id,
            fuel_capacity=random.choice(BARGE_FUEL_CAPACITY_OPTIONS),
        )
    
    def to_json(self):
        return json.dumps(self.__dict__, indent=4)
    
    @staticmethod
    def from_json(data: str | dict) -> Self:
        if isinstance(data, str):
            data = json.loads(data)
    
        barge = Barge(
            barge_id=data["id"],
            fuel_capacity=data["fuel_capacity"]
        )
        barge.base_move_speed_knots = data["base_move_speed_knots"]
        barge.move_speed_per_ton = data["move_speed_per_ton"]
        return barge

class ProblemInstance:
    def __init__(self, vessels: List[Vessel], barges: List[Barge]):
        self.vessels = vessels
        self.barges = barges
        self.tide_amplitude = TIDE_AMPLITUDE
        self.tide_period = TIDE_PERIOD
        self.fuel_flow_rate_per_minute = FUEL_FLOW_RATE_PER_MINUTE
        self.origin_setup_time = ORIGIN_SETUP_TIME
        self.vessel_setup_time = VESSEL_SETUP_TIME
    
    def get_tide_speed_at(self: Self, t: int):
        return self.tide_amplitude * math.sin(2 * math.pi * t / self.tide_period) # converts a 2*pi period to a 24h period
    
    @staticmethod
    def generate():
        num_vessels = max(7, int(random.gauss(mu=MEAN_VESSELS, sigma=STD_VESSELS)))  # Generate a reasonable number of vessels, considering a normal distribution
        # Guarantee enough barges, but not too many
        # Barges is always between vessels/3 and vessels/2
        num_barges = NUM_BARGES
        #(OLD) num_barges = random.randint(max(1, num_vessels // 3), max(2, num_vessels // 2))
        
        vessels = []
        for i in range(num_vessels):
            vessels.append(Vessel.generate(vessel_id=i+1, min_time=0, max_time=24*60, existing_vessels=vessels)) # Arrive randomly in a day
        barges = [Barge.generate(barge_id=i+1) for i in range(num_barges)]
        
        return ProblemInstance(vessels=vessels, barges=barges)
    
    def to_json(self):
        return json.dumps({
            **self.__dict__,
            "vessels": [json.loads(v.to_json()) for v in self.vessels],
            "barges": [json.loads(b.to_json()) for b in self.barges],
        }, indent=4)
    
    @staticmethod
    def from_json(data: str | dict) -> Self:
        if isinstance(data, str):
            data = json.loads(data)
    
        vessels = [Vessel.from_json(v) for v in data["vessels"]]
        barges = [Barge.from_json(b) for b in data["barges"]]
        instance = ProblemInstance(vessels=vessels, barges=barges)
    
        instance.tide_amplitude = data['tide_amplitude']
        instance.tide_period = data['tide_period']
        instance.fuel_flow_rate_per_minute = data['fuel_flow_rate_per_minute']
        
        return instance
