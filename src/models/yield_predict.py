import numpy as np
import pandas as pd

class YieldPredictor:
    """
    🚀 v9.0 Yield Management: Mock XGBoost/Random Forest logic to predict 
    demand and compute optimal pricing strategies.
    """
    def __init__(self):
        # Model coefficients (simulating trained weights)
        self.price_elasticity = -1.2 # % change in demand for 1% change in price
        self.business_loyalty = 0.8  # Business segment is less price-sensitive
        
    def predict_demand(self, base_demand, current_price, reference_price):
        """
        Simulates ML prediction based on price deviation.
        """
        price_ratio = current_price / reference_price
        # Demand = Base * (Ratio ^ Elasticity)
        predicted = base_demand * (price_ratio ** self.price_elasticity)
        return int(max(0, predicted))

    def calculate_optimal_price(self, flight_row):
        """
        Calculates the revenue-maximizing price point.
        """
        # Logic: High load factor -> Increase price. Hub destination -> Premium.
        base_price = 1000
        if flight_row['destination'] == 'IST': base_price *= 1.3
        
        # Simple optimization loop (simulating ML decision surface)
        best_price = base_price
        max_rev = 0
        for p in range(int(base_price*0.5), int(base_price*2.0), 50):
            pax = self.predict_demand(flight_row['passenger_count'], p, base_price)
            rev = pax * p
            if rev > max_rev:
                max_rev = rev
                best_price = p
        return best_price
