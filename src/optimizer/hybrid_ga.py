import pandas as pd
import numpy as np
import random
import logging

logger = logging.getLogger(__name__)


class HybridGA:
    def __init__(self, flights_df, pop_size=30, generations=20):
        df = flights_df.copy()
        if 'is_canceled' not in df.columns:
            df['is_canceled'] = 0
        if 'assigned_delay' not in df.columns:
            df['assigned_delay'] = 0
        if 'assigned_ac' not in df.columns:
            df['assigned_ac'] = df['aircraft_id']

        df['departure_time'] = pd.to_datetime(df['departure_time'])
        df['arrival_time'] = pd.to_datetime(df['arrival_time'])

        self.flights = df
        self.pop_size = pop_size
        self.generations = generations
        self.lambda_stability = 50
        self.stats = []
        self._ac_list = df['aircraft_id'].unique().tolist()

    # ------------------------------------------------------------------
    # MUTATION OPERATORS
    # ------------------------------------------------------------------

    def quantum_tunneling_mutation(self, individual):
        """
        Quantum-Inspired mutation: reassigns 10% of flights to random aircraft,
        deliberately ignoring local constraints to escape deep local optima.
        """
        child = individual.copy()
        tunnel_indices = random.sample(child.index.tolist(), max(1, len(child) // 10))
        for idx in tunnel_indices:
            child.at[idx, 'assigned_ac'] = random.choice(self._ac_list)
        return child

    def reversal_mutation(self, individual):
        """
        GARSRev: Reassigns a consecutive sub-sequence of one aircraft's
        rotation to another aircraft, preserving the departure-time ordering.
        """
        child = individual.copy()
        ac_candidates = child['assigned_ac'].unique().tolist()
        if len(ac_candidates) < 2:
            return child

        target_ac = random.choice(ac_candidates)
        ac_flights = child[child['assigned_ac'] == target_ac].index.tolist()
        if len(ac_flights) < 3:
            return child

        idx1, idx2 = sorted(random.sample(range(len(ac_flights)), 2))
        sub_seq = ac_flights[idx1:idx2 + 1]

        other_ac = random.choice([a for a in ac_candidates if a != target_ac])
        child.loc[sub_seq, 'assigned_ac'] = other_ac
        return child

    def point_mutation(self, individual):
        """Standard single-gene mutation: reassign one random flight."""
        child = individual.copy()
        f_idx = random.choice(child.index.tolist())
        child.at[f_idx, 'assigned_ac'] = random.choice(self._ac_list)
        return child

    # ------------------------------------------------------------------
    # CROSSOVER
    # ------------------------------------------------------------------

    def aircraft_rotation_crossover(self, parent1, parent2):
        """
        Aircraft-Rotation Crossover: for a randomly chosen aircraft, the child
        inherits from parent1 for all flights *except* those that parent2
        assigns to that aircraft — those slots are taken from parent2's rotation.

        This preserves aircraft-rotation feasibility better than random point
        crossover because it operates at the 'rotation unit' granularity.
        """
        child = parent1.copy()
        ac_to_swap = random.choice(self._ac_list)
        # Indices that parent2 assigns to ac_to_swap
        p2_rotation_idx = parent2[parent2['assigned_ac'] == ac_to_swap].index
        # Give those same flights the same aircraft in the child
        valid_idx = p2_rotation_idx[p2_rotation_idx.isin(child.index)]
        child.loc[valid_idx, 'assigned_ac'] = ac_to_swap
        return child

    # ------------------------------------------------------------------
    # SELECTION
    # ------------------------------------------------------------------

    def _tournament_select(self, pop_fitness, k=4):
        """
        Tournament selection with tournament size k.
        More selective than random top-N sampling; tunable via k.
        """
        candidates = random.sample(pop_fitness, min(k, len(pop_fitness)))
        return max(candidates, key=lambda x: x[1])[0]

    # ------------------------------------------------------------------
    # SIMULATION
    # ------------------------------------------------------------------

    def simulate_delay_propagation(self, ac_schedule):
        """
        Monte Carlo simulation of cascading delay propagation along a
        single aircraft rotation. Returns total propagated minutes.
        """
        if len(ac_schedule) < 2:
            return 0
        total_prop_delay = 0
        current_delay = 0

        for i in range(len(ac_schedule) - 1):
            if random.random() < 0.20:  # 20% chance of an independent 30-min disruption
                current_delay += 30

            t1_arr = ac_schedule.iloc[i]['arrival_time'] + pd.Timedelta(minutes=current_delay)
            t2_dep = ac_schedule.iloc[i + 1]['departure_time']
            gap = (t2_dep - t1_arr).total_seconds() / 60

            if gap < 45:
                prop = 45 - gap
                current_delay += prop
                total_prop_delay += prop
            else:
                current_delay = max(0, current_delay - (gap - 45))

        return total_prop_delay

    # ------------------------------------------------------------------
    # FITNESS
    # ------------------------------------------------------------------

    def fitness(self, individual):
        """
        Multi-objective fitness: maximizes profit, penalizes cancellations,
        delay propagation, contrail risk, and TAT violations.
        """
        assigned = individual[individual['is_canceled'] == 0]
        canceled = individual[individual['is_canceled'] == 1]

        score = 0.0

        # 1. Financial objective
        score += float(assigned['revenue_tl'].sum())
        score -= float((assigned['op_cost_tl'] + assigned['fuel_cost_tl']).sum())
        score -= float((canceled['revenue_tl'] * 3).sum())  # rebooking cost multiplier
        score -= float((assigned['assigned_delay'] * assigned['delay_cost_per_min']).sum())

        # 2. Contrail ESG penalty
        if 'contrail_risk' in assigned.columns:
            score -= float((assigned['contrail_risk'] * 500 * 10).sum())

        # 3. Cascading delay resilience penalty
        for ac in assigned['assigned_ac'].unique():
            ac_schedule = assigned[assigned['assigned_ac'] == ac].sort_values('departure_time')
            prop_delay = self.simulate_delay_propagation(ac_schedule)
            score -= prop_delay * 1000

        # 4. Hard constraint: range violation
        if 'dist_km' in assigned.columns and 'ac_range_km' in assigned.columns:
            violations = (assigned['dist_km'] > assigned['ac_range_km']).sum()
            score -= violations * 1e6

        # 5. Rotation stability: reward adequate TAT, penalize violations
        for ac in assigned['assigned_ac'].unique():
            ac_schedule = assigned[assigned['assigned_ac'] == ac].sort_values('departure_time')
            if len(ac_schedule) > 1:
                for i in range(len(ac_schedule) - 1):
                    t1_arr = ac_schedule.iloc[i]['arrival_time']
                    t2_dep = ac_schedule.iloc[i + 1]['departure_time']
                    gap = (t2_dep - t1_arr).total_seconds() / 60
                    if gap >= 45:
                        score += (gap // 15) * self.lambda_stability
                    else:
                        score -= 5e5

        return score

    # ------------------------------------------------------------------
    # MAIN SOLVE LOOP
    # ------------------------------------------------------------------

    def solve(self, initial_seed=None):
        logger.info(f"--- Hybrid GA v9.0 (Tournament + GARSRev + Rotation Crossover) Başlıyor ---")
        logger.info(f"    Pop: {self.pop_size} | Nesil: {self.generations} | Uçuş: {len(self.flights)}")

        # Initialize population with variety: seed + random permutations
        population = []
        if initial_seed is not None:
            population.append(initial_seed.copy())

        while len(population) < self.pop_size:
            ind = self.flights.copy()
            # Randomize aircraft assignments to create initial diversity
            ind['assigned_ac'] = [random.choice(self._ac_list) for _ in range(len(ind))]
            population.append(ind)

        for gen in range(self.generations):
            # Evaluate fitness
            pop_fitness = [(ind, self.fitness(ind)) for ind in population]
            pop_fitness.sort(key=lambda x: x[1], reverse=True)

            fit_values = [x[1] for x in pop_fitness]
            best = fit_values[0]
            avg = float(np.mean(fit_values))
            std = float(np.std(fit_values))
            self.stats.append({'gen': gen, 'best': best, 'avg': avg, 'std': std})
            logger.info(f"Nesil {gen:02d}: Best={best:,.0f} | Avg={avg:,.0f} | StdDev={std:,.2f}")

            # Elitism: keep top 2
            new_pop = [pop_fitness[i][0] for i in range(2)]

            while len(new_pop) < self.pop_size:
                # Tournament selection (replaces random top-10 sampling)
                p1 = self._tournament_select(pop_fitness, k=4)
                p2 = self._tournament_select(pop_fitness, k=4)

                # Rotation crossover
                child = self.aircraft_rotation_crossover(p1, p2)

                # Mutation (probabilities unchanged from v8)
                r = random.random()
                if r < 0.10:
                    child = self.point_mutation(child)
                elif r < 0.20:
                    child = self.reversal_mutation(child)
                elif r < 0.25:
                    child = self.quantum_tunneling_mutation(child)

                new_pop.append(child)

            population = new_pop

        # Final evaluation to return best individual
        final_fitness = [(ind, self.fitness(ind)) for ind in population]
        final_fitness.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"GA Tamamlandı. Final En İyi Skor: {final_fitness[0][1]:,.0f}")
        return final_fitness[0][0]
