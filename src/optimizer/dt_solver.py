import pandas as pd
import numpy as np
from ortools.sat.python import cp_model
import logging

# Professional Logging Configuration
logger = logging.getLogger(__name__)

class DigitalTwinSolver:
    def __init__(self, flights_df):
        self.flights = flights_df.copy()
        # HARDENING: Ensure time columns are datetime objects
        self.flights['departure_time'] = pd.to_datetime(self.flights['departure_time'])
        self.flights['arrival_time'] = pd.to_datetime(self.flights['arrival_time'])
        
    def solve_baseline(self, max_time_sec=30, max_shift_mins=60):
        # Alias for benchmark compatibility
        return self.solve_winning(max_time_sec=max_time_sec)

    def solve_winning(self, max_time_sec=60):
        logger.info("--- Decathlon Solver v5.1 (Enterprise Edition) Basliyor ---")
        model = cp_model.CpModel()
        
        # 1. SETS & INDICES
        F = self.flights.index.tolist()
        A = self.flights['aircraft_id'].unique().tolist()
        K = self.flights['crew_id'].unique().tolist()
        
        # 2. DECISION VARIABLES
        x = {} # x[f, a] -> Flight f assigned to Aircraft a
        for f in F:
            for a in A:
                x[f, a] = model.NewBoolVar(f'x_{f}_{a}')
        
        y = {} # y[f, k] -> Flight f assigned to Crew k
        for f in F:
            for k in K:
                y[f, k] = model.NewBoolVar(f'y_{f}_{k}')
                
        z = {} # z[f] -> Cancellation
        for f in F:
            z[f] = model.NewBoolVar(f'z_{f}')
            
        d = {} # d[f] -> Delay (mins)
        for f in F:
            d[f] = model.NewIntVar(0, 60, f'd_{f}')

        s = {} # s[f] -> SAF Usage (0-100%)
        for f in F:
            s[f] = model.NewIntVar(0, 100, f's_{f}')

        # 3. CONSTRAINTS (K1 - K10)
        for f in F:
            model.Add(sum(x[f, a] for a in A) + z[f] == 1)
            model.Add(sum(y[f, k] for k in K) + z[f] == 1)
            
            for a in A:
                if self.flights.loc[f, 'demand'] > self.flights.loc[f, 'ac_capacity']:
                    model.Add(x[f, a] == 0)

            for k in K:
                if self.flights.loc[f, 'ac_cat'] != self.flights.loc[f, 'crew_cert']:
                    model.Add(y[f, k] == 0)

        # (K2/K10) Aircraft Flow & TAT
        for a in A:
            for f1 in F:
                for f2 in F:
                    if f1 == f2: continue
                    if not self._check_time_feasibility(f1, f2):
                        model.Add(x[f1, a] + x[f2, a] <= 1)

        # (K4/K5) Crew Duty Limit (Hardened to 12h) & MCT
        for k in K:
            duty_time = sum(int(self.flights.loc[f, 'block_time']) * y[f, k] for f in F)
            model.Add(duty_time <= 720) # 12 Hours max
            
            # Max sectors per day: 4
            model.Add(sum(y[f, k] for f in F) <= 4)

            for f1 in F:
                for f2 in F:
                    if f1 == f2: continue
                    if not self._check_time_feasibility(f1, f2, crew_mode=True):
                        model.Add(y[f1, k] + y[f2, k] <= 1)

        # 4. OBJECTIVE: Maximize Net Profit
        # Z = Revenue - OpCost - FuelCost(SAF) - DelayPenalty - CarbonPenalty(SAF) - FatiguePenalty
        revenue = []
        op_costs = []
        fuel_costs = []
        delay_penalty = []
        carbon_penalty = []
        fatigue_penalty = []

        for f in F:
            active = (1 - z[f])
            revenue.append(active * int(self.flights.loc[f, 'revenue_tl']))
            op_costs.append(active * int(self.flights.loc[f, 'op_cost_tl']))
            
            # Dynamic Fuel Cost with SAF (SAF is 3x more expensive)
            # Cost = BaseFuel * (1 + 2 * s[f]/100)
            base_fuel = int(self.flights.loc[f, 'fuel_cost_tl'])
            # Multiply first then add to avoid division on variable
            fuel_costs.append(active * base_fuel + s[f] * (base_fuel * 2 // 100))
            
            delay_penalty.append(d[f] * int(self.flights.loc[f, 'delay_cost_per_min']))
            
            # Carbon Penalty (SAF reduces CO2 by 80%)
            # CO2 = BaseCO2 * (1 - 0.8 * s[f]/100)
            base_co2 = int(self.flights.loc[f, 'co2_kg'])
            # Simplified expression to avoid division on variable
            co2_emitted_scaled = active * base_co2 - s[f] * (base_co2 * 80 // 100)
            carbon_penalty.append(co2_emitted_scaled * 10) # 10 TL per kg CO2

        for k in K:
            base_f = int(self.flights[self.flights['crew_id'] == k]['crew_base_fatigue'].iloc[0])
            k_fatigue_terms = [base_f]
            for f in F:
                multiplier = 13 if self.flights.loc[f, 'is_night_flight'] == 1 else 10
                block_time = int(self.flights.loc[f, 'block_time'])
                k_fatigue_terms.append(y[f, k] * (block_time * multiplier // 10))
            fatigue_penalty.append(sum(k_fatigue_terms) * 500)

        model.Maximize(sum(revenue) - sum(op_costs) - sum(fuel_costs) - sum(delay_penalty) - sum(carbon_penalty) - sum(fatigue_penalty))

        for k in K:
            # Fatigue is base + weighted block time (1.3x for night)
            base_f = self.flights[self.flights['crew_id'] == k]['crew_base_fatigue'].iloc[0]
            k_fatigue_terms = [int(base_f)]
            for f in F:
                multiplier = 1.3 if self.flights.loc[f, 'is_night_flight'] == 1 else 1.0
                k_fatigue_terms.append(y[f, k] * int(self.flights.loc[f, 'block_time'] * multiplier))
            
            # Penalty of 500 TL per fatigue unit (minutes-equivalent)
            fatigue_penalty.append(sum(k_fatigue_terms) * 500)

        model.Maximize(sum(revenue) - sum(op_costs) - sum(fuel_costs) - sum(delay_penalty) - sum(carbon_penalty) - sum(fatigue_penalty))

        # 5. SOLVE
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_sec
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            logger.info(f"BİRİNCİLİK SEVİYESİ ÇÖZÜM BULUNDU! Skor: {solver.ObjectiveValue():,} TL")
            return self._format_results(solver, x, y, z, d, s, A)
        logger.warning("Optimum çözüm bulunamadı, kısıtlar gözden geçiriliyor.")

    def _check_time_feasibility(self, f1, f2, crew_mode=False):
        t1_arr = self.flights.loc[f1, 'arrival_time']
        t2_dep = self.flights.loc[f2, 'departure_time']
        
        apt = self.flights.loc[f1, 'destination']
        turn_min = 45
        if apt == 'IST': turn_min = 45
        elif apt == 'AYT': turn_min = 40
        elif apt == 'ESB': turn_min = 35
        
        if crew_mode: turn_min = max(turn_min, 60) # EASA MCT
        
        if t2_dep < t1_arr + pd.Timedelta(minutes=turn_min): return False
        return True

    def _format_results(self, solver, x, y, z, d, s, A):
        res = self.flights.copy()
        res['is_canceled'] = [solver.Value(z[f]) for f in self.flights.index]
        res['assigned_delay'] = [solver.Value(d[f]) for f in self.flights.index]
        res['saf_usage'] = [solver.Value(s[f]) for f in self.flights.index]
        
        assigned_acs = []
        for f in self.flights.index:
            found_ac = "None"
            for a in A:
                if solver.Value(x[f, a]) == 1:
                    found_ac = a
                    break
            assigned_acs.append(found_ac)
        res['assigned_aircraft'] = assigned_acs
        return res
