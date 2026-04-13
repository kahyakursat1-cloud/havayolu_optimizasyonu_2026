import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error
import shap
import matplotlib.pyplot as plt
import os

# Simulatoru import et
from src.generator.synthetic_env import AdvancedAirlineSimulator

def run_benchmark():
    print("--- AI Model Benchmarking Basliyor ---")
    sim = AdvancedAirlineSimulator()
    df = sim.generate_full_scenario(days=30) # 1 Alylik veri ile egitim
    
    # Feature Engineering (Derece odakli: Zaman ve Lokasyon pikselleri)
    df['hour'] = df['departure_time'].dt.hour
    df['day_of_week'] = df['departure_time'].dt.dayofweek
    
    # Kategorik verileri Encode et (Basit version)
    df = pd.get_dummies(df, columns=['origin', 'destination'], drop_first=True)
    
    X = df.drop(['flight_id', 'departure_time', 'arrival_time', 'aircraft_id', 
                 'crew_id', 'is_delayed', 'delay_risk', 'actual_delay'], axis=1)
    y = df['delay_risk'] # Hedefimiz risk skoru
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    results = {}
    
    # 1. Linear Regression (Baseline)
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    results['LinearRegression'] = mean_absolute_error(y_test, lr_preds)
    
    # 2. XGBoost (The Winner)
    xgb = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
    xgb.fit(X_train, y_train)
    xgb_preds = xgb.predict(X_test)
    results['XGBoost'] = mean_absolute_error(y_test, xgb_preds)
    
    print("\n--- Model Karsilastirma (MAE - Ortalama Mutlak Hata) ---")
    for model, score in results.items():
        print(f"{model}: {score:.4f}")
        
    # SHAP Explainability (XAI)
    print("\n--- SHAP Aciklanabilirlik Analizi ---")
    explainer = shap.Explainer(xgb)
    shap_values = explainer(X_test)
    
    # SHAP özetini bir resim olarak kaydet (Sunumda kullanmak icin)
    plt.figure()
    shap.summary_plot(shap_values, X_test, show=False)
    plt.savefig('shap_summary.png')
    print("SHAP ozeti 'shap_summary.png' olarak kaydedildi.")
    
    return xgb

if __name__ == "__main__":
    run_benchmark()
