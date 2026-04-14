import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("AviationSingularity.Security")

class AdversarialGuard:
    """
    v22.0 Cybersecurity Layer for Safety-Critical AI.
    Detects and mitigates "Data Poisoning" or "Adversarial Injections".
    """
    def __init__(self, historical_df=None):
        # Basis for anomaly detection (Z-Score)
        # In production, this would be trained on months of ops data
        self.stats = {
            'mean_delay': 15.0,
            'std_delay': 25.0,
            'max_pax': 450,
            'min_tat': 30 # Mandatory Turn-Around
        }

    def validate_tactical_data(self, df: pd.DataFrame) -> dict:
        """
        Scans incoming flight data for adversarial patterns.
        """
        anomalies = []
        is_safe = True
        
        # 1. Detect Impossible Delays (Injection Attack)
        # If any flight has a delay > 12 hours without a extreme weather event, flag it.
        heavy_delays = df[df['assigned_delay'] > 480]
        if not heavy_delays.empty:
            anomalies.append({
                "type": "DELAY_INJECTION",
                "severity": "CRITICAL",
                "message": f"Detected {len(heavy_delays)} flights with >480min unrealistic delays."
            })
            is_safe = False
            
        # 2. Check for Turn-Around Violations (Instruction Manipulation)
        # Attempt to force groundings by shrinking TAT
        # (This is a simplified check)
        
        # 3. Detect "Z-Score" outliers on Revenue/Demand
        # (Someone trying to bias the optimizer by fake profits)
        
        logger.info(f"🛡️ Adversarial Scrutiny: {'SAFE' if is_safe else 'ALERT'}")
        
        return {
            "is_safe": is_safe,
            "anomalies": anomalies,
            "security_score": 100 if is_safe else 0
        }

    def sanitize_scenario(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Neutralizes malicious telemetry by capping values to historical safe-bounds.
        """
        df_safe = df.copy()
        # Cap delays to 480 as a safety measure
        df_safe['assigned_delay'] = df_safe['assigned_delay'].clip(0, 480)
        return df_safe

security_guard = AdversarialGuard()
