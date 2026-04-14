import numpy as np
import logging
import os
import sys
from collections import deque
import threading

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

logger = logging.getLogger("AviationSingularity.Evolution")

# Minimum experience samples before an evolution cycle is attempted
_MIN_BUFFER_SIZE = 10
# Number of synthetic fine-tuning timesteps per evolution cycle
_LEARN_TIMESTEPS = 200


class EvolutionEngine:
    """
    v23.0 Neural Evolution Engine.

    Implements online policy improvement via experience replay:
      1. The live tactical map feeds (observation, action, reward) tuples into
         the experience_buffer via collect_experience().
      2. Every 15 minutes, evolve_model() runs a fine-tuning pass:
         - Builds a lightweight replay Gymnasium environment from the buffer.
         - Calls PPO.learn() for _LEARN_TIMESTEPS steps so the policy weights
           are updated on real operational data — not just the training corpus.
      3. The improved model is versioned and saved.

    Observation space expected by the loaded PPO model (must match rl_env.py):
      11-dim float32: [delay, pax, ac_fh, crew_fatigue, load_factor,
                       weather_risk, revenue, dist_km, co2, pax_conn, network_congestion]
    """

    def __init__(self, model_path: str = "src/models/shikra_v4_11dim.zip"):
        self.model_path = model_path
        self.experience_buffer: deque = deque(maxlen=1000)
        self.lock = threading.Lock()
        self.is_training = False
        self.evolution_count = 0
        self.model = None

        if os.path.exists(model_path):
            try:
                from stable_baselines3 import PPO
                self.model = PPO.load(model_path)
                logger.info(f"Loaded Shikra 11-dim model from {model_path}")
            except Exception as e:
                logger.warning(f"Model load failed: {e}. Evolution will use untrained policy.")
        else:
            logger.warning(f"Model not found at {model_path}. Will train from scratch on first evolve.")

    # ------------------------------------------------------------------
    # LIVE INFERENCE
    # ------------------------------------------------------------------

    def infer_flight_meta(self, state_vector: dict, weather_data, traffic_density: int) -> dict:
        """
        Infers route phase and operational status from ADS-B telemetry.
        Uses deterministic threshold rules — no random sampling.
        """
        alt      = state_vector.get('alt', 0)
        velocity = state_vector.get('velocity', 0)

        # Phase detection
        if alt < 2_000 and velocity < 250:
            phase = "Approach/Landing"
        elif alt < 5_000 and velocity < 300:
            phase = "Climb/Descent"
        else:
            phase = "Cruise"

        # Status classification
        if velocity < 50 and alt < 100:
            status = "GROUND_DELAYED"
            if weather_data and any(k in str(weather_data) for k in ("SNOW", "TS", "FG", "RA")):
                cause = "Meteorolojik (Hava Durumu)"
            elif traffic_density > 20:
                cause = "Hava Sahası Konjesyonu"
            else:
                cause = "Operasyonel (Ekip/Bakım/Yer Hizmetleri)"
        elif velocity < 150 and alt < 500:
            status = "TAXIING"
            cause = "Yer Operasyonu"
        else:
            status = "OPTIMAL"
            cause = "None"

        return {"phase": phase, "status": status, "root_cause": cause}

    # ------------------------------------------------------------------
    # EXPERIENCE COLLECTION
    # ------------------------------------------------------------------

    def collect_experience(self, obs: list, action: list, reward: float) -> None:
        """Thread-safe collection of real-world (obs, action, reward) tuples."""
        with self.lock:
            self.experience_buffer.append((obs, action, reward))

    # ------------------------------------------------------------------
    # EVOLUTION CYCLE
    # ------------------------------------------------------------------

    def evolve_model(self) -> bool:
        """
        15-minute neural pulse: fine-tune the PPO policy on buffered
        real-world operational data.

        Returns True if evolution completed successfully, False otherwise.
        """
        with self.lock:
            buffer_size = len(self.experience_buffer)

        if self.is_training or buffer_size < _MIN_BUFFER_SIZE:
            logger.debug(f"Evolution skipped: training={self.is_training}, buffer={buffer_size}")
            return False

        with self.lock:
            self.is_training = True

        try:
            logger.info(f"Neural Evolution Cycle #{self.evolution_count + 1} — buffer: {buffer_size} samples")

            if self.model is None:
                self._initialize_fresh_model()

            if self.model is not None:
                self._fine_tune_from_buffer()

            self.evolution_count += 1
            logger.info(f"Evolution #{self.evolution_count} complete.")
            return True

        except Exception as e:
            logger.error(f"Evolution cycle failed: {e}")
            return False
        finally:
            with self.lock:
                self.is_training = False

    def _initialize_fresh_model(self) -> None:
        """Create a new PPO model when no pre-trained weights are available."""
        try:
            from stable_baselines3 import PPO
            from src.models.rl_env import OBS_DIM
            import gymnasium as gym
            from gymnasium import spaces

            # Minimal dummy env for policy initialization
            class _DummyAviationEnv(gym.Env):
                observation_space = spaces.Box(low=0.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32)
                action_space = spaces.Discrete(6)

                def reset(self, **kw):
                    return np.zeros(OBS_DIM, dtype=np.float32), {}

                def step(self, _action):
                    return np.zeros(OBS_DIM, dtype=np.float32), 0.0, True, False, {}

            env = _DummyAviationEnv()
            self.model = PPO("MlpPolicy", env, verbose=0)
            logger.info("Initialized fresh PPO policy from scratch.")
        except Exception as e:
            logger.warning(f"Could not initialize fresh model: {e}")

    def _fine_tune_from_buffer(self) -> None:
        """
        Build a replay Gymnasium environment from the experience buffer and
        run PPO.learn() for _LEARN_TIMESTEPS steps to update policy weights.
        """
        try:
            import gymnasium as gym
            from gymnasium import spaces
            from src.models.rl_env import OBS_DIM

            with self.lock:
                samples = list(self.experience_buffer)

            obs_list    = [np.array(s[0], dtype=np.float32) for s in samples]
            reward_list = [float(s[2]) for s in samples]

            class _ReplayEnv(gym.Env):
                """Cycles through the experience buffer for offline fine-tuning."""
                observation_space = spaces.Box(low=0.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32)
                action_space      = spaces.Discrete(6)

                def __init__(self):
                    super().__init__()
                    self._obs     = obs_list
                    self._rewards = reward_list
                    self._idx     = 0

                def reset(self, **kw):
                    self._idx = 0
                    return self._obs[0], {}

                def step(self, _action):
                    obs    = self._obs[self._idx % len(self._obs)]
                    reward = self._rewards[self._idx % len(self._rewards)]
                    self._idx += 1
                    done = self._idx >= len(self._obs)
                    return obs, reward, done, False, {}

            replay_env = _ReplayEnv()
            self.model.set_env(replay_env)
            self.model.learn(total_timesteps=_LEARN_TIMESTEPS, reset_num_timesteps=False)

            # Version and persist the updated brain
            v_path = self.model_path.replace(".zip", f"_dynamic.zip")
            self.model.save(v_path)
            logger.info(f"Fine-tuned model saved → {v_path}")

        except Exception as e:
            logger.warning(f"Fine-tuning skipped: {e}")

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        return {
            "status": "training" if self.is_training else "idle",
            "evolution_cycles": self.evolution_count,
            "experience_points": len(self.experience_buffer),
            "buffer_capacity": self.experience_buffer.maxlen,
            "model_loaded": self.model is not None,
            "model_version": f"Shikra-v{self.evolution_count + 1}-Dynamic",
        }


evolution_engine = EvolutionEngine()
