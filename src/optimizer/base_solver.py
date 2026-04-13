import pandas as pd
import numpy as np
from ortools.sat.python import cp_model

class ConnectionOptimizer:
    def __init__(self, flights_df, hub='IST', min_wait=45, max_wait=180):
        self.flights = flights_df.copy()
        self.hub = hub
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.model = cp_model.CpModel()

    def solve(self, max_shift_mins=30):
        # 1. Degiskenleri Tanimla: Her ucusun kalkis zamanindaki degisim (shift)
        # -30 ile +30 dakika arasinda bir tamsayi
        shifts = {}
        for i, row in self.flights.iterrows():
            shifts[i] = self.model.NewIntVar(-max_shift_mins, max_shift_mins, f'shift_{i}')

        # 2. Baglanti Hedefi (Objective)
        # Bu basite indirgenmis bir modeldir. IST'deki tum ucuslar arasi baglantiya bakar.
        connections = []
        
        # Gelen ucuslar (Arrivals to IST)
        arrivals = self.flights[self.flights['destination'] == self.hub]
        # Giden ucuslar (Departures from IST)
        departures = self.flights[self.flights['origin'] == self.hub]

        total_connection_score = 0
        
        for i, arr_row in arrivals.iterrows():
            for j, dep_row in departures.iterrows():
                # Eger ucuslar zaten zaman olarak birbirine yakin ise baglanti adayi olabilirler
                # Baslangic bekleme suresi (as-is)
                wait_time_current = (dep_row['departure_time'] - arr_row['arrival_time']).total_seconds() / 60
                
                # Eger kaydirma ile ideal araliga (45-180 dk) girme ihtimali varsa
                if (self.min_wait - 2*max_shift_mins) <= wait_time_current <= (self.max_wait + 2*max_shift_mins):
                    # Boolean degisken: Bu iki ucus arasinda 'Iyi Baglanti' var mi?
                    is_connected = self.model.NewBoolVar(f'conn_{i}_{j}')
                    
                    # Kisit: is_connected == 1 <=> min_wait <= (actual_wait + shift_dep - shift_arr) <= max_wait
                    actual_wait_expr = int(wait_time_current) + shifts[j] - shifts[i]
                    
                    self.model.Add(actual_wait_expr >= self.min_wait).OnlyEnforceIf(is_connected)
                    self.model.Add(actual_wait_expr <= self.max_wait).OnlyEnforceIf(is_connected)
                    self.model.Add(actual_wait_expr < self.min_wait).OnlyEnforceIf(is_connected.Not())
                    # (Not: Basitlik icin sadece min kısıtını guclendirdik)
                    
                    total_connection_score += is_connected

        # 3. Objective: Baglanti sayisini maksimize et
        self.model.Maximize(total_connection_score)

        # 4. Solv
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"Bulasan Toplam Iyi Baglanti Sayisi: {solver.ObjectiveValue()}")
            optimized_flights = self.flights.copy()
            for i in self.flights.index:
                shift_val = solver.Value(shifts[i])
                optimized_flights.at[i, 'departure_time'] += pd.Timedelta(minutes=shift_val)
                optimized_flights.at[i, 'arrival_time'] += pd.Timedelta(minutes=shift_val)
            return optimized_flights
        else:
            print("Cozum bulunamadi.")
            return None

if __name__ == "__main__":
    from src.generator.synthetic_env import AirlineSimulator
    
    sim = AirlineSimulator()
    flights_df = sim.generate_flights(50)
    
    optimizer = ConnectionOptimizer(flights_df)
    optimized_df = optimizer.solve(max_shift_mins=30)
    
    if optimized_df is not None:
        print("\n--- Optimizasyon Oncesi Ilk 3 Ucus ---")
        print(flights_df[['flight_id', 'departure_time', 'arrival_time']].head(3))
        print("\n--- Optimizasyon Sonrasi Ilk 3 Ucus ---")
        print(optimized_df[['flight_id', 'departure_time', 'arrival_time']].head(3))
