import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("AviationSingularity.Security")

class AdversarialGuard:
    """
    v25.0 Robust Defense against Adversarial Perturbations.
    
    Implements:
    1. Z-Score outlier detection.
    2. Delta-Noise Filtering (Median-based smoothing).
    3. Operator Alerting.
    """
    def __init__(self, threshold=3.5):
        self.threshold = threshold
        self.noise_meta = {"detected": False, "intensity": 0.0}

    def validate_tactical_data(self, df):
        """
        Scans for malicious data injections (e.g., fake delays).
        v25.0: Automatically filters noise and informs operator.
        """
        if df.empty or 'assigned_delay' not in df.columns:
            return {"is_safe": True, "noise": self.noise_meta}

        delays = df['assigned_delay'].astype(float)
        mean = delays.mean()
        std = delays.std()
        
        if std == 0: return {"is_safe": True, "noise": self.noise_meta}
        
        z_scores = (delays - mean).abs() / std
        anomalies = z_scores > self.threshold
        
        noise_level = anomalies.sum() / len(df)
        if noise_level > 0.02:
            self.noise_meta = {"detected": True, "intensity": noise_level}
            logger.warning(f"🚨 ADVERSARIAL NOISE DETECTED: {noise_level:.1%}")
            return {"is_safe": False, "noise": self.noise_meta}
            
        return {"is_safe": True, "noise": self.noise_meta}

    def sanitize_scenario(self, df):
        """
        Automatically cleans the scenario using robust smoothing (Median Filtering).
        """
        clean_df = df.copy()
        
        # v25.0: Automatic Noise Removal
        # Replace outliers with the rolling median (denoising)
        if 'assigned_delay' in clean_df.columns:
            median_val = clean_df['assigned_delay'].median()
            delays = clean_df['assigned_delay'].astype(float)
            z_scores = (delays - delays.mean()).abs() / (delays.std() + 1e-6)
            
            # Reset extreme noise to median
            clean_df.loc[z_scores > self.threshold, 'assigned_delay'] = int(median_val)
            
        return clean_df

security_guard = AdversarialGuard()
