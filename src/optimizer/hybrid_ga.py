import logging
import time
import random

import numpy as np
import pandas as pd

logger = logging.getLogger("AviationSingularity.QIO")


class QuantumInspiredGA:
    """
    Hybrid recovery layer for tactical rescheduling.

    Stage 2: Quantum-inspired population search proposes aircraft assignments.
    Stage 3: Repair/local-search logic converts proposals into a feasible
    operational plan by resolving aircraft conflicts and forced cancellations.
    """

    def __init__(self, flights_df, pop_size=30, generations=20):
        self.flights = flights_df.copy()
        self.flights["departure_time"] = pd.to_datetime(self.flights["departure_time"])
        self.flights["arrival_time"] = pd.to_datetime(self.flights["arrival_time"])
        if "is_canceled" not in self.flights.columns:
            self.flights["is_canceled"] = 0
        if "assigned_delay" not in self.flights.columns:
            self.flights["assigned_delay"] = 0
        if "assigned_aircraft" not in self.flights.columns:
            self.flights["assigned_aircraft"] = self.flights.get("aircraft_id", "None")

        self.pop_size = pop_size
        self.generations = generations
        self.ac_list = sorted(self.flights["aircraft_id"].dropna().unique().tolist())
        self.num_ac = len(self.ac_list)
        self.num_flights = len(self.flights)

        if self.num_ac == 0 or self.num_flights == 0:
            raise ValueError("QuantumInspiredGA requires at least one flight and one aircraft")

        self.q_pop = np.full((pop_size, self.num_flights, self.num_ac), np.pi / 4)
        self.best_individual = None
        self.best_fitness = -np.inf
        self.stats = []

    def _turnaround_minutes(self, ac_type):
        if ac_type == "Alice-E":
            return 90
        if ac_type == "ZeroAvia-H2":
            return 60
        return 45

    def _is_aircraft_eligible(self, flight_row, aircraft_id):
        ac_rows = self.flights[self.flights["aircraft_id"] == aircraft_id]
        if ac_rows.empty:
            return False

        ac_data = ac_rows.iloc[0]
        health = float(ac_data.get("engine_health", 1.0))
        if health < 0.2:
            return False

        maint_reason = ac_data.get("maintenance_reason")
        if maint_reason is not None and not pd.isna(maint_reason):
            if str(maint_reason).strip().lower() not in ("", "none", "nan"):
                return False

        pax_count = int(flight_row.get("passenger_count", 0))
        ac_capacity = int(ac_data.get("ac_capacity", pax_count or 9999))
        if pax_count > ac_capacity:
            return False

        return True

    def _time_feasible(self, previous_row, candidate_row):
        tat = self._turnaround_minutes(previous_row.get("ac_type", "standard"))
        return candidate_row["departure_time"] >= previous_row["arrival_time"] + pd.Timedelta(minutes=tat)

    def _collapse(self, q_ind):
        collapsed = self.flights.copy()
        probs = np.sin(q_ind) ** 2
        probs = probs / probs.sum(axis=1, keepdims=True)
        assignments = []
        for i in range(self.num_flights):
            ac_idx = np.random.choice(range(self.num_ac), p=probs[i])
            assignments.append(self.ac_list[ac_idx])
        collapsed["assigned_ac"] = assignments
        collapsed["assigned_aircraft"] = assignments
        return collapsed

    def _seed_q_population(self, seed_schedule=None):
        if seed_schedule is None or "assigned_aircraft" not in seed_schedule.columns:
            return

        seed_map = seed_schedule["assigned_aircraft"].to_dict()
        for flight_pos, flight_id in enumerate(self.flights.index):
            assigned = seed_map.get(flight_id)
            if assigned not in self.ac_list:
                continue
            ac_idx = self.ac_list.index(assigned)
            self.q_pop[0, flight_pos, :] = 0.05
            self.q_pop[0, flight_pos, ac_idx] = np.pi / 2 - 0.05

    def _repair_schedule(self, individual):
        repaired = individual.copy()
        repaired["assigned_delay"] = repaired.get("assigned_delay", 0)
        repaired["is_canceled"] = repaired.get("is_canceled", 0)
        repaired["assigned_aircraft"] = repaired.get("assigned_aircraft", repaired.get("assigned_ac", "None"))
        repaired["assigned_ac"] = repaired["assigned_aircraft"]

        schedules = {ac: [] for ac in self.ac_list}
        order = repaired.sort_values(["departure_time", "arrival_time"]).index.tolist()

        for flight_id in order:
            row = repaired.loc[flight_id]
            if int(row.get("is_canceled", 0)) == 1:
                repaired.at[flight_id, "assigned_aircraft"] = "None"
                repaired.at[flight_id, "assigned_ac"] = "None"
                continue
            preferred = row.get("assigned_aircraft", row.get("aircraft_id"))
            candidate_pool = []
            if preferred in self.ac_list:
                candidate_pool.append(preferred)
            candidate_pool.extend([ac for ac in self.ac_list if ac not in candidate_pool])

            chosen = None
            for aircraft_id in candidate_pool:
                if not self._is_aircraft_eligible(row, aircraft_id):
                    continue
                prior_jobs = schedules.get(aircraft_id, [])
                if prior_jobs and not self._time_feasible(prior_jobs[-1], row):
                    continue
                chosen = aircraft_id
                break

            if chosen is None:
                repaired.at[flight_id, "assigned_aircraft"] = "None"
                repaired.at[flight_id, "assigned_ac"] = "None"
                repaired.at[flight_id, "is_canceled"] = 1
                continue

            repaired.at[flight_id, "assigned_aircraft"] = chosen
            repaired.at[flight_id, "assigned_ac"] = chosen
            repaired.at[flight_id, "is_canceled"] = 0
            schedules[chosen].append(repaired.loc[flight_id])

        return repaired

    def _local_search(self, individual):
        improved = individual.copy()
        canceled = improved[improved["is_canceled"] == 1].sort_values(
            ["revenue_tl", "pax_connection_count"], ascending=False
        )
        if canceled.empty:
            return improved

        baseline = self.fitness(improved)
        for flight_id in canceled.index.tolist():
            trial = improved.copy()
            flight_row = trial.loc[flight_id]
            for aircraft_id in self.ac_list:
                trial.at[flight_id, "assigned_aircraft"] = aircraft_id
                trial.at[flight_id, "assigned_ac"] = aircraft_id
                trial.at[flight_id, "is_canceled"] = 0
                repaired = self._repair_schedule(trial)
                score = self.fitness(repaired)
                if score > baseline:
                    improved = repaired
                    baseline = score
                    break
        return improved

    def _update_qbits(self, q_ind, best_discrete):
        new_q = q_ind.copy()
        target_ac_indices = []
        for ac in best_discrete["assigned_ac"]:
            if ac in self.ac_list:
                target_ac_indices.append(self.ac_list.index(ac))
            else:
                target_ac_indices.append(None)

        delta = 0.05 * np.pi
        for i, target_idx in enumerate(target_ac_indices):
            if target_idx is None:
                continue
            for j in range(self.num_ac):
                if j == target_idx:
                    new_q[i, j] = min(np.pi / 2, new_q[i, j] + delta)
                else:
                    new_q[i, j] = max(0, new_q[i, j] - delta / max(self.num_ac - 1, 1))
        return new_q

    def fitness(self, individual, strategy="PROFIT"):
        repaired = self._repair_schedule(individual)
        active = repaired[repaired["is_canceled"] == 0]
        if active.empty:
            return -1e9

        revenue = float(active["revenue_tl"].sum())
        fuel_cost = float(active["fuel_cost_tl"].sum())
        op_cost = float(active["op_cost_tl"].sum())
        delay_cost = float((active["assigned_delay"] * active["delay_cost_per_min"]).sum())
        total_pax = float(active["passenger_count"].sum())
        total_dist = float(active["dist_km"].sum())
        rasm = revenue / (max(total_pax * total_dist, 1.0))

        cancellation_penalty = float(repaired["is_canceled"].sum()) * 250000.0
        swap_penalty = float(
            (
                (repaired["assigned_aircraft"] != "None")
                & (repaired["assigned_aircraft"] != repaired["aircraft_id"])
            ).sum()
        ) * 5000.0
        connectivity_bonus = float(active.get("pax_connection_count", pd.Series(dtype=float)).sum()) * 250.0

        if strategy == "PROFIT":
            return revenue - fuel_cost - op_cost - delay_cost - cancellation_penalty - swap_penalty + (rasm * 10000.0) + connectivity_bonus
        return (total_pax * 100.0) - delay_cost - cancellation_penalty * 0.25 + connectivity_bonus

    def solve(self, strategy="PROFIT", seed_schedule=None):
        start_time = time.time()
        self._seed_q_population(seed_schedule=seed_schedule)
        logger.info(
            f"QIO recovery engagement: population={self.pop_size} generations={self.generations} strategy={strategy}"
        )

        for gen in range(self.generations):
            discrete_pop = []
            fitness_pop = []
            for i in range(self.pop_size):
                discrete = self._collapse(self.q_pop[i])
                repaired = self._repair_schedule(discrete)
                improved = self._local_search(repaired)
                fit = self.fitness(improved, strategy)
                discrete_pop.append(improved)
                fitness_pop.append(fit)

                if fit > self.best_fitness:
                    self.best_fitness = fit
                    self.best_individual = improved.copy()

            for i in range(self.pop_size):
                self.q_pop[i] = self._update_qbits(self.q_pop[i], self.best_individual)

            self.stats.append(
                {"gen": gen, "best": float(self.best_fitness), "avg": float(np.mean(fitness_pop))}
            )

        solve_time = time.time() - start_time
        logger.info(f"QIO recovery converged in {solve_time:.2f}s | score={self.best_fitness:,.0f}")
        best = self.best_individual.copy()
        best.attrs["ga_stats"] = self.stats
        best.attrs["ga_runtime_sec"] = solve_time
        return best, solve_time
