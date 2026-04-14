import numpy as np
import pandas as pd

class SBMAuditor:
    """
    v25.0 Ecosystem Leader: Slack-Based Measure (SBM) 
    using Directional Distance Function (DDF).
    
    Objective: Maximize desirable outputs (pax) given undesirable inputs (fuel/CO2).
    """
    @staticmethod
    def calculate_efficiency_frontier(df):
        if df.empty: return df
        
        # v25.0 Direction: Maximize passengers for the same fuel
        # We simplify the frontier by grouping by aircraft category
        results = df.copy()
        
        for cat in df['ac_cat'].unique():
            cat_mask = df['ac_cat'] == cat
            cat_df = df[cat_mask]
            
            if cat_df.empty: continue
            
            # Theoretical Best (Frontier): Max Pax / Min Fuel
            # We use a benchmark ratio: Pax per 1000kg Fuel
            ratios = cat_df['passenger_count'] / (cat_df['fuel_cost_tl'] / 1000)
            frontier_ratio = ratios.max()
            
            # SBM Efficiency Score [0-1]
            results.loc[cat_mask, 'sbm_efficiency'] = ratios / frontier_ratio
            
            # Directional Distance: How many 'Slacks' to reach the frontier?
            results.loc[cat_mask, 'ddf_slack_pax'] = (frontier_ratio * (cat_df['fuel_cost_tl'] / 1000)) - cat_df['passenger_count']
            
        return results

sbm_auditor = SBMAuditor()
