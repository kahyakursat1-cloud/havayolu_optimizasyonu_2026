import numpy as np
import random

class BayesianCausalModel:
    """
    🧠 v12.0 Causal Intelligence: Uses Bayesian logic to attribute and 
    predict delay factors, including 2026 Cybersecurity risks.
    """
    def __init__(self):
        # Probabilistic Causal Weights (Literature Based)
        self.p_weather = 0.35
        self.p_security = 0.20
        self.p_technical = 0.15
        self.p_cyber = 0.10      # 2026 Trend: Increased dependency on digital ATC
        self.p_ground_ops = 0.20
        
    def attribute_delay(self, flight_row):
        """
        Attributes a given delay to one or more causal factors using 
        Bayesian inference (Mock).
        """
        delay = flight_row.get('assigned_delay', 0)
        if delay == 0: return "None"
        
        # Bayesian prior adjustment based on environment
        is_night = flight_row.get('is_night_flight', 0)
        is_hub = 1 if flight_row.get('destination') == 'IST' else 0
        
        # Logic: Night flights have higher Cyber risk (updates), Hubs have higher Security risk
        scores = {
            'Weather': self.p_weather * random.random(),
            'Security/TSA': self.p_security * (1.5 if is_hub else 1) * random.random(),
            'Technical': self.p_technical * random.random(),
            'Cyber Attack': self.p_cyber * (2.0 if is_night else 1) * random.random(),
            'Ground Ops': self.p_ground_ops * random.random()
        }
        
        # Attribution: Return the factor with highest probability
        return max(scores, key=scores.get)

    def predict_cyber_risk(self, system_health=98):
        """
        Predicts potential delay impact based on simulated system security levels.
        """
        if system_health < 90:
            return random.randint(30, 120) # Major disruption
        return random.randint(0, 15)
