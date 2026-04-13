import pandas as pd
import numpy as np
from ortools.sat.python import cp_model

class DecathlonSolver:
    def __init__(self, flights_df):
        self.flights = flights_df.copy()
        
    def solve_winning(self, max_time_sec=60):
        print("--- Decathlon Solver v4.1 (Standardized Alignment) Basliyor ---")
        model = cp_model.CpModel()
        
        # 1. SETS & INDICES
        F = self.flights.index.tolist()
        A = self.flights['ac_id'].unique().tolist()
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

        # (K4/K5) Crew Duty Limit (780 min) & MCT
        for k in K:
            duty_time = sum(int(self.flights.loc[f, 'block_time']) * y[f, k] for f in F)
            model.Add(duty_time <= 780)
            
            for f1 in F:
                for f2 in F:
                    if f1 == f2: continue
                    if not self._check_time_feasibility(f1, f2):
                        model.Add(y[f1, k] + y[f2, k] <= 1)

        # 4. OBJECTIVE FUNCTION
        lambda_stability = 50
        
        obj_revenue = sum(int(self.flights.loc[f, 'revenue_tl']) * (1 - z[f]) for f in F)
        obj_costs = sum((int(self.flights.loc[f, 'op_cost_tl']) + int(self.flights.loc[f, 'fuel_cost_tl'])) * (1 - z[f]) for f in F)
        obj_penalties = sum(z[f] * int(self.flights.loc[f, 'revenue_tl']) * 3 for f in F)
        obj_delays = sum(d[f] * int(self.flights.loc[f, 'delay_cost_per_min']) for f in F)
        
        self.model_maximize = obj_revenue - obj_costs - obj_penalties - obj_delays
        model.Maximize(self.model_maximize)

        # 5. SOLVE
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_sec
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"BİRİNCİLİK SEVİYESİ ÇÖZÜM BULUNDU! Skor: {solver.ObjectiveValue():,} TL")
            return self._format_results(solver, x, y, z, d, A)
        return None

    def _check_time_feasibility(self, f1, f2):
        t1_arr = self.flights.loc[f1, 'arrival_time']
        t2_dep = self.flights.loc[f2, 'departure_time']
        
        # Consistent with updated simulator col: 'destination'
        apt = self.flights.loc[f1, 'destination']
        turn_min = 45
        if apt == 'IST': turn_min = 45
        elif apt == 'AYT': turn_min = 40
        elif apt == 'ESB': turn_min = 35
        
        if t2_dep < t1_arr + pd.Timedelta(minutes=turn_min): return False
        return True

    def _format_results(self, solver, x, y, z, d, A):
        res = self.flights.copy()
        res['is_canceled'] = [solver.Value(z[f]) for f in self.flights.index]
        res['assigned_delay'] = [solver.Value(d[f]) for f in self.flights.index]
        
        assigned_acs = []
        for f in self.flights.index:
            found_ac = "None"
            for a in A:
                if solver.Value(x[f, a]) == 1:
                    found_ac = a
                    break
            assigned_acs.append(found_ac)
        res['assigned_ac'] = assigned_acs
        return res
