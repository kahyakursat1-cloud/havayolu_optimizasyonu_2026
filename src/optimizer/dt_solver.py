import pandas as pd
import numpy as np
from ortools.sat.python import cp_model
import logging
from src.analytics.fatigue_engine import fatigue_engine
from src.optimizer.hybrid_ga import QuantumInspiredGA

logger = logging.getLogger(__name__)


class SolverError(Exception):
    """Base class for solver errors surfaced to the API layer."""


class InfeasibleScheduleError(SolverError):
    """CP-SAT returned INFEASIBLE — the input schedule has no valid assignment."""


class SolverTimeoutError(SolverError):
    """CP-SAT exhausted its time budget before finding a feasible solution."""

class DigitalTwinSolver:
    def __init__(self, flights_df):
        self.flights = flights_df.copy()
        # HARDENING: Ensure time columns are datetime objects
        self.flights['departure_time'] = pd.to_datetime(self.flights['departure_time'])
        self.flights['arrival_time'] = pd.to_datetime(self.flights['arrival_time'])
        self.flights['departure_hour'] = self.flights['departure_time'].dt.floor('h')
        self.flights['arrival_hour'] = self.flights['arrival_time'].dt.floor('h')

    def _compute_eligible_aircraft(self, F, A):
        ac_schedules = {}
        for a in A:
            ac_df = self.flights[self.flights['aircraft_id'] == a].sort_values('departure_time')
            ac_schedules[a] = ac_df

        eligible = {}
        grounding_reasons = {}

        for f in F:
            dep = self.flights.loc[f, 'departure_time']
            origin = self.flights.loc[f, 'origin']
            eligible[f] = []

            for a in A:
                # v24.0 MRO Check: Industrial Reliability
                # Fetch engine health from the first flight this aircraft is assigned to in this batch
                ac_data = self.flights[self.flights['aircraft_id'] == a].iloc[0]
                health = ac_data.get('engine_health', 1.0)
                maint_reason = ac_data.get('maintenance_reason')
                pax_count = int(self.flights.loc[f].get('passenger_count', 0))
                ac_capacity = int(ac_data.get('ac_capacity', pax_count or 9999))

                if health < 0.2:
                    grounding_reasons[a] = f"Engine Health Critical ({health:.2f})"
                    continue
                if pax_count > ac_capacity:
                    continue
                # Treat Python None, pandas NaN, and string sentinels ("None", "", "nan") as "no maintenance"
                if maint_reason is not None and not pd.isna(maint_reason) \
                        and str(maint_reason).strip().lower() not in ('', 'none', 'nan'):
                    grounding_reasons[a] = f"Pending Maintenance: {maint_reason}"
                    continue

                sched = ac_schedules[a]
                prior = sched[sched['departure_time'] < dep]
                if prior.empty:
                    eligible[f].append(a)
                else:
                    prev = prior.iloc[-1]
                    if self._check_time_feasibility_v16(prev.name, f):
                        eligible[f].append(a)

            if not eligible[f]:
                # If no aircraft is eligible, it must be canceled
                pass
                
        # Report groundings to logger for operator visibility
        for ac, reason in grounding_reasons.items():
            logger.warning(f"⚠️ AIRCRAFT GROUNDED: {ac} | Reason: {reason}")
            
        return eligible, grounding_reasons

    def _compute_eligible_crews(self, F, K):
        eligible = {}

        for f in F:
            required_cert = str(self.flights.loc[f].get('ac_cat', '')).strip().lower()
            eligible[f] = []

            for k in K:
                crew_data = self.flights[self.flights['crew_id'] == k].iloc[0]
                crew_cert = str(crew_data.get('crew_cert', '')).strip().lower()

                if required_cert in ('', 'train') or crew_cert == required_cert:
                    eligible[f].append(k)

            if not eligible[f]:
                eligible[f] = list(K)

        return eligible

    def _estimate_airport_hour_capacity(self, airport_code):
        airport_defaults = {
            'IST': 18,
            'ESB': 7,
            'ADB': 7,
            'AYT': 9,
            'LHR': 6,
            'JFK': 5,
        }
        return airport_defaults.get(str(airport_code), 6)

    def _build_airport_capacity_buckets(self, F):
        departure_buckets = {}
        arrival_buckets = {}

        for f in F:
            dep_key = (self.flights.loc[f, 'origin'], self.flights.loc[f, 'departure_hour'])
            arr_key = (self.flights.loc[f, 'destination'], self.flights.loc[f, 'arrival_hour'])
            departure_buckets.setdefault(dep_key, []).append(f)
            arrival_buckets.setdefault(arr_key, []).append(f)

        return departure_buckets, arrival_buckets

    def _build_aircraft_gate_conflicts(self, F):
        conflicts = []
        for i, f1 in enumerate(F):
            for f2 in F[i + 1:]:
                same_airport = self.flights.loc[f1, 'destination'] == self.flights.loc[f2, 'origin']
                same_gate = self.flights.loc[f1].get('gate_id') == self.flights.loc[f2].get('gate_id')
                overlap = not self._check_time_feasibility_v16(f1, f2)
                if same_airport and same_gate and overlap:
                    conflicts.append((f1, f2))
        return conflicts

    def _build_slot_pressure_map(self):
        slot_pressure = {}
        grouped = self.flights.groupby(['origin', 'departure_hour']).size()
        for (airport, hour), count in grouped.items():
            slot_pressure[(airport, hour)] = {
                'scheduled': int(count),
                'capacity': self._estimate_airport_hour_capacity(airport),
            }
        return slot_pressure

    def _annotate_solution(self, res, eligible_aircraft, eligible_crews, slot_pressure_map):
        annotated = res.copy()
        if 'assigned_aircraft' not in annotated.columns and 'assigned_ac' in annotated.columns:
            annotated['assigned_aircraft'] = annotated['assigned_ac']
        if 'assigned_aircraft' not in annotated.columns:
            annotated['assigned_aircraft'] = "None"
        if 'is_canceled' not in annotated.columns:
            annotated['is_canceled'] = 0
        if 'assigned_delay' not in annotated.columns:
            annotated['assigned_delay'] = 0

        annotated['decision_reason'] = [
            self._derive_decision_reason(annotated.loc[f], eligible_aircraft, eligible_crews, slot_pressure_map)
            for f in annotated.index
        ]
        annotated['slot_pressure_flag'] = [
            slot_pressure_map.get((annotated.loc[f, 'origin'], annotated.loc[f, 'departure_hour']), {}).get('scheduled', 0)
            > slot_pressure_map.get((annotated.loc[f, 'origin'], annotated.loc[f, 'departure_hour']), {}).get('capacity', 999)
            for f in annotated.index
        ]
        return annotated

    def _hybrid_recovery(self, strategy: str, eligible_aircraft, eligible_crews, slot_pressure_map):
        ga = QuantumInspiredGA(self.flights, pop_size=12, generations=8)
        seed_schedule = self.flights.copy()
        seed_schedule['assigned_aircraft'] = seed_schedule.get('assigned_aircraft', seed_schedule['aircraft_id'])
        recovered, runtime_sec = ga.solve(strategy=strategy, seed_schedule=seed_schedule)
        recovered = self._annotate_solution(recovered, eligible_aircraft, eligible_crews, slot_pressure_map)
        recovered.attrs['hybrid_runtime_sec'] = runtime_sec
        recovered.attrs['hybrid_stats'] = list(recovered.attrs.get('ga_stats', []))
        recovered.attrs['recovery_mode'] = 'ga_local_search'
        return recovered

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
            eligible_aircraft, grounding_reasons = self._compute_eligible_aircraft(F, A)
        else:
            # Still run MRO check even for small batches
            eligible_aircraft, grounding_reasons = self._compute_eligible_aircraft(F, A)
        eligible_crews = self._compute_eligible_crews(F, K)

        model = cp_model.CpModel()
        departure_buckets, arrival_buckets = self._build_airport_capacity_buckets(F)
        gate_conflicts = self._build_aircraft_gate_conflicts(F)
        slot_pressure_map = self._build_slot_pressure_map()

        # Decision Variables
        x = {} # Flight f to AC a
        for f in F:
            for a in eligible_aircraft[f]:
                x[f, a] = model.NewBoolVar(f'x_{f}_{a}')

        y = {} # Flight f to Crew k
        for f in F:
            for k in eligible_crews[f]:
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
            model.Add(sum(y[f, k] for k in eligible_crews[f]) + z[f] == 1)

        # Airport throughput capacity. This approximates tactical slot and stand pressure
        # by limiting how many departures/arrivals can remain active in the same hour.
        for (airport, hour), flights in departure_buckets.items():
            capacity = self._estimate_airport_hour_capacity(airport)
            model.Add(sum(1 - z[f] for f in flights) <= capacity)

        for (airport, hour), flights in arrival_buckets.items():
            capacity = max(2, self._estimate_airport_hour_capacity(airport) - 1)
            model.Add(sum(1 - z[f] for f in flights) <= capacity)

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
                        if (f1, k) in y and (f2, k) in y:
                            model.Add(y[f1, k] + y[f2, k] <= 1)

        # Crew Continuity (Route Linkage)
        for k in K:
            for i, f1 in enumerate(F):
                for f2 in F[i+1:]:
                    if self.flights.loc[f1,'destination'] != self.flights.loc[f2,'origin']:
                         if (f1, k) in y and (f2, k) in y:
                             model.Add(y[f1, k] + y[f2, k] <= 1)

        # Gate conflicts: if two flights occupy the same stand in an overlapping
        # tactical window, at least one must be canceled or assigned away by the model.
        for f1, f2 in gate_conflicts:
            for a in A:
                if (f1, a) in x and (f2, a) in x:
                    model.Add(x[f1, a] + x[f2, a] <= 1)

        # Objective Function
        revenue = []
        op_costs = []
        fuel_costs = []
        delay_penalty = []
        carbon_penalty = []
        corsia_tax = [] 
        fatigue_penalties = [] # v23.0 Bio-Mathematical Penalty
        
        for f in F:
            active = (1 - z[f])
            
            # v23.0 Fatigue Analysis
            f_time = self.flights.loc[f, 'departure_time']
            f_block = int(self.flights.loc[f, 'block_time'])
            f_risk = fatigue_engine.calculate_duty_fatigue(f_time, f_block)
            # Soft Penalty: Each 0.1 fatigue index = 5000 TL penalty
            # This allows the solver to fly high-fatigue legs if profit is extreme (e.g. trans-Atlantic)
            fatigue_penalties.append(active * int(f_risk * 50000))

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
            # Reward schedules that protect high-connection flights, so when
            # two flights compete for the same slot the one with more
            # downstream connecting passengers wins (misconnects are expensive).
            connection_bonus = sum(
                int(self.flights.loc[f, 'pax_connection_count']) * 10 * (1 - z[f])
                for f in F
            )
            model.Maximize(
                sum(revenue) - sum(op_costs) - sum(fuel_costs)
                - sum(delay_penalty) - sum(carbon_penalty) - sum(corsia_tax)
                - sum(fatigue_penalties)
                + connection_bonus
            )
        else: # VOLUME Strategy
            # Prioritize Load Factor and Connectivity over margin
            pax_count = [active * int(self.flights.loc[f, 'passenger_count']) for f in F]
            model.Maximize(sum(pax_count) * 1000 - sum(delay_penalty) * 2)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_sec
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            results = self._format_results(
                solver, x, y, z, d, s, t, eligible_aircraft, eligible_crews, slot_pressure_map
            )
            results.attrs['mro_warnings'] = grounding_reasons
            return results

        status_name = solver.StatusName(status) if hasattr(solver, 'StatusName') else str(status)
        if status == cp_model.INFEASIBLE:
            raise InfeasibleScheduleError(
                f"No feasible assignment (strategy={strategy}, flights={len(F)}, grounded={len(grounding_reasons)})"
            )
        if status == cp_model.MODEL_INVALID:
            raise SolverError(f"CP-SAT model invalid: {solver.ResponseProto().solve_log[:500]}")
        # UNKNOWN status = timeout without feasible solution
        raise SolverTimeoutError(
            f"Solver timed out after {max_time_sec}s without a feasible solution (status={status_name})"
        )

    def solve_with_windows(self, strategy: str = "PROFIT", window_size_hrs=4):
        sorted_flights = self.flights.sort_values('departure_time').copy()
        start_time = sorted_flights['departure_time'].min()
        end_time = sorted_flights['departure_time'].max()

        full_results = []
        failures = []
        hybrid_recoveries = []
        current_start = start_time
        while current_start <= end_time:
            current_end = current_start + pd.Timedelta(hours=window_size_hrs)
            window_df = sorted_flights[(sorted_flights['departure_time'] >= current_start) &
                                       (sorted_flights['departure_time'] < current_end)].copy()
            if not window_df.empty:
                window_solver = DigitalTwinSolver(window_df)
                try:
                    res = window_solver.solve_winning(strategy=strategy, max_time_sec=5)
                    full_results.append(res)
                except SolverError as e:
                    logger.warning(f"Window [{current_start}..{current_end}] solve failed: {e}")
                    try:
                        F = window_solver.flights.index.tolist()
                        A = window_solver.flights['aircraft_id'].unique().tolist()
                        K = window_solver.flights['crew_id'].unique().tolist()
                        eligible_aircraft, _grounding = window_solver._compute_eligible_aircraft(F, A)
                        eligible_crews = window_solver._compute_eligible_crews(F, K)
                        slot_pressure_map = window_solver._build_slot_pressure_map()
                        recovered = window_solver._hybrid_recovery(
                            strategy=strategy,
                            eligible_aircraft=eligible_aircraft,
                            eligible_crews=eligible_crews,
                            slot_pressure_map=slot_pressure_map,
                        )
                        hybrid_recoveries.append({
                            "window_start": str(current_start),
                            "mode": recovered.attrs.get("recovery_mode", "ga_local_search"),
                            "runtime_sec": round(float(recovered.attrs.get("hybrid_runtime_sec", 0.0)), 3),
                        })
                        full_results.append(recovered)
                    except Exception as recovery_error:
                        failures.append({
                            "window_start": str(current_start),
                            "error": str(e),
                            "recovery_error": str(recovery_error),
                        })
                        full_results.append(window_df)
            current_start = current_end

        if not full_results:
            raise InfeasibleScheduleError("No time windows contained any flights")

        res_df = pd.concat(full_results)
        res_df = res_df[~res_df.index.duplicated(keep='last')]
        res_df.attrs['window_failures'] = failures
        res_df.attrs['hybrid_recoveries'] = hybrid_recoveries
        return res_df

    def _calculate_ist_gate_distance(self, g1, g2):
        """
        v25.0 Real IST Pier Map (Approximate distance in minutes from Hub)
        """
        ist_piers = {'A': 15, 'B': 12, 'D': 10, 'F': 22, 'G': 8}
        
        try:
            p1, p2 = str(g1)[0], str(g2)[0]
            if p1 == p2: return 5 # Same pier
            # Distances are from Hub. To go A -> B, you go A -> Hub -> B.
            return ist_piers.get(p1, 15) + ist_piers.get(p2, 15)
        except Exception:
            return 30 # Safe default

    def _check_time_feasibility_v16(self, f1, f2, crew_mode=False):
        """
        v25.0 Terminal-Gate Aware Dynamic MCT.
        Fulfills the 'Personalized and Dynamic MCT' requirement.
        """
        t1_arr = self.flights.loc[f1, 'arrival_time']
        t2_dep = self.flights.loc[f2, 'departure_time']

        # Column 'ac_type' is the canonical name from synthetic_env; fall back to 'standard'
        row1 = self.flights.loc[f1]
        ac_type = row1.get('ac_type', row1.get('aircraft_type', 'standard'))
        origin = self.flights.loc[f2, 'origin']

        # v25.0 Dynamic Gate-to-Gate Distance (optional columns — default to fixed TAT)
        g1 = row1.get('gate_id', None)
        g2_row = self.flights.loc[f2]
        g2 = g2_row.get('gate_id', None)
        mobility = float(row1.get('pax_mobility_index', 1.0))

        walking_time = 0
        if origin == "IST" and g1 is not None and g2 is not None:
            walking_time = self._calculate_ist_gate_distance(g1, g2)
            walking_time = walking_time / max(mobility, 0.1)  # guard against division by 0

        # Mandatory Charging/Refueling Windows
        if ac_type == "Alice-E":
            tat = 90
        elif ac_type == "ZeroAvia-H2":
            tat = 60
        else:
            # Baseline Turnaround + Dynamic Walking Buffer
            tat = (45 if not crew_mode else 60) + walking_time

        if t2_dep < t1_arr + pd.Timedelta(minutes=tat): return False
        return True

    def _derive_decision_reason(self, row, eligible_aircraft, eligible_crews, slot_pressure_map):
        if row['is_canceled'] == 1:
            if not eligible_aircraft.get(row.name):
                return "Cancellation: no eligible aircraft after maintenance/capacity screening"
            if not eligible_crews.get(row.name):
                return "Cancellation: no eligible crew available for aircraft category"
            dep_key = (row['origin'], row['departure_hour'])
            slot_data = slot_pressure_map.get(dep_key)
            if slot_data and slot_data['scheduled'] > slot_data['capacity']:
                return "Cancellation: tactical airport slot pressure exceeded hourly capacity"
            return "Cancellation: network feasibility conflict under current tactical constraints"

        reasons = []
        if row['assigned_delay'] > 0:
            reasons.append("delay absorbed to protect wider network stability")
        if row['assigned_aircraft'] != "None" and row['assigned_aircraft'] != row.get('aircraft_id'):
            reasons.append("aircraft swap applied for feasibility")
        dep_key = (row['origin'], row['departure_hour'])
        slot_data = slot_pressure_map.get(dep_key)
        if slot_data and slot_data['scheduled'] > slot_data['capacity']:
            reasons.append("protected under high slot pressure due to value/connectivity")
        if float(row.get('pax_connection_count', 0)) >= 30:
            reasons.append("high connecting passenger count prioritized")
        if not reasons:
            reasons.append("baseline feasible plan retained")
        return "; ".join(reasons)

    def _format_results(self, solver, x, y, z, d, s, t, eligible_aircraft, eligible_crews, slot_pressure_map):
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
        return self._annotate_solution(res, eligible_aircraft, eligible_crews, slot_pressure_map)
