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

    def solve_winning(self, max_time_sec=60, contrail_penalty_weight=500):
        logger.info(f"--- Scientific DigitalTwin Solver v8.0 Basliyor (Contrail Weight: {contrail_penalty_weight}) ---")
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

        # 3. CONSTRAINTS
        for f in F:
            model.Add(sum(x[f, a] for a in A) + z[f] == 1)
            model.Add(sum(y[f, k] for k in K) + z[f] == 1)
            
            for a in A:
                if self.flights.loc[f, 'passenger_count'] > self.flights.loc[f, 'ac_capacity']:
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

        # (K4/K5) Hierarchical Crew Duty (Scientific v8)
        for k in K:
            # 2026 Standards: 45m briefing + 45m debriefing = 90m per duty
            is_crew_active = model.NewBoolVar(f'is_active_{k}')
            model.AddMaxEquality(is_crew_active, [y[f, k] for f in F])
            
            flight_time = sum(int(self.flights.loc[f, 'block_time']) * y[f, k] for f in F)
            # Duty = FlightTime + 90m (if active)
            model.Add(flight_time + (is_crew_active * 90) <= 720) 
            
            # Max sectors per day: 4
            model.Add(sum(y[f, k] for f in F) <= 4)

            for f1 in F:
                for f2 in F:
                    if f1 == f2: continue
                    if not self._check_time_feasibility(f1, f2, crew_mode=True):
                        model.Add(y[f1, k] + y[f2, k] <= 1)

        # --- MAINTENANCE (Standard v7 preserved) ---
        for a in A:
            total_block_time = []
            for f in F:
                total_block_time.append(x[f, a] * int(self.flights.loc[f, 'block_time']))
            rem_fh_total = self.flights[self.flights['aircraft_id'] == a]['ac_remaining_fh'].iloc[0] * 60
            model.Add(sum(total_block_time) <= int(rem_fh_total))

        # 4. OBJECTIVE: Maximize Net Profit
        revenue = []
        op_costs = []
        fuel_costs = []
        delay_penalty = []
        carbon_penalty = []
        fatigue_penalty = []
        contrail_penalty = []
        missed_connection_penalty = []

        for f in F:
            active = (1 - z[f])
            revenue.append(active * int(self.flights.loc[f, 'revenue_tl']))
            op_costs.append(active * int(self.flights.loc[f, 'op_cost_tl']))
            
            base_fuel = int(self.flights.loc[f, 'fuel_cost_tl'])
            fuel_costs.append(active * base_fuel + s[f] * (base_fuel * 2 // 100))
            
            delay_penalty.append(d[f] * int(self.flights.loc[f, 'delay_cost_per_min']))
            
            # v9 Resilience: Missed Connection Penalty
            # If delay > 30m, connection risk increases linearly
            pax_conn = int(self.flights.loc[f, 'pax_connection_count'])
            # Simulation: 2000 TL per missed connection
            # We use a linear approximation for MILP: (d[f] - 30) * pax_conn * 50 if d > 30
            # For simplicity, we use d[f] * pax_conn * 20 (approximate weight)
            missed_connection_penalty.append(d[f] * pax_conn * 20)

            base_co2 = int(self.flights.loc[f, 'co2_kg'])
            co2_emitted_scaled = active * base_co2 - s[f] * (base_co2 * 80 // 100)
            carbon_penalty.append(co2_emitted_scaled * 10) 
            
            # v8 Scientific: Contrail Penalty
            c_risk = int(self.flights.loc[f, 'contrail_risk'] * 100)
            contrail_penalty.append(active * (c_risk * contrail_penalty_weight // 100))

        for k in K:
            base_f = int(self.flights[self.flights['crew_id'] == k]['crew_base_fatigue'].iloc[0])
            k_fatigue_terms = [base_f]
            for f in F:
                multiplier = 13 if self.flights.loc[f, 'is_night_flight'] == 1 else 10
                block_time = int(self.flights.loc[f, 'block_time'])
                k_fatigue_terms.append(y[f, k] * (block_time * multiplier // 10))
            fatigue_penalty.append(sum(k_fatigue_terms) * 500)

        model.Maximize(sum(revenue) - sum(op_costs) - sum(fuel_costs) - sum(delay_penalty) - sum(carbon_penalty) - sum(fatigue_penalty) - sum(contrail_penalty) - sum(missed_connection_penalty))

        # 5. SOLVE
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_sec
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            logger.info(f"BİRİNCİLİK SEVİYESİ ÇÖZÜM BULUNDU! Skor: {solver.ObjectiveValue():,} TL")
            return self._format_results(solver, x, y, z, d, s, A)
        logger.warning("Optimum çözüm bulunamadı, kısıtlar gözden geçiriliyor.")

    def solve_with_windows(self, window_size_hrs=6, max_time_per_window=10):
        """
        🚀 v12.0 Sliding Window Optimization: Solves flights in overlapping chunks.
        """
        logger.info(f"--- v12.0 Sliding Window Solver (Size: {window_size_hrs}h) ---")
        full_results = []
        
        # Sort flights by time
        sorted_flights = self.flights.sort_values('departure_time')
        start_time = sorted_flights['departure_time'].min()
        end_time = sorted_flights['departure_time'].max()
        
        current_start = start_time
        while current_start < end_time:
            current_end = current_start + pd.Timedelta(hours=window_size_hrs)
            
            # Select flights in window
            window_df = sorted_flights[(sorted_flights['departure_time'] >= current_start) & 
                                       (sorted_flights['departure_time'] < current_end)]
            
            if not window_df.empty:
                window_solver = DigitalTwinSolver(window_df)
                result = window_solver.solve_winning(max_time_sec=max_time_per_window)
                if result is not None:
                    full_results.append(result)
            
            # Advance window (no overlap for simplicity in v12.0 baseline, can be added)
            current_start = current_end
            
        return pd.concat(full_results).drop_duplicates('flight_id') if full_results else None

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
