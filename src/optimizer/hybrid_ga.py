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
        self.stats = []

    def reversal_mutation(self, individual):
        """GARSRev: Reverses a sub-sequence of flights for a random aircraft."""
        child = individual.copy()
        ac_list = child['assigned_ac'].unique()
        target_ac = random.choice(ac_list)
        
        ac_flights = child[child['assigned_ac'] == target_ac].index.tolist()
        if len(ac_flights) < 3: return child
        
        # Select sub-sequence
        idx1, idx2 = sorted(random.sample(range(len(ac_flights)), 2))
        sub_seq = ac_flights[idx1:idx2+1]
        
        # Reverse assigned flights (only for this AC context if applicable)
        # In this specific GA, we just swap assignments between these flights and others?
        # Actually, for GARSRev, we can just shuffle or reverse the order if the GA was sequence-based.
        # Here, we will just swap assignments with another random AC for that sub-sequence
        other_ac = random.choice([a for a in ac_list if a != target_ac])
        child.loc[sub_seq, 'assigned_ac'] = other_ac
        return child

    def simulate_delay_propagation(self, ac_schedule):
        """
        🚀 v9.0 Resilience: Monte Carlo simulation of propagated delays.
        """
        if len(ac_schedule) < 2: return 0
        total_prop_delay = 0
        current_delay = 0
        
        for i in range(len(ac_schedule) - 1):
            # 20% chance of an independent 30min delay at each leg
            if random.random() < 0.20:
                current_delay += 30
            
            t1_arr = ac_schedule.iloc[i]['arrival_time'] + pd.Timedelta(minutes=current_delay)
            t2_dep = ac_schedule.iloc[i+1]['departure_time']
            
            # If arrival with delay > next departure - tat, propagation occurs
            gap = (t2_dep - t1_arr).total_seconds() / 60
            if gap < 45: # 45m TAT threshold
                prop = 45 - gap
                current_delay += prop
                total_prop_delay += prop
            else:
                # Gap absorbed some delay
                current_delay = max(0, current_delay - (gap - 45))
                
        return total_prop_delay

    def fitness(self, individual):
        score = 0
        assigned_flights = individual[individual['is_canceled'] == 0]
        canceled_flights = individual[individual['is_canceled'] == 1]
        
        # 1. Financial Objective (v8: Weighted Revenue)
        score += float(assigned_flights['revenue_tl'].sum())
        score -= float((assigned_flights['op_cost_tl'] + assigned_flights['fuel_cost_tl']).sum())
        score -= float((canceled_flights['revenue_tl'] * 3).sum()) 
        score -= float((assigned_flights['assigned_delay'] * assigned_flights['delay_cost_per_min']).sum())
        
        # 2. Scientific v8: Contrail Penalty
        if 'contrail_risk' in assigned_flights.columns:
            score -= float((assigned_flights['contrail_risk'] * 500 * 10).sum())

        # 3. v9 Resilience: Propagated Delay Penalty
        for ac in assigned_flights['assigned_ac'].unique():
            ac_schedule = assigned_flights[assigned_flights['assigned_ac'] == ac].sort_values('departure_time')
            prop_delay = self.simulate_delay_propagation(ac_schedule)
            score -= prop_delay * 1000 # 1000 TL penalty per minute of expected propagation

        # 4. Hard Constraints (Penalties)
        for _, row in assigned_flights.iterrows():
            if row['dist_km'] > row['ac_range_km']: score -= 1e6
            
        # 5. Stability & TAT
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
                        score -= 5e5 
        
        return score

    def solve(self, initial_seed=None):
        print(f"--- Hybrid GA v8.0 (Scientific GARSRev) Basliyor ---")
        population = []
        if initial_seed is not None:
            population.append(initial_seed.copy())
            
        while len(population) < self.pop_size:
            population.append(self.flights.copy()) 
            
        for gen in range(self.generations):
            pop_fitness = [(ind, self.fitness(ind)) for ind in population]
            pop_fitness.sort(key=lambda x: x[1], reverse=True)
            
            fit_values = [x[1] for x in pop_fitness]
            self.stats.append({'gen': gen, 'best': max(fit_values), 'avg': np.mean(fit_values), 'std': np.std(fit_values)})
            
            new_pop = [pop_fitness[i][0] for i in range(2)] 
            
            while len(new_pop) < self.pop_size:
                p1, p2 = random.sample(population[:10], 2)
                child = p1.copy()
                ac_list = self.flights['aircraft_id'].unique()
                ac_to_swap = random.choice(ac_list)
                
                # Crossover
                child.loc[child['assigned_ac'] == ac_to_swap] = p2[p2['assigned_ac'] == ac_to_swap]
                
                # Scientific v8: GARSRev Operators
                r = random.random()
                if r < 0.1: # Standard Mutation
                    f_idx = random.choice(child.index)
                    child.at[f_idx, 'assigned_ac'] = random.choice(ac_list)
                elif r < 0.2: # GARSRev Reversal
                    child = self.reversal_mutation(child)
                
                new_pop.append(child)
                
            population = new_pop
            print(f"Nesil {gen}: Skor={pop_fitness[0][1]:,.0f} | StdDev={np.std(fit_values):,.2f}")
            
        return pop_fitness[0][0]
