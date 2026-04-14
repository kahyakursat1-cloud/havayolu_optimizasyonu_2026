import pandas as pd
import numpy as np
from ortools.sat.python import cp_model
import logging
import time

# Professional Logging Configuration
logger = logging.getLogger(__name__)

class DigitalTwinSolver:
    def __init__(self, flights_df):
        self.flights = flights_df.copy()
        # HARDENING: Ensure time columns are datetime objects
        self.flights['departure_time'] = pd.to_datetime(self.flights['departure_time'])
        self.flights['arrival_time'] = pd.to_datetime(self.flights['arrival_time'])

    def _compute_eligible_aircraft(self, F, A):
        ac_schedules = {}
        for a in A:
            ac_df = self.flights[self.flights['aircraft_id'] == a].sort_values('departure_time')
            ac_schedules[a] = ac_df

        eligible = {}
        for f in F:
            dep = self.flights.loc[f, 'departure_time']
            origin = self.flights.loc[f, 'origin']
            eligible[f] = []

            for a in A:
                sched = ac_schedules[a]
                prior = sched[sched['departure_time'] < dep]
                if prior.empty:
                    eligible[f].append(a)
                else:
                    prev = prior.iloc[-1]
                    if self._check_time_feasibility_v16(prev.name, f):
                        eligible[f].append(a)

            if not eligible[f]:
                eligible[f] = list(A)
        return eligible

    def solve_winning(self, strategy: str = "PROFIT", max_time_sec=60):
        """
        Solve the airline assignment problem using CP-SAT.
        v22.0: Supports Strategy-based objective toggles.
        """
        logger.info(f"--- v22.0 CP-SAT SOLVER Engagement | Strategy: {strategy} ---")

        F = self.flights.index.tolist()
        A = self.flights['aircraft_id'].unique().tolist()
        K = self.flights['crew_id'].unique().tolist()

        if len(self.flights) > 150:
            eligible_aircraft = self._compute_eligible_aircraft(F, A)
        else:
            eligible_aircraft = {f: list(A) for f in F}

        model = cp_model.CpModel()

        # Decision Variables
        x = {} # Flight f to AC a
        for f in F:
            for a in eligible_aircraft[f]:
                x[f, a] = model.NewBoolVar(f'x_{f}_{a}')

        y = {} # Flight f to Crew k
        for f in F:
            for k in K:
                y[f, k] = model.NewBoolVar(f'y_{f}_{k}')
                
        z = {} # Cancellation
        for f in F:
            z[f] = model.NewBoolVar(f'z_{f}')
            
        d = {} # Delay (mins)
        for f in F:
            d[f] = model.NewIntVar(0, 60, f'd_{f}')

        s = {} # SAF Usage (0-100%)
        for f in F:
            s[f] = model.NewIntVar(0, 100, f's_{f}')

        t = {} # Fuel Tankering (kg)
        for f in F:
            t[f] = model.NewIntVar(0, 5000, f'tanker_{f}')

        # Constraints
        for f in F:
            model.Add(sum(x[f, a] for a in eligible_aircraft[f]) + z[f] == 1)
            model.Add(sum(y[f, k] for k in K) + z[f] == 1)

        # Maintenance & Turnaround Conflicts
        for i, f1 in enumerate(F):
            for f2 in F[i+1:]:
                # Check for AC conflicts
                if not self._check_time_feasibility_v16(f1, f2):
                    for a in A:
                        if (f1, a) in x and (f2, a) in x:
                            model.Add(x[f1, a] + x[f2, a] <= 1)
                
                # Check for Crew conflicts
                if not self._check_time_feasibility_v16(f1, f2, crew_mode=True):
                    for k in K:
                        model.Add(y[f1, k] + y[f2, k] <= 1)

        # Crew Continuity (Route Linkage)
        for k in K:
            for i, f1 in enumerate(F):
                for f2 in F[i+1:]:
                    if self.flights.loc[f1,'destination'] != self.flights.loc[f2,'origin']:
                         model.Add(y[f1, k] + y[f2, k] <= 1)

        # Objective Function
        revenue = []
        op_costs = []
        fuel_costs = []
        delay_penalty = []
        carbon_penalty = []
        corsia_tax = [] 

        for f in F:
            active = (1 - z[f])
            revenue.append(active * int(self.flights.loc[f, 'revenue_tl']))
            op_costs.append(active * int(self.flights.loc[f, 'op_cost_tl']))
            
            base_fuel = int(self.flights.loc[f, 'fuel_cost_tl'])
            fuel_costs.append(active * base_fuel + s[f] * (base_fuel * 3 // 100))
            delay_penalty.append(d[f] * int(self.flights.loc[f, 'delay_cost_per_min']))
            
            qsi_weight = float(self.flights.loc[f, 'market_qsi_weight'])
            
            base_co2 = int(self.flights.loc[f, 'co2_kg'])
            co2_emitted = active * base_co2 - s[f] * (base_co2 * 8 // 10)
            carbon_penalty.append(co2_emitted * 20)
            
            allowance = 1500 
            overage = model.NewIntVar(0, 10000, f'over_{f}')
            model.AddMaxEquality(overage, [0, co2_emitted - allowance])
            corsia_tax.append(overage * 5)
            
        if strategy == "PROFIT":
            model.Maximize(
                sum(revenue) - sum(op_costs) - sum(fuel_costs) 
                - sum(delay_penalty) - sum(carbon_penalty) - sum(corsia_tax)
            )
        else: # VOLUME Strategy
            # Prioritize Load Factor and Connectivity over margin
            pax_count = [active * int(self.flights.loc[f, 'passenger_count']) for f in F]
            model.Maximize(sum(pax_count) * 1000 - sum(delay_penalty) * 2)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_sec
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return self._format_results(solver, x, y, z, d, s, t, eligible_aircraft)
        return None

    def solve_with_windows(self, strategy: str = "PROFIT", window_size_hrs=4):
        sorted_flights = self.flights.sort_values('departure_time').copy()
        start_time = sorted_flights['departure_time'].min()
        end_time = sorted_flights['departure_time'].max()
        
        full_results = []
        current_start = start_time
        while current_start <= end_time:
            current_end = current_start + pd.Timedelta(hours=window_size_hrs)
            window_df = sorted_flights[(sorted_flights['departure_time'] >= current_start) & 
                                       (sorted_flights['departure_time'] < current_end)].copy()
            if not window_df.empty:
                window_solver = DigitalTwinSolver(window_df)
                res = window_solver.solve_winning(strategy=strategy, max_time_sec=5)
                if res is not None: full_results.append(res)
                else: full_results.append(window_df)
            current_start = current_end
            
        return pd.concat(full_results).drop_duplicates('flight_id', keep='last')

    def _check_time_feasibility_v16(self, f1, f2, crew_mode=False):
        """
        v22.0 Propulsion-aware Turnaround.
        Checks if f2 can be flown after f1 by the same aircraft or crew.
        """
        t1_arr = self.flights.loc[f1, 'arrival_time']
        t2_dep = self.flights.loc[f2, 'departure_time']
        
        ac_type = self.flights.loc[f1, 'aircraft_type']
        
        # Mandatory Charging/Refueling Windows
        if ac_type == "Alice-E":
            tat = 90
        elif ac_type == "ZeroAvia-H2":
            tat = 60
        else:
            tat = 45 if not crew_mode else 60
            
        if t2_dep < t1_arr + pd.Timedelta(minutes=tat): return False
        return True

    def _format_results(self, solver, x, y, z, d, s, t, eligible_aircraft):
        res = self.flights.copy()
        res['is_canceled'] = [solver.Value(z[f]) for f in self.flights.index]
        res['assigned_delay'] = [solver.Value(d[f]) for f in self.flights.index]
        res['decision_logic'] = ["AI Optimized" for _ in self.flights.index]
        
        assigned_acs = []
        for f in self.flights.index:
            found_ac = "None"
            for a in eligible_aircraft.get(f, []):
                if (f, a) in x and solver.Value(x[f, a]) == 1:
                    found_ac = a
                    break
            assigned_acs.append(found_ac)
        res['assigned_aircraft'] = assigned_acs
        return res
