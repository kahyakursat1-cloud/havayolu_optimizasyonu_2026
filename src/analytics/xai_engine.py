import shap
import torch
import numpy as np
import pandas as pd
import logging
import os
from stable_baselines3 import PPO

logger = logging.getLogger("AviationSingularity.XAI")

class ShikraExplainer:
    """
    v21.0 XAI Layer.
    Provides SHAP-based feature importance for PPO decisions.
    
    Features (v20.0 11-dim):
      0: Delay, 1: Pax, 2: AC FH, 3: Crew Fatigue, 4: LF,
      5: Weather, 6: Revenue, 7: Distance, 8: CO2, 9: Pax Conn, 10: Network Load
    """
    def __init__(self, model_path="src/models/shikra_v4_11dim.zip"):
        self.feature_names = [
            "Assigned Delay", "Pax Demand", "AC Maintenance", "Crew Fatigue",
            "Load Factor", "Weather Risk", "Revenue", "Distance", "CO2 Emission",
            "Pax Connections", "Network Load"
        ]
        self.model = None
        if os.path.exists(model_path):
            try:
                self.model = PPO.load(model_path)
                logger.info("XAI Engine: Model loaded for explanation.")
            except Exception as e:
                logger.error(f"XAI Engine: Model load failed {e}")

    def explain_decision(self, observation):
        """
        Uses a KernelExplainer (or GradientExplainer if compatible) 
        to compute SHAP values for a single observation.
        """
        if self.model is None:
            return {"error": "Model not loaded"}

        # Define a wrapper function for SHAP (maps obs -> action probabilities)
        def model_predict(obs_batch):
            obs_tensor = torch.tensor(obs_batch, dtype=torch.float32)
            # Use the policy net to get logits
            with torch.no_grad():
                dist = self.model.policy.get_distribution(obs_tensor)
                # Return probabilities for all actions (6 actions)
                return dist.distribution.probs.numpy()

        # Since PPO is non-linear, we use KernelExplainer on a small neighborhood or global background
        # Background: Zeros (no risk case)
        background = np.zeros((1, 11))
        explainer = shap.KernelExplainer(model_predict, background)
        
        # Explain the current tactical observation
        shap_values = explainer.shap_values(observation.reshape(1, -1))
        
        # We focus on the importance for the "best" action chosen
        action, _states = self.model.predict(observation, deterministic=True)
        
        # Extract SHAP values for the specific action chosen
        # shap_values is a list of arrays (one per output class)
        # We take the array for the chosen action index
        chosen_action_shap = shap_values[action][0]
        
        explanation = {}
        for name, val in zip(self.feature_names, chosen_action_shap):
            explanation[name] = float(val)
            
        return {
            "chosen_action": int(action),
            "feature_contributions": explanation,
            "top_reason": self.feature_names[np.argmax(np.abs(chosen_action_shap))]
        }

# Singleton Instance
shikra_xai = ShikraExplainer()
