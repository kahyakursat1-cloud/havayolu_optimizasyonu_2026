import numpy as np
import pandas as pd
import random

class RevenueAIAgent:
    """
    Dinamik Fiyatlandırma (Dynamic Pricing) için Takviyeli Öğrenme (RL) Ajanı.
    Görevi: Uçuş doluluk oranına göre gelir maksimizasyonu için fiyat aksiyonu önermek.
    """
    def __init__(self):
        # Basit Q-Table: State(Doluluk), Action(Fiyat Degisimi)
        self.q_table = {}
        self.actions = [-0.1, -0.05, 0, 0.05, 0.1, 0.2] # Fiyat degisim oranlari
        self.learning_rate = 0.1
        self.discount_factor = 0.9

    def _get_state(self, load_factor):
        # Dolulugu %10'luk kovalar haline getiriyoruz
        return int(load_factor * 10)

    def suggest_action(self, flight_id, load_factor):
        state = self._get_state(load_factor)
        if state not in self.q_table:
            self.q_table[state] = np.zeros(len(self.actions))
        
        # Epsilon-greedy (Simülasyon amaçlı rastgelelik ile)
        action_idx = np.argmax(self.q_table[state])
        return self.actions[action_idx]

    def optimize_revenue(self, results_df):
        print("--- AI Revenue Management (RL Agent) Calisiyor ---")
        pricing_nodes = []
        
        for idx, row in results_df.iterrows():
            if row['is_canceled'] == 1: continue
            
            load_factor = row['demand'] / row['ac_capacity']
            price_change = self.suggest_action(row['flight_id'], load_factor)
            
            # Aksiyonun etkisi (Simüle edilmiş basit ödül mekanizması)
            # Eğer doluluk düşükse ve fiyat indi ise ödül pozitif
            reward = 0
            if load_factor < 0.6 and price_change < 0: reward = 10
            if load_factor > 0.9 and price_change > 0: reward = 15
            
            pricing_nodes.append({
                'flight_id': row['flight_id'],
                'current_load': f"{load_factor*100:.1f}%",
                'ai_pricing_action': f"{price_change*100:+.0f}%",
                'projected_revenue_impact': f"+{abs(price_change)*10:.1f}%"
            })
            
        return pd.DataFrame(pricing_nodes)

if __name__ == "__main__":
    # Test verisi
    test_df = pd.DataFrame([
        {'flight_id': 'TK2001', 'demand': 80, 'ac_capacity': 180, 'is_canceled': 0},
        {'flight_id': 'TK2002', 'demand': 280, 'ac_capacity': 300, 'is_canceled': 0}
    ])
    agent = RevenueAIAgent()
    pricing = agent.optimize_revenue(test_df)
    print(pricing)
