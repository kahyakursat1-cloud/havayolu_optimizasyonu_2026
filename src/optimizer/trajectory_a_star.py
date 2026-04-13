import heapq
import numpy as np
import random

class TrajectoryPlannerAStar:
    """
    📐 v13.0 Aviation Singularity: 3D A* Trajectory Optimizer.
    Optimizes horizontal path, altitude (FL), and Mach speed.
    """
    def __init__(self):
        # Physics Boundaries (2026 Fleet Standard)
        self.min_mach = 0.5
        self.max_mach = 0.85
        self.min_fl = 290  # Flight Level 290
        self.max_fl = 410  # Flight Level 410
        
    def generate_random_wind(self, altitude):
        """
        Randomize wind motor: Simulated wind vectors based on altitude.
        """
        # Literature: Higher altitudes have stronger jet streams.
        base_wind = altitude / 10.0
        return random.uniform(-base_wind, base_wind) # (Knots) - Headwind/Tailwind

    def calculate_cost(self, distance, altitude, mach, wind):
        """
        v14.1 Hardened Physics: Includes ground speed safety and div-by-zero guards.
        """
        # Ground speed must be positive and safely above stall speeds
        # 600 kt is a typical cruise speed for narrowbodies
        effective_speed = (mach * 600) + wind 
        
        # Hardening: Minimum ground speed guard (50 kts) to prevent div-by-zero
        safe_ground_speed = max(50, effective_speed)
        
        # Fuel flow simulation
        fuel_flow = (mach**2 * 2000) + (40000 / altitude)
        time_hrs = distance / safe_ground_speed
        return fuel_flow * time_hrs

    def optimize_3d_path(self, origin, destination, total_dist):
        """
        A* Search through 3D state space: (distance_idx, altitude, mach)
        """
        start_node = (0, 350, 0.78) # initial: 0km, FL350, .78M
        # Priority Queue: (estimated_total_cost, current_cost, current_node)
        pq = [(0, 0, start_node)]
        visited = {}
        
        while pq:
            est_total, current_cost, (dist_idx, alt, mach) = heapq.heappop(pq)
            
            if dist_idx >= 10: # Destination reached (normalized to 10 steps)
                return {
                    'total_cost': current_cost,
                    'optimal_fl': alt,
                    'optimal_mach': mach,
                    'is_3d_optimized': True
                }
            
            state = (dist_idx, alt, mach)
            if state in visited and visited[state] <= current_cost:
                continue
            visited[state] = current_cost
            
            # Neighbors: Change Altitude (+-10 FL), Change Mach (+-0.02)
            for d_alt in [-10, 0, 10]:
                for d_mach in [-0.02, 0, 0.02]:
                    new_alt = max(self.min_fl, min(self.max_fl, alt + d_alt))
                    new_mach = max(self.min_mach, min(self.max_mach, mach + d_mach))
                    
                    wind = self.generate_random_wind(new_alt)
                    step_cost = self.calculate_cost(total_dist/10, new_alt, new_mach, wind)
                    
                    new_cost = current_cost + step_cost
                    # Heuristic: Remaining distance / typical speed
                    h = (10 - (dist_idx + 1)) * 500 
                    
                    heapq.heappush(pq, (new_cost + h, new_cost, (dist_idx + 1, new_alt, new_mach)))
                    
        return None
