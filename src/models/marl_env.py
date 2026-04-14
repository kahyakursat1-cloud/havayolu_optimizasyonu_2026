import functools
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from pettingzoo import ParallelEnv
from pettingzoo.utils import parallel_to_aec, wrappers

class AviationMARLEnv(ParallelEnv):
    """
    v21.0 "Leader Edition" MARL Environment.
    
    Each Aircraft is an autonomous Agent.
    Agents negotiate for "priority" and "slots" during recovery.
    """
    metadata = {"render_modes": ["human"], "name": "aviation_singularity_marl_v21"}

    def __init__(self, simulator, flights_df):
        self.sim = simulator
        self.initial_df = flights_df.copy()
        
        # Each unique aircraft_id is an agent
        self.possible_agents = sorted(self.initial_df['aircraft_id'].unique().tolist())
        self.agent_name_mapping = dict(zip(self.possible_agents, range(len(self.possible_agents))))
        
        # Obs: [Delay, Next_Leg_PLF, Maintenance_Risk, Hub_Congestion] (Normalized)
        self.observation_spaces = {
            agent: spaces.Box(low=0, high=1, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # Actions: 0: Optimal, 1: Minor_Delay, 2: Major_Delay, 3: Swap_Proposal
        self.action_spaces = {
            agent: spaces.Discrete(4)
            for agent in self.possible_agents
        }

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return self.action_spaces[agent]

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.current_df = self.initial_df.copy()
        
        observations = {}
        for agent in self.agents:
            observations[agent] = self._get_obs(agent)
            
        return observations, {}

    def step(self, actions):
        """
        Parallel step where all agents act simultaneously.
        """
        rewards = {}
        terminations = {agent: False for agent in self.agents}
        truncations = {agent: False for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        
        # 1. Apply local actions
        for agent, action in actions.items():
            # (Simplified) Apply action to the aircraft's next available flight
            mask = (self.current_df['aircraft_id'] == agent) & (self.current_df['is_canceled'] == 0)
            if any(mask):
                idx = self.current_df[mask].index[0]
                if action == 1: self.current_df.loc[idx, 'assigned_delay'] += 15
                elif action == 2: self.current_df.loc[idx, 'assigned_delay'] += 45
        
        # 2. Collaborative Reward Calculation
        # Every agent gets a mix of Local Punctuality and Global Fleet Profit
        global_avg_delay = self.current_df['assigned_delay'].mean()
        
        for agent in self.agents:
            ac_df = self.current_df[self.current_df['aircraft_id'] == agent]
            local_delay = ac_df['assigned_delay'].mean() if not ac_df.empty else 0
            
            # Local Penalty for local delay
            local_rew = - (local_delay / 120.0)
            
            # Global Benefit for keeping system delay low
            global_rew = - (global_avg_delay / 150.0)
            
            rewards[agent] = local_rew * 0.7 + global_rew * 0.3

        # (Simplified) Single-step tactical recovery session
        for agent in self.agents:
            terminations[agent] = True

        observations = {agent: self._get_obs(agent) for agent in self.agents}
        self.agents = [] # Terminate episode
        
        return observations, rewards, terminations, truncations, infos

    def _get_obs(self, agent):
        ac_df = self.current_df[self.current_df['aircraft_id'] == agent]
        if ac_df.empty: return np.zeros(4, dtype=np.float32)
        
        f = ac_df.iloc[0]
        # [Local_Delay, LF, Maintenance_Risk, Hub_Risk]
        obs = np.array([
            min(1.0, f.get('assigned_delay', 0) / 180.0),
            float(f.get('load_factor', 0)),
            min(1.0, f.get('ac_remaining_fh', 0) / 100.0),
            min(1.0, f.get('weather_risk', 0))
        ], dtype=np.float32)
        return obs
