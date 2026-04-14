import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

class AdvancedAirlineSimulator:
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
            'B737': {'range': 5000, 'fuel': 15, 'capacity': 180, 'op_cost': 5000, 'cat': 'Narrow', 'co2': 3.1},
            'A320': {'range': 6000, 'fuel': 14, 'capacity': 160, 'op_cost': 4800, 'cat': 'Narrow', 'co2': 3.0},
            'A350': {'range': 15000, 'fuel': 32, 'capacity': 300, 'op_cost': 12000, 'cat': 'Wide', 'co2': 2.8},
            'B787': {'range': 14000, 'fuel': 30, 'capacity': 290, 'op_cost': 11500, 'cat': 'Wide', 'co2': 2.7},
            # v22.0 Propulsions
            'Alice-E': {'range': 440, 'fuel': 1, 'capacity': 9, 'op_cost': 500, 'cat': 'Narrow', 'co2': 0.0},
            'ZeroAvia-H2': {'range': 1800, 'fuel': 4, 'capacity': 60, 'op_cost': 2000, 'cat': 'Narrow', 'co2': 0.5}
        }
        }
        
        self.aircraft_pool = {
            f"AC_{i:03d}": {
                'type': random.choice(list(self.aircraft_specs.keys())),
                'remaining_fh': random.randint(15, 60),
                'maintenance_station': 'IST'
            } for i in range(50)
        }
        self.crew_pool = {
            f"CREW_{i:03d}": {
                'cert': random.choice(['Narrow', 'Wide']), 
                'duty_mins': 0,
                'base_fatigue': random.randint(0, 15)
            } for i in range(120)
        }

    def calculate_distance(self, p1, p2):
        lat1, lon1 = self.airports[p1]['lat'], self.airports[p1]['lon']
        lat2, lon2 = self.airports[p2]['lat'], self.airports[p2]['lon']
        return np.sqrt((lat1-lat2)**2 + (lon1-lon2)**2) * 111

    def _is_electric(self, ac_type):
        return ac_type == "Alice-E"

    def _is_hydrogen(self, ac_type):
        return ac_type == "ZeroAvia-H2"

    def generate_full_scenario(self, days=1):
        """
        🚀 v15.0 "Aviation Excellence" Simulator: 
        Integrated Weather risks, Technical failure probabilities, and Causal Factors.
        """
        flights = []
        from datetime import timezone
        start_date = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        
        # v15.0 Excellence: Define Base Causal Probabilities
        causal_weights = {
            'Weather': 0.15,
            'Security': 0.05,
            'Technical': 0.10,
            'Personnel': 0.20,
            'Cyber': 0.05,
            'Operational': 0.45
        }
        
        for day in range(days):
            current_day = start_date + timedelta(days=day)
            num_flights = random.randint(120, 150) # Increased density for stress testing
            
            for i in range(num_flights):
                origin = random.choice(list(self.airports.keys()))
                destination = random.choice([a for a in self.airports.keys() if a != origin])
                dist = self.calculate_distance(origin, destination)
                
                # Demand-Weight Distribution
                hour = random.choices(range(24), weights=[1,1,1,2,6,10,12,10,8,6,5,5,6,8,10,12,10,8,6,4,3,2,1,1])[0]
                departure_time = current_day + timedelta(hours=hour, minutes=random.randint(0, 59))
                
                block_time = int(dist / 8) + 40
                arrival_time = departure_time + timedelta(minutes=block_time)
                
                ac_id = random.choice(list(self.aircraft_pool.keys()))
                ac_type = self.aircraft_pool[ac_id]['type']
                capacity = self.aircraft_specs[ac_type]['capacity']
                
                # Business/Leisure Segmentation
                business_pax = min(random.randint(10, 60), int(capacity * 0.2))
                leisure_pax = min(random.randint(70, 260), capacity - business_pax)
                passenger_count = business_pax + leisure_pax
                load_factor = passenger_count / capacity
                
                is_night = 1 if (departure_time.hour >= 22 or departure_time.hour <= 6) else 0
                
                # O&D / MCT Analysis: Hub Density Impact
                # IST is a major hub; ESB/ADB are regional. LHR/JFK are international.
                hub_density = self.airports[destination]['delay_factor']
                pax_connection_count = random.randint(10, 60) if hub_density > 1.2 else random.randint(0, 20)
                
                # v15.0 Risks & Attribution
                weather_risk = random.uniform(0.01, 0.15) * hub_density
                tech_risk = random.uniform(0.01, 0.05)
                causal_factor = random.choices(list(causal_weights.keys()), weights=list(causal_weights.values()))[0]
                
                contrail_risk = random.uniform(0.1, 0.4)
                if is_night == 1: contrail_risk += 0.2
                
                rem_fh = self.aircraft_pool[ac_id]['remaining_fh']
                crew_id = random.choice(list(self.crew_pool.keys()))
                
                flights.append({
                    'flight_id': f"TK{2000 + len(flights)}",
                    'origin': origin,
                    'destination': destination, 
                    'dist_km': dist,
                    'departure_time': departure_time,
                    'arrival_time': arrival_time,
                    'block_time': block_time, 
                    'business_pax': business_pax,
                    'leisure_pax': leisure_pax,
                    'passenger_count': passenger_count,
                    'pax_connection_count': pax_connection_count,
                    'load_factor': load_factor,
                    'aircraft_id': ac_id,
                    'ac_type': ac_type,
                    'ac_cat': self.aircraft_specs[ac_type]['cat'],
                    'ac_range_km': self.aircraft_specs[ac_type]['range'],
                    'ac_remaining_fh': rem_fh,
                    'ac_capacity': capacity,
                    'crew_id': crew_id,
                    'crew_cert': self.crew_pool[crew_id]['cert'],
                    'crew_base_fatigue': self.crew_pool[crew_id]['base_fatigue'],
                    'is_night_flight': is_night,
                    'contrail_risk': contrail_risk,
                    'weather_risk': weather_risk,
                    'tech_failure_prob': tech_risk,
                    'causal_factor': causal_factor,
                    'revenue_tl': (business_pax * 3500) + (leisure_pax * 1200),
                    'fuel_cost_tl': dist * self.aircraft_specs[ac_type]['fuel'] * (1 + load_factor * 0.2),
                    'co2_kg': dist * self.aircraft_specs[ac_type]['co2'],
                    'op_cost_tl': self.aircraft_specs[ac_type]['op_cost'],
                    'delay_cost_per_min': 800 if destination in ['IST', 'LHR', 'JFK'] else 500,
                    'market_qsi_weight': random.uniform(0.8, 1.3) if is_night == 0 else random.uniform(0.5, 0.9), # Night flights have lower preference
                    'saf_usage': 0.0
                })
        
        df = pd.DataFrame(flights)
        df['departure_time'] = pd.to_datetime(df['departure_time'], utc=True)
        df['arrival_time'] = pd.to_datetime(df['arrival_time'], utc=True)
        # Standard initial state
        df['is_canceled'] = 0
        df['assigned_delay'] = 0
        df['saf_usage'] = 0.0
        return df.dropna()

    def trigger_disruption(self, df, hub='IST', delay_mins=120):
        """
        🚀 v16.0 Resilience: Injects massive delays at a hub to test recovery.
        """
        mask = (df['origin'] == hub) & (df['departure_time'].dt.hour < 12)
        df.loc[mask, 'assigned_delay'] = delay_mins
        df.loc[mask, 'causal_factor'] = 'Operational Failure'
        return df

        
        return pd.DataFrame(flights)
