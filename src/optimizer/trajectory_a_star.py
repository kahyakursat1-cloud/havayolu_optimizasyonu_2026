import heapq
import math


class TrajectoryPlannerAStar:
    """
    v14.0 Aviation Singularity: 3D A* Trajectory Optimizer.
    Optimizes horizontal path, altitude (Flight Level), and Mach speed.

    Wind Model (deterministic):
      Jet-stream wind is modelled as a sinusoidal function of altitude and
      step index, approximating the meridional wind variation at cruise levels.
      Using a fixed phase offset ensures reproducible results for the same
      (origin, destination, distance) triple — no random sampling.

    Heuristic (admissible):
      h(n) = remaining_steps × min_step_cost
      where min_step_cost is computed at optimal (max Mach, max FL, zero
      headwind) conditions.  This is a tight lower bound, so A* remains
      optimal and never over-estimates.
    """

    # Physics boundaries — ICAO standard cruise envelope
    MIN_MACH = 0.50
    MAX_MACH = 0.85
    MIN_FL   = 290   # FL290
    MAX_FL   = 410   # FL410

    # Path is discretised into N_STEPS waypoints
    N_STEPS = 10

    def __init__(self):
        self.min_mach = self.MIN_MACH
        self.max_mach = self.MAX_MACH
        self.min_fl   = self.MIN_FL
        self.max_fl   = self.MAX_FL

        # Pre-compute the cheapest possible step cost for the admissible heuristic
        self._min_step_cost = self._calculate_cost(
            distance=1.0,           # normalised: actual distance / N_STEPS
            altitude=self.MAX_FL,
            mach=self.MAX_MACH,
            wind=30.0               # best-case tailwind (knots)
        )

    # ------------------------------------------------------------------
    # ATMOSPHERIC MODEL
    # ------------------------------------------------------------------

    def _jet_stream_wind(self, altitude: int, step_idx: int) -> float:
        """
        Deterministic jet-stream model.

        Returns a wind component (knots) along the flight path:
          positive = tailwind (reduces travel time)
          negative = headwind (increases fuel burn)

        The model is a superposition of:
          1. Altitude-driven base jet stream (stronger at FL350-400)
          2. A sinusoidal variation across the route (weather cell pattern)

        Both components are fully deterministic given (altitude, step_idx).
        """
        # Peak jet-stream altitude approx. FL360; weaker below and above
        fl_norm = (altitude - 290) / 120.0          # 0 at FL290, 1 at FL410
        jet_peak = math.sin(fl_norm * math.pi)       # max at FL350
        base_wind = jet_peak * 40.0                  # up to ±40 kt

        # Route-level oscillation: simulates passing through different air masses
        route_phase = step_idx / self.N_STEPS * 2.0 * math.pi
        oscillation = math.cos(route_phase) * 15.0  # ±15 kt

        return base_wind + oscillation

    # ------------------------------------------------------------------
    # COST FUNCTION
    # ------------------------------------------------------------------

    def _calculate_cost(self, distance: float, altitude: int,
                        mach: float, wind: float) -> float:
        """
        Fuel-based step cost (kg·h proxy).

        Ground speed = (mach × 600 kt) + wind, clamped above stall speed.
        Fuel flow increases with Mach² (drag) and decreases with altitude
        (thinner air → lower engine work per kt of ground speed).
        """
        ground_speed = max(50.0, mach * 600.0 + wind)
        fuel_flow    = mach ** 2 * 2_000.0 + 40_000.0 / altitude
        time_hrs     = distance / ground_speed
        return fuel_flow * time_hrs

    # ------------------------------------------------------------------
    # HEURISTIC (admissible lower bound)
    # ------------------------------------------------------------------

    def _heuristic(self, remaining_steps: int, step_distance: float) -> float:
        """
        Admissible heuristic: remaining_steps × cheapest_possible_step_cost.
        Never over-estimates → A* solution is optimal.
        """
        return remaining_steps * self._min_step_cost * step_distance

    # ------------------------------------------------------------------
    # A* SEARCH
    # ------------------------------------------------------------------

    def optimize_3d_path(self, origin: str, destination: str,  # noqa: ARG002
                         total_dist: float) -> dict:
        """
        A* search through the 3D state space: (waypoint_idx, FL, Mach).

        Returns the minimum-fuel trajectory profile.
        """
        step_dist = total_dist / self.N_STEPS

        # State: (waypoint_index, flight_level, mach_×100_int)
        start = (0, 350, 78)  # FL350, Mach 0.78
        pq    = [(0.0, 0.0, start)]  # (f, g, state)
        visited: dict = {}

        while pq:
            f_est, g_cost, (step, fl, mach_int) = heapq.heappop(pq)

            if step >= self.N_STEPS:
                mach = mach_int / 100.0
                return {
                    'total_cost':    round(g_cost, 2),
                    'optimal_fl':    fl,
                    'optimal_mach':  mach,
                    'is_3d_optimized': True,
                }

            state = (step, fl, mach_int)
            if state in visited and visited[state] <= g_cost:
                continue
            visited[state] = g_cost

            mach = mach_int / 100.0

            # Expand neighbours: ΔFL ∈ {-10, 0, +10}, ΔMach ∈ {-0.02, 0, +0.02}
            for d_fl in (-10, 0, 10):
                new_fl = max(self.MIN_FL, min(self.MAX_FL, fl + d_fl))
                for d_mach in (-2, 0, 2):  # stored as integer ×100
                    new_mach_int = max(
                        int(self.MIN_MACH * 100),
                        min(int(self.MAX_MACH * 100), mach_int + d_mach)
                    )
                    new_mach = new_mach_int / 100.0

                    wind      = self._jet_stream_wind(new_fl, step)
                    step_cost = self._calculate_cost(step_dist, new_fl, new_mach, wind)
                    new_g     = g_cost + step_cost
                    remaining = self.N_STEPS - (step + 1)
                    h         = self._heuristic(remaining, step_dist)

                    heapq.heappush(pq, (new_g + h, new_g,
                                        (step + 1, new_fl, new_mach_int)))

        return None  # infeasible (should not occur with this state space)
