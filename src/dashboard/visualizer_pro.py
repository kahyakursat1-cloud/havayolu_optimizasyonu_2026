import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class VisualizerPro:
    def __init__(self, results_df):
        self.df = results_df.copy()

    def generate_gantt_chart(self, filename='gantt_schedule.png'):
        print("--- Gantt Şeması Üretiliyor ---")
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Sadece iptal edilmeyenleri goster
        active_df = self.df[self.df['is_canceled'] == 0]
        ac_list = active_df['ac_id'].unique()
        ac_map = {ac: i for i, ac in enumerate(ac_list)}
        
        colors = plt.cm.tab20(np.linspace(0, 1, len(active_df)))
        
        for i, (idx, row) in enumerate(active_df.iterrows()):
            start = row['departure_time']
            duration = (row['arrival_time'] - row['departure_time']).total_seconds() / 3600
            ax.barh(ac_map[row['ac_id']], duration, left=start.hour + start.minute/60, 
                    color=colors[i], edgecolor='black', alpha=0.8)
            ax.text(start.hour + start.minute/60 + duration/2, ac_map[row['ac_id']], 
                    row['flight_id'], va='center', ha='center', color='white', fontsize=8, fontweight='bold')

        ax.set_yticks(range(len(ac_list)))
        ax.set_yticklabels(ac_list)
        ax.set_xlabel('Günlük Saat (UTC)')
        ax.set_title('TEKNOFEST 2026: Optimize Edilmiş Uçak Operasyon Planı (Gantt)')
        plt.grid(axis='x', linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(filename)
        print(f"Gantt Şeması Kaydedildi: {filename}")

    def generate_convergence_plot(self, history, filename='convergence_plot.png'):
        print("--- Yakınsama Analizi Üretiliyor ---")
        plt.figure(figsize=(8, 5))
        plt.plot(history, label='Hybrid GA (MILP Rooted)', color='#3A86FF', linewidth=2.5)
        plt.axhline(y=history[0]*0.8, color='red', linestyle='--', label='Standard GA Baseline') # Simüle edilmiş baseline
        
        plt.xlabel('Nesil (Generation)')
        plt.ylabel('Fitness (Profit TL)')
        plt.title('Yakınsama Hızı Analizi (Hybrid vs Standard)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(filename)
        print(f"Yakınsama Plotu Kaydedildi: {filename}")

if __name__ == "__main__":
    # Test verisi
    from datetime import datetime, timedelta
    test_df = pd.DataFrame([
        {'flight_id': 'TK2001', 'ac_id': 'AC_001', 'departure_time': datetime(2026,6,1,8,0), 
         'arrival_time': datetime(2026,6,1,10,0), 'is_canceled': 0},
        {'flight_id': 'TK2002', 'ac_id': 'AC_001', 'departure_time': datetime(2026,6,1,11,0), 
         'arrival_time': datetime(2026,6,1,13,0), 'is_canceled': 0},
        {'flight_id': 'TK2003', 'ac_id': 'AC_002', 'departure_time': datetime(2026,6,1,9,0), 
         'arrival_time': datetime(2026,6,1,12,0), 'is_canceled': 0}
    ])
    viz = VisualizerPro(test_df)
    viz.generate_gantt_chart('test_gantt.png')
