import pandas as pd
import numpy as np
import random
import logging

# Professional Logging Configuration
logger = logging.getLogger(__name__)

class HybridGA:
    def __init__(self, flights_df, pop_size=30, generations=20):
        # Initialize required columns if missing
        df = flights_df.copy()
        if 'is_canceled' not in df.columns: df['is_canceled'] = 0
        if 'assigned_delay' not in df.columns: df['assigned_delay'] = 0
        if 'assigned_ac' not in df.columns: df['assigned_ac'] = df['aircraft_id']
        
        # HARDENING: Ensure time columns are datetime objects
        df['departure_time'] = pd.to_datetime(df['departure_time'])
        df['arrival_time'] = pd.to_datetime(df['arrival_time'])
        
        self.flights = df
        self.pop_size = pop_size
        self.generations = generations
        self.lambda_stability = 50 
        
    def fitness(self, individual):
        score = 0
        # Ensure 'individual' has the columns (should be true if initialized in __init__ or solve)
        assigned_flights = individual[individual['is_canceled'] == 0]
        canceled_flights = individual[individual['is_canceled'] == 1]
        
        # 1. Financial Objective
        score += float(assigned_flights['revenue_tl'].sum())
        score -= float((assigned_flights['op_cost_tl'] + assigned_flights['fuel_cost_tl']).sum())
        score -= float((canceled_flights['revenue_tl'] * 3).sum()) 
        score -= float((assigned_flights['assigned_delay'] * assigned_flights['delay_cost_per_min']).sum())
        
        # 2. Hard Constraints (Penalties)
        for _, row in assigned_flights.iterrows():
            if row['dist_km'] > row['ac_range_km']: score -= 1e6
            
        # 3. Stability Bonus
        for ac in assigned_flights['assigned_ac'].unique():
            ac_schedule = assigned_flights[assigned_flights['assigned_ac'] == ac].sort_values('departure_time')
            if len(ac_schedule) > 1:
                for i in range(len(ac_schedule) - 1):
                    t1_arr = ac_schedule.iloc[i]['arrival_time']
                    t2_dep = ac_schedule.iloc[i+1]['departure_time']
                    gap = (t2_dep - t1_arr).total_seconds() / 60
                    if gap >= 45: 
                        score += (gap // 15) * self.lambda_stability
                    else:
                        score -= 5e5 # Feasibility violation for aircraft flow
        
        return score

    def solve(self, initial_seed=None):
        print(f"--- Hybrid GA v3.2 (Robust Alignment) Basliyor ---")
        population = []
        if initial_seed is not None:
            # Seed must have necessary columns (dt_solver ensures this)
            population.append(initial_seed.copy())
            
        while len(population) < self.pop_size:
            population.append(self.flights.copy()) 
            
        for gen in range(self.generations):
            pop_fitness = [(ind, self.fitness(ind)) for ind in population]
            pop_fitness.sort(key=lambda x: x[1], reverse=True)
            
            new_pop = [pop_fitness[i][0] for i in range(2)] 
            
            while len(new_pop) < self.pop_size:
                p1, p2 = random.sample(population[:10], 2)
                child = p1.copy()
                ac_list = self.flights['aircraft_id'].unique()
                ac_to_swap = random.choice(ac_list)
                
                # Crossover logic
                child.loc[child['assigned_ac'] == ac_to_swap] = p2[p2['assigned_ac'] == ac_to_swap]
                
                if random.random() < 0.2: # Mutation
                    f_idx = random.choice(child.index)
                    child.at[f_idx, 'assigned_ac'] = random.choice(ac_list)
                
                new_pop.append(child)
                
            population = new_pop
            print(f"Nesil {gen}: En İyi Skor = {pop_fitness[0][1]:,.0f} TL")
            
        return pop_fitness[0][0]
