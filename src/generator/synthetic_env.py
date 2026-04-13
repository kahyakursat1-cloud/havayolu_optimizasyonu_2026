import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

class GrandMasterSimulator:
    def __init__(self, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        
        self.airports = {
            'IST': {'capacity': 40, 'delay_factor': 1.2, 'lat': 41.275, 'lon': 28.751},
            'ESB': {'capacity': 15, 'delay_factor': 0.8, 'lat': 40.128, 'lon': 32.995},
            'ADB': {'capacity': 15, 'delay_factor': 0.9, 'lat': 38.292, 'lon': 27.156},
            'AYT': {'capacity': 20, 'delay_factor': 1.1, 'lat': 36.898, 'lon': 30.800},
            'LHR': {'capacity': 10, 'delay_factor': 1.5, 'lat': 51.470, 'lon': -0.454},
            'JFK': {'capacity': 8, 'delay_factor': 1.4, 'lat': 40.641, 'lon': -73.778}
        }
        
        self.aircraft_specs = {
            'B737': {'range': 5000, 'fuel': 15, 'capacity': 180, 'op_cost': 5000, 'cat': 'Narrow'},
            'A320': {'range': 6000, 'fuel': 14, 'capacity': 160, 'op_cost': 4800, 'cat': 'Narrow'},
            'A350': {'range': 15000, 'fuel': 32, 'capacity': 300, 'op_cost': 12000, 'cat': 'Wide'},
            'B787': {'range': 14000, 'fuel': 30, 'capacity': 290, 'op_cost': 11500, 'cat': 'Wide'}
        }
        
        self.aircraft_pool = {f"AC_{i:03d}": random.choice(list(self.aircraft_specs.keys())) for i in range(50)}
        self.crew_pool = {f"CREW_{i:03d}": {'cert': random.choice(['Narrow', 'Wide']), 'duty_mins': 0} for i in range(120)}

    def calculate_distance(self, p1, p2):
        lat1, lon1 = self.airports[p1]['lat'], self.airports[p1]['lon']
        lat2, lon2 = self.airports[p2]['lat'], self.airports[p2]['lon']
        return np.sqrt((lat1-lat2)**2 + (lon1-lon2)**2) * 111

    def generate_grand_scenario(self, days=1):
        flights = []
        start_date = datetime(2026, 6, 1, 0, 0)
        
        for day in range(days):
            current_day = start_date + timedelta(days=day)
            for i in range(random.randint(80, 120)):
                origin = random.choice(list(self.airports.keys()))
                destination = random.choice([a for a in self.airports.keys() if a != origin])
                dist = self.calculate_distance(origin, destination)
                
                hour = random.choices(range(24), weights=[1,1,1,2,6,10,12,10,8,6,5,5,6,8,10,12,10,8,6,4,3,2,1,1])[0]
                departure_time = current_day + timedelta(hours=hour, minutes=random.randint(0, 59))
                
                block_time = int(dist / 8) + 40
                arrival_time = departure_time + timedelta(minutes=block_time)
                
                demand = random.randint(80, 320)
                ac_id = random.choice(list(self.aircraft_pool.keys()))
                ac_type = self.aircraft_pool[ac_id]
                crew_id = random.choice(list(self.crew_pool.keys()))
                
                flights.append({
                    'flight_id': f"TK{2000 + len(flights)}",
                    'origin': origin,
                    'destination': destination, # Consistent with dt_solver
                    'dist_km': dist,
                    'departure_time': departure_time,
                    'arrival_time': arrival_time,
                    'block_time': block_time, # For K4 (Crew Duty)
                    'slot_start': departure_time - timedelta(minutes=15),
                    'slot_end': departure_time + timedelta(minutes=15),
                    'demand': demand,
                    'ac_id': ac_id,
                    'ac_type': ac_type,
                    'ac_cat': self.aircraft_specs[ac_type]['cat'],
                    'ac_range_km': self.aircraft_specs[ac_type]['range'], # GA consistency
                    'ac_capacity': self.aircraft_specs[ac_type]['capacity'],
                    'crew_id': crew_id,
                    'crew_cert': self.crew_pool[crew_id]['cert'],
                    'revenue_tl': demand * random.randint(300, 1200),
                    'fuel_cost_tl': dist * self.aircraft_specs[ac_type]['fuel'],
                    'op_cost_tl': self.aircraft_specs[ac_type]['op_cost'],
                    'delay_cost_per_min': 600
                })
        
        return pd.DataFrame(flights)
