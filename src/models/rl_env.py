import gymnasium as gym
from gymnasium import spaces
import numpy as np

# Normalization constants (domain knowledge)
_MAX_DELAY_MIN = 180.0
_MAX_PAX = 400.0
_MAX_REMAINING_FH = 100.0
_MAX_FATIGUE = 20.0
_MAX_REVENUE_TL = 500_000.0
_MAX_DIST_KM = 10_000.0
_MAX_CO2_KG = 50_000.0
_MAX_PAX_CONN = 50.0
_MAX_WEATHER_RISK = 1.0
_MAX_DELAY_COST = 5_000.0

OBS_DIM = 10

class AviationRLBotEnv(gym.Env):
    """
    v18.0 "Neural Commander" Gymnasium Environment.
    Wraps the Aviation Singularity CP-SAT simulator for Reinforcement Learning.

    Goal: Maximize Fleet Efficiency (Profit + PLF + CQI) while minimizing
    disruption impact, CO2 emissions, and crew fatigue.

    Observation Space (10-dim, all normalized [0,1]):
      0  assigned_delay       — current delay load on the flight
      1  passenger_count      — pax demand pressure
      2  ac_remaining_fh      — maintenance urgency (low = grounding risk)
      3  crew_base_fatigue    — crew duty-hour exposure
      4  load_factor          — commercial revenue density
      5  weather_risk         — external disruption probability
      6  revenue_tl           — flight commercial value
      7  dist_km              — route length (operational complexity)
      8  co2_kg               — carbon cost sensitivity
      9  pax_connection_count — downstream connection vulnerability

    Action Space (6 discrete actions):
      0: Keep Original         — no intervention
      1: Delay +15 min         — minor delay absorption
      2: Delay +30 min         — moderate recovery buffer
      3: Delay +60 min         — major weather/maintenance hold
      4: Cancel Flight         — last-resort, high rebooking cost
      5: Priority Bump         — reset delay to 0, max crew effort
                                 (used for high-LF connecting flights)
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, simulator, initial_df):
        super().__init__()
        self.sim = simulator
        self.initial_df = initial_df.copy()
        self.current_df = initial_df.copy()

        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32
        )

        self.current_step = 0
        self.max_steps = len(initial_df)
        self._episode_co2 = 0.0
        self._episode_revenue = 0.0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_df = self.initial_df.copy()
        self.current_step = 0
        self._episode_co2 = 0.0
        self._episode_revenue = 0.0
        return self._get_obs(), {}

    def _get_obs(self):
        f = self.current_df.iloc[self.current_step]
        obs = np.array([
            min(1.0, f.get('assigned_delay', 0) / _MAX_DELAY_MIN),
            min(1.0, f.get('passenger_count', 0) / _MAX_PAX),
            min(1.0, f.get('ac_remaining_fh', 0) / _MAX_REMAINING_FH),
            min(1.0, f.get('crew_base_fatigue', 0) / _MAX_FATIGUE),
            float(f.get('load_factor', 0)),
            min(1.0, f.get('weather_risk', 0) / _MAX_WEATHER_RISK),
            min(1.0, f.get('revenue_tl', 0) / _MAX_REVENUE_TL),
            min(1.0, f.get('dist_km', 0) / _MAX_DIST_KM),
            min(1.0, f.get('co2_kg', 0) / _MAX_CO2_KG),
            min(1.0, f.get('pax_connection_count', 0) / _MAX_PAX_CONN),
        ], dtype=np.float32)
        return obs

    def step(self, action):
        delay_col = self.current_df.columns.get_loc('assigned_delay')
        cancel_col = self.current_df.columns.get_loc('is_canceled')

        # 1. Apply action
        if action == 1:
            self.current_df.iloc[self.current_step, delay_col] += 15
        elif action == 2:
            self.current_df.iloc[self.current_step, delay_col] += 30
        elif action == 3:
            self.current_df.iloc[self.current_step, delay_col] += 60
        elif action == 4:
            self.current_df.iloc[self.current_step, cancel_col] = 1
        elif action == 5:
            # Priority Bump: zero out delay, mark for expedited handling
            self.current_df.iloc[self.current_step, delay_col] = 0

        # 2. Compute multi-objective reward
        f = self.current_df.iloc[self.current_step]
        reward = self._compute_reward(f)

        # 3. Track episode-level KPIs for terminal bonus
        if f.get('is_canceled', 0) != 1:
            self._episode_revenue += f.get('revenue_tl', 0)
            self._episode_co2 += f.get('co2_kg', 0) * (1 - f.get('saf_usage', 0) / 100)

        # 4. Advance
        self.current_step += 1
        truncated = False
        terminated = self.current_step >= self.max_steps

        if terminated:
            # Episode-end bonus: reward high fleet PLF and low CO2
            fleet_plf = self.current_df['load_factor'].mean()
            co2_factor = max(0.0, 1.0 - self._episode_co2 / (self.max_steps * _MAX_CO2_KG))
            reward += fleet_plf * 5.0 + co2_factor * 2.0
            obs = np.zeros(OBS_DIM, dtype=np.float32)
        else:
            obs = self._get_obs()

        return obs, reward, terminated, truncated, {}

    def _compute_reward(self, f) -> float:
        if f.get('is_canceled', 0) == 1:
            # Cancellation: heavy fixed penalty + pax rebooking cost
            pax_rebooking = f.get('passenger_count', 0) * 0.05 / _MAX_PAX
            return -8.0 - pax_rebooking

        delay = f.get('assigned_delay', 0)
        revenue = f.get('revenue_tl', 0)
        lf = float(f.get('load_factor', 0))
        pax_conn = int(f.get('pax_connection_count', 0))
        co2 = f.get('co2_kg', 0)
        saf = f.get('saf_usage', 0) / 100.0
        delay_cost_per_min = f.get('delay_cost_per_min', 100)

        # Revenue component (normalized)
        reward = revenue / _MAX_REVENUE_TL * 3.0

        # Delay penalty: scaled by cost-per-minute and connection exposure
        conn_multiplier = 1.0 + pax_conn / _MAX_PAX_CONN  # connecting pax amplify delay cost
        reward -= (delay * delay_cost_per_min / (_MAX_DELAY_MIN * _MAX_DELAY_COST)) * 4.0 * conn_multiplier

        # Connection quality bonus: intact connections are high commercial value
        if delay < 30 and pax_conn > 0:
            reward += 1.5
        elif delay == 0:
            reward += 0.5

        # PLF bonus: high load-factor flights contribute more to network revenue
        reward += lf * 1.5

        # ESG: reward SAF usage, penalize high net CO2
        net_co2 = co2 * (1.0 - saf * 0.8)
        reward -= net_co2 / _MAX_CO2_KG * 1.0
        reward += saf * 0.5

        return float(reward)

    def render(self):
        active = self.current_df[self.current_df['is_canceled'] == 0]
        plf = active['load_factor'].mean() if not active.empty else 0.0
        avg_delay = active['assigned_delay'].mean() if not active.empty else 0.0
        print(f"Step {self.current_step}/{self.max_steps} | PLF: {plf:.2f} | Avg Delay: {avg_delay:.1f}m | Active: {len(active)}")
