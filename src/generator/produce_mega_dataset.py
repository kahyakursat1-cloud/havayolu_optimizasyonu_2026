import pandas as pd
import sys
import os
from datetime import datetime

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.generator.synthetic_env import AdvancedAirlineSimulator

def produce_mega_benchmark(days=15, output_path="data/benchmark_10k_flights.csv"):
    print(f"--- Mega Dataset Üretimi Başlatıldı: {days} Günlük Senaryo ---")
    
    sim = AdvancedAirlineSimulator(seed=1903) # Unique seed for benchmark
    
    # Increase the daily flight count for stress testing
    mega_days = 90 # 3 months of data
    df = sim.generate_full_scenario(days=mega_days)
    
    print(f"✅ Üretim Tamamlandı!")
    print(f"📊 Toplam Uçuş Sayısı: {len(df)}")
    print(f"🏗️ Sütun Sayısı: {len(df.columns)}")
    
    # Final check for columns
    required_cols = ['flight_id', 'origin', 'destination', 'departure_time', 'arrival_time', 'block_time', 'ac_id']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ HATA: Eksik sütun tespit edildi: {col}")
            return
            
    df.to_csv(output_path, index=False)
    print(f"💾 Veri seti başarıyla mühürlendi: {output_path}")
    print(f"--- Üretim Hattı Durduruldu ---")

if __name__ == "__main__":
    produce_mega_benchmark()
