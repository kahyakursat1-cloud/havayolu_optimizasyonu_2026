import os
import gymnasium as gym
import pandas as pd
from stable_baselines3 import PPO
from src.models.rl_env import AviationRLBotEnv
from src.generator.synthetic_env import AdvancedAirlineSimulator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_neural_commander():
    logger.info("🚀 Initializing Neural Commander Training Loop (v20.0 11-Dim Obs Space)...")
    
    # Setup the simulator the right way
    sim = AdvancedAirlineSimulator(seed=42)
    # Generate tactical data for the agent (1 full day of operations)
    initial_df = sim.generate_full_scenario(days=1)
    
    # Initialize the Gymnasium environment with the valid simulator and dataframe
    env = AviationRLBotEnv(sim, initial_df)
    
    # Initialize PPO Agent with tuned hyperparameters for aviation disruption
    model = PPO("MlpPolicy", env, verbose=1, 
                learning_rate=0.0003, 
                n_steps=2048, 
                batch_size=64, 
                tensorboard_log="./logs/ai_training/")
    
    logger.info("🧠 Brain Synapsing... Starting 25,000 training steps for 11-dim state space.")
    model.learn(total_timesteps=25000)
    
    # Save the professional grade model
    model_path = os.path.join("src", "models", "shikra_v4_11dim")
    model.save(model_path)
    logger.info(f"✅ Training Complete. Neural model saved as {model_path}.zip")

if __name__ == "__main__":
    train_neural_commander()
