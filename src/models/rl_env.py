import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class AviationRLBotEnv(gym.Env):
    """
    🚀 v17.0 "Neural Commander" Gymnasium Environment
    Wraps the Aviation Singularity simulator for Reinforcement Learning.
    
    Goal: Maximize Fleet Efficiency (Profit + PLF) while minimizing Disruption.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, simulator, initial_df):
        super(AviationRLBotEnv, self).__init__()
        self.sim = simulator
        self.initial_df = initial_df.copy()
        self.current_df = initial_df.copy()
        
        # Action Space: 
        # 0: Keep Original
        # 1: Delay by 15m
        # 2: Delay by 30m
        # 3: Cancel Flight
        self.action_space = spaces.Discrete(4)
        
        # Observation Space: [Delay, PaxCount, MaintenanceHealth, CrewFatigue, LoadFactor]
        # Normalized between 0 and 1
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(5,), dtype=np.float32
        )
        
        self.current_step = 0
        self.max_steps = len(initial_df)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_df = self.initial_df.copy()
        self.current_step = 0
        
        obs = self._get_obs()
        return obs, {}

    def _get_obs(self):
        # Extract normalized state for the current flight being considered
        f = self.current_df.iloc[self.current_step]
        obs = np.array([
            min(1.0, f['assigned_delay'] / 180),
            min(1.0, f['passenger_count'] / 300),
            min(1.0, f['ac_remaining_fh'] / 100),
            min(1.0, f['crew_base_fatigue'] / 20),
            f['load_factor']
        ], dtype=np.float32)
        return obs

    def step(self, action):
        # 1. Apply Action to Current Flight
        if action == 1:
            self.current_df.iloc[self.current_step, self.current_df.columns.get_loc('assigned_delay')] += 15
        elif action == 2:
            self.current_df.iloc[self.current_step, self.current_df.columns.get_loc('assigned_delay')] += 30
        elif action == 3:
            self.current_df.iloc[self.current_step, self.current_df.columns.get_loc('is_canceled')] = 1

        # 2. Calculate Reward
        f = self.current_df.iloc[self.current_step]
        reward = 0
        
        if f['is_canceled'] == 1:
            reward = -5.0 # High penalty for cancellation
        else:
            # Profit basis
            reward += f['revenue_tl'] / 100000 
            # Delay penalty
            reward -= (f['assigned_delay'] / 60) * 2.0
            # Connection health bonus
            if f['assigned_delay'] < 30:
                reward += 1.0

        # 3. Advance Step
        self.current_step += 1
        truncated = False
        terminated = self.current_step >= self.max_steps
        
        obs = self._get_obs() if not terminated else np.zeros(5, dtype=np.float32)
        
        return obs, reward, terminated, truncated, {}

    def render(self):
        print(f"Step: {self.current_step} | Fleet PLF: {self.current_df['load_factor'].mean():.2f}")
