import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset
except Exception:  # pragma: no cover - optional runtime guard
    torch = None
    nn = None
    DataLoader = None
    TensorDataset = None


FEATURE_COLUMNS = [
    "weather_risk",
    "tech_failure_prob",
    "load_factor",
    "passenger_count",
    "pax_connection_count",
    "block_time",
    "dist_km",
    "delay_cost_per_min",
    "market_qsi_weight",
    "engine_health",
    "is_night_flight",
]


@dataclass
class _SequenceSplit:
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray


class _LSTMDelayClassifier(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 16):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(hidden_size, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
        )

    def forward(self, x):
        output, _ = self.lstm(x)
        return self.head(output[:, -1, :]).squeeze(-1)


class ModelBenchmarker:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def _derive_target(self, df: pd.DataFrame) -> pd.Series:
        origin_factor = df["origin"].map({
            "IST": 1.2, "LHR": 1.15, "JFK": 1.1, "AYT": 1.0, "ADB": 0.95, "ESB": 0.9
        }).fillna(1.0)
        destination_factor = df["destination"].map({
            "IST": 1.15, "LHR": 1.1, "JFK": 1.1, "AYT": 1.0, "ADB": 0.95, "ESB": 0.9
        }).fillna(1.0)
        conn_scaled = df["pax_connection_count"].fillna(0) / max(df["pax_connection_count"].max(), 1)
        pax_scaled = df["passenger_count"].fillna(0) / max(df["passenger_count"].max(), 1)
        block_scaled = df["block_time"].fillna(0) / max(df["block_time"].max(), 1)
        inverse_health = 1.0 - df["engine_health"].fillna(1.0).clip(0.0, 1.0)

        risk_score = (
            df["weather_risk"].fillna(0) * 2.4
            + df["tech_failure_prob"].fillna(0) * 4.0
            + df["load_factor"].fillna(0) * 0.6
            + conn_scaled * 0.45
            + pax_scaled * 0.25
            + block_scaled * 0.2
            + inverse_health * 0.9
            + df["is_night_flight"].fillna(0) * 0.15
            + (origin_factor - 1.0) * 0.4
            + (destination_factor - 1.0) * 0.3
        )
        threshold = float(risk_score.quantile(0.6))
        return (risk_score >= threshold).astype(int)

    def _prepare_frame(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        frame = df.copy()
        for col in FEATURE_COLUMNS:
            if col not in frame.columns:
                frame[col] = 0.0
        frame = frame.sort_values("departure_time").reset_index(drop=True)
        X = frame[FEATURE_COLUMNS].fillna(0.0).astype(float)
        y = self._derive_target(frame)
        return X, y

    def _score_predictions(self, y_true, y_pred, y_proba) -> dict:
        metrics = {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        }
        try:
            metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_proba)), 4)
        except Exception:
            metrics["roc_auc"] = None
        return metrics

    def _benchmark_logistic_regression(self, X_train, X_test, y_train, y_test) -> dict:
        started = time.perf_counter()
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=self.random_state)),
        ])
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        return {
            "name": "LogisticRegression",
            "status": "ok",
            "train_seconds": round(time.perf_counter() - started, 4),
            **self._score_predictions(y_test, y_pred, y_proba),
        }

    def _benchmark_xgboost(self, X_train, X_test, y_train, y_test) -> dict:
        started = time.perf_counter()
        model = XGBClassifier(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=self.random_state,
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        return {
            "name": "XGBoost",
            "status": "ok",
            "train_seconds": round(time.perf_counter() - started, 4),
            **self._score_predictions(y_test, y_pred, y_proba),
        }

    def _build_sequence_split(self, X: pd.DataFrame, y: pd.Series, sequence_length: int = 5) -> _SequenceSplit | None:
        if len(X) <= sequence_length + 10:
            return None

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        sequences = []
        labels = []
        for idx in range(sequence_length, len(X_scaled)):
            sequences.append(X_scaled[idx - sequence_length:idx])
            labels.append(int(y.iloc[idx]))

        X_seq = np.asarray(sequences, dtype=np.float32)
        y_seq = np.asarray(labels, dtype=np.float32)
        split_index = max(int(len(X_seq) * 0.8), 1)
        if split_index >= len(X_seq):
            split_index = len(X_seq) - 1
        return _SequenceSplit(
            X_train=X_seq[:split_index],
            y_train=y_seq[:split_index],
            X_test=X_seq[split_index:],
            y_test=y_seq[split_index:],
        )

    def _benchmark_lstm(self, X: pd.DataFrame, y: pd.Series) -> dict:
        if torch is None:
            return {"name": "LSTM", "status": "skipped", "reason": "torch unavailable"}

        sequence_split = self._build_sequence_split(X, y)
        if sequence_split is None:
            return {"name": "LSTM", "status": "skipped", "reason": "insufficient sequence data"}

        started = time.perf_counter()
        torch.manual_seed(self.random_state)
        model = _LSTMDelayClassifier(input_size=sequence_split.X_train.shape[-1])
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        criterion = nn.BCEWithLogitsLoss()

        train_ds = TensorDataset(
            torch.tensor(sequence_split.X_train),
            torch.tensor(sequence_split.y_train),
        )
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)

        model.train()
        for _ in range(6):
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                logits = model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()

        model.eval()
        with torch.no_grad():
            logits = model(torch.tensor(sequence_split.X_test))
            probs = torch.sigmoid(logits).cpu().numpy()
            preds = (probs >= 0.5).astype(int)

        return {
            "name": "LSTM",
            "status": "ok",
            "train_seconds": round(time.perf_counter() - started, 4),
            **self._score_predictions(sequence_split.y_test, preds, probs),
        }

    def benchmark_models(self, flights_df: pd.DataFrame) -> dict:
        X, y = self._prepare_frame(flights_df)
        n_classes = int(y.nunique())
        test_size = 0.25
        if len(X) < 8:
            test_size = 0.5

        use_stratify = None
        min_class_count = int(y.value_counts().min()) if n_classes > 1 else 0
        estimated_test_rows = max(int(round(len(X) * test_size)), 1)
        if n_classes > 1 and min_class_count >= 2 and estimated_test_rows >= n_classes:
            use_stratify = y

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=use_stratify
        )

        results = [
            self._benchmark_logistic_regression(X_train, X_test, y_train, y_test),
            self._benchmark_xgboost(X_train, X_test, y_train, y_test),
            self._benchmark_lstm(X, y),
        ]
        successful = [item for item in results if item.get("status") == "ok"]
        best_model = max(successful, key=lambda item: item["f1"])["name"] if successful else None
        return {
            "dataset": {
                "rows": int(len(X)),
                "features": FEATURE_COLUMNS,
                "positive_rate": round(float(y.mean()), 4),
                "train_rows": int(len(X_train)),
                "test_rows": int(len(X_test)),
            },
            "models": results,
            "best_model": best_model,
        }


model_benchmarker = ModelBenchmarker()
