import numpy as np
import pandas as pd
import random
import logging
import time

logger = logging.getLogger("AviationSingularity.QIO")

class QuantumInspiredGA:
    """
    v22.0 Quantum-Inspired Genetic Algorithm (QIGA).
    
    Representation: Q-bit individuals where genes are probability amplitudes.
    Evolution: Interference via Quantum Rotation Gates (U-gates).
    Objective: High-speed convergence for non-deterministic tactical rescheduling.
    """
    def __init__(self, flights_df, pop_size=30, generations=20):
        self.flights = flights_df.copy()
        if 'is_canceled' not in self.flights.columns: self.flights['is_canceled'] = 0
        if 'assigned_delay' not in self.flights.columns: self.flights['assigned_delay'] = 0
        
        self.pop_size = pop_size
        self.generations = generations
        self.ac_list = sorted(self.flights['aircraft_id'].unique().tolist())
        self.num_ac = len(self.ac_list)
        self.num_flights = len(self.flights)
        
        # Q-bit population (theta angles)
        # Initial state: Pi/4 (Superposition with equal probability)
        self.q_pop = np.full((pop_size, self.num_flights, self.num_ac), np.pi / 4)
        
        # Best found so far
        self.best_individual = None
        self.best_fitness = -np.inf
        self.stats = []

    def _collapse(self, q_ind):
        """
        Collapses Q-bit superposition into a discrete operational schedule.
        Probability of picking AC_j = sin(theta_j)^2
        """
        collapsed = self.flights.copy()
        assignments = []
        
        # Compute probabilities: sin^2(theta)
        probs = np.sin(q_ind)**2
        # Normalize to sum to 1
        probs = probs / probs.sum(axis=1, keepdims=True)
        
        for i in range(self.num_flights):
            ac_idx = np.random.choice(range(self.num_ac), p=probs[i])
            assignments.append(self.ac_list[ac_idx])
            
        collapsed['assigned_ac'] = assignments
        return collapsed

    def _update_qbits(self, q_ind, best_discrete, fit_individual, fit_best):
        """
        Quantum Rotation Gate (U-gate).
        Rotates the Q-bit toward the target (best_discrete) based on fitness delta.
        """
        new_q = q_ind.copy()
        target_ac_indices = [self.ac_list.index(ac) for ac in best_discrete['assigned_ac']]
        
        # Delta theta logic (tunable)
        delta = 0.05 * np.pi 
        
        # Strategy: Rotate toward 1.0 (pi/2) for the target aircraft index,
        # and toward 0.0 for others.
        for i, target_idx in enumerate(target_ac_indices):
            for j in range(self.num_ac):
                if j == target_idx:
                    # Move toward Pi/2
                    new_q[i, j] = min(np.pi/2, new_q[i, j] + delta)
                else:
                    # Move toward 0
                    new_q[i, j] = max(0, new_q[i, j] - delta / (self.num_ac - 1))
        return new_q

    def fitness(self, individual, strategy='PROFIT'):
        """
        Multi-objective fitness incorporating v22.0 RASM and Strategy.
        """
        assigned = individual[individual['is_canceled'] == 0]
        if assigned.empty: return -1e9
        
        revenue = assigned['revenue_tl'].sum()
        fuel_cost = assigned['fuel_cost_tl'].sum()
        op_cost = assigned['op_cost_tl'].sum()
        delay_cost = (assigned['assigned_delay'] * assigned['delay_cost_per_min']).sum()
        
        # RASM calculation (v22.0)
        total_pax = assigned['passenger_count'].sum()
        total_dist = assigned['dist_km'].sum()
        rasm = revenue / (total_pax * total_dist + 1)
        
        if strategy == 'PROFIT':
            score = revenue - fuel_cost - op_cost - delay_cost + (rasm * 10000)
        else: # VOLUME mode
            score = total_pax * 100 - delay_cost
            
        return score

    def solve(self, strategy='PROFIT'):
        start_time = time.time()
        logger.info(f"⚛️ QIO Race Mode Engagement: Population={self.pop_size} | Strategy={strategy}")
        
        for gen in range(self.generations):
            discrete_pop = []
            fitness_pop = []
            
            # Collapse and Evaluate
            for i in range(self.pop_size):
                discrete = self._collapse(self.q_pop[i])
                fit = self.fitness(discrete, strategy)
                discrete_pop.append(discrete)
                fitness_pop.append(fit)
                
                if fit > self.best_fitness:
                    self.best_fitness = fit
                    self.best_individual = discrete.copy()
            
            # Interference phase: Update Q-bits towards global best
            for i in range(self.pop_size):
                self.q_pop[i] = self._update_qbits(
                    self.q_pop[i], 
                    self.best_individual, 
                    fitness_pop[i], 
                    self.best_fitness
                )
            
            avg_fit = np.mean(fitness_pop)
            self.stats.append({'gen': gen, 'best': self.best_fitness, 'avg': avg_fit})
            
        solve_time = time.time() - start_time
        logger.info(f"✅ QIO Convergence in {solve_time:.2f}s | Score: {self.best_fitness:,.0f}")
        return self.best_individual, solve_time
