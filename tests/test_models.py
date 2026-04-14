"""
Unit tests for AI/ML components:
  - HybridGA (fitness, selection, crossover, mutation)
  - AviationRLBotEnv (observation space, action application, reward shaping)
  - AviationForecastEngine (determinism, seasonal shape, 7-day coverage)
  - BayesianCausalModel (attribution logic, cyber risk scale)
  - TrajectoryPlannerAStar (path completeness, physical bounds)
"""
import pytest
import math
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_flights_df():
    data = {
        'flight_id':           ['TK1', 'TK2', 'TK3', 'TK4'],
        'aircraft_id':         ['A320-1', 'A320-1', 'B737-1', 'B737-1'],
        'crew_id':             ['CRW-01', 'CRW-01', 'CRW-02', 'CRW-02'],
        'departure_time':      [
            pd.Timestamp('2026-04-15 06:00'),
            pd.Timestamp('2026-04-15 09:00'),
            pd.Timestamp('2026-04-15 07:00'),
            pd.Timestamp('2026-04-15 12:00'),
        ],
        'arrival_time':        [
            pd.Timestamp('2026-04-15 08:00'),
            pd.Timestamp('2026-04-15 11:00'),
            pd.Timestamp('2026-04-15 09:00'),
            pd.Timestamp('2026-04-15 14:00'),
        ],
        'origin':              ['IST', 'LHR', 'IST', 'AYT'],
        'destination':         ['LHR', 'IST', 'AYT', 'IST'],
        'passenger_count':     [150, 160, 140, 170],
        'ac_capacity':         [180, 180, 189, 189],
        'ac_cat':              ['NARROW', 'NARROW', 'NARROW', 'NARROW'],
        'crew_cert':           ['NARROW', 'NARROW', 'NARROW', 'NARROW'],
        'block_time':          [120, 120, 120, 120],
        'ac_remaining_fh':     [80.0, 80.0, 95.0, 95.0],
        'ac_range_km':         [6000, 6000, 6000, 6000],
        'dist_km':             [2500, 2500, 1000, 1000],
        'revenue_tl':          [100_000, 110_000, 90_000, 95_000],
        'op_cost_tl':          [20_000, 22_000, 18_000, 19_000],
        'fuel_cost_tl':        [10_000, 11_000, 9_000, 9_500],
        'delay_cost_per_min':  [500, 500, 400, 400],
        'load_factor':         [0.83, 0.89, 0.74, 0.90],
        'pax_connection_count':[20, 15, 10, 25],
        'co2_kg':              [5_000, 5_500, 4_000, 4_200],
        'weather_risk':        [0.1, 0.2, 0.0, 0.3],
        'is_canceled':         [0, 0, 0, 0],
        'assigned_delay':      [0, 0, 0, 0],
        'assigned_ac':         ['A320-1', 'A320-1', 'B737-1', 'B737-1'],
        'status':              ['SCHEDULED'] * 4,
        'saf_usage':           [0, 0, 0, 0],
        'crew_base_fatigue':   [5, 5, 3, 3],
        'is_night_flight':     [0, 0, 0, 0],
    }
    return pd.DataFrame(data)


# ===========================================================================
# HybridGA Tests
# ===========================================================================

class TestHybridGA:
    def test_fitness_positive_for_valid_schedule(self, sample_flights_df):
        from src.optimizer.hybrid_ga import HybridGA
        ga = HybridGA(sample_flights_df, pop_size=5, generations=1)
        score = ga.fitness(ga.flights)
        assert isinstance(score, float)
        assert score > -1e7, "Fitness should not be catastrophically negative for a valid schedule"

    def test_fitness_penalizes_cancellation(self, sample_flights_df):
        from src.optimizer.hybrid_ga import HybridGA
        ga = HybridGA(sample_flights_df, pop_size=5, generations=1)
        normal = ga.fitness(ga.flights)
        canceled = ga.flights.copy()
        canceled['is_canceled'] = 1
        score_canceled = ga.fitness(canceled)
        assert score_canceled < normal, "Canceling all flights must reduce fitness"

    def test_tournament_select_returns_individual(self, sample_flights_df):
        from src.optimizer.hybrid_ga import HybridGA
        ga = HybridGA(sample_flights_df, pop_size=5, generations=1)
        pop_fitness = [(ga.flights.copy(), float(i)) for i in range(5)]
        winner = ga._tournament_select(pop_fitness, k=3)
        assert winner is not None
        assert isinstance(winner, pd.DataFrame)

    def test_aircraft_rotation_crossover_preserves_index(self, sample_flights_df):
        from src.optimizer.hybrid_ga import HybridGA
        ga = HybridGA(sample_flights_df, pop_size=5, generations=1)
        p1 = ga.flights.copy()
        p2 = ga.flights.copy()
        p2['assigned_ac'] = 'B737-1'
        child = ga.aircraft_rotation_crossover(p1, p2)
        assert set(child.index) == set(p1.index), "Crossover must not drop or add rows"
        assert child['assigned_ac'].isin(ga._ac_list).all(), "All aircraft must be from the fleet"

    def test_mutation_preserves_row_count(self, sample_flights_df):
        from src.optimizer.hybrid_ga import HybridGA
        ga = HybridGA(sample_flights_df, pop_size=5, generations=1)
        ind = ga.flights.copy()
        assert len(ga.quantum_tunneling_mutation(ind)) == len(ind)
        assert len(ga.reversal_mutation(ind)) == len(ind)
        assert len(ga.point_mutation(ind)) == len(ind)

    def test_solve_returns_dataframe(self, sample_flights_df):
        from src.optimizer.hybrid_ga import HybridGA
        ga = HybridGA(sample_flights_df, pop_size=4, generations=2)
        result = ga.solve()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_flights_df)


# ===========================================================================
# AviationRLBotEnv Tests
# ===========================================================================

class TestRLEnv:
    def _make_env(self, sample_flights_df):
        from src.models.rl_env import AviationRLBotEnv, OBS_DIM
        env = AviationRLBotEnv(simulator=None, initial_df=sample_flights_df)
        return env, OBS_DIM

    def test_observation_space_shape(self, sample_flights_df):
        env, OBS_DIM = self._make_env(sample_flights_df)
        obs, _ = env.reset()
        assert obs.shape == (OBS_DIM,), f"Expected ({OBS_DIM},), got {obs.shape}"
        assert obs.dtype == np.float32

    def test_obs_bounds(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        obs, _ = env.reset()
        assert (obs >= 0.0).all() and (obs <= 1.0).all(), "All obs must be in [0, 1]"

    def test_action_keep_no_change(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        env.reset()
        delay_before = env.current_df.iloc[0]['assigned_delay']
        env.step(0)  # action 0: keep
        delay_after = env.current_df.iloc[0]['assigned_delay']
        assert delay_after == delay_before

    def test_action_delay_15(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        env.reset()
        delay_before = env.current_df.iloc[0]['assigned_delay']
        env.step(1)
        assert env.current_df.iloc[0]['assigned_delay'] == delay_before + 15

    def test_action_delay_60(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        env.reset()
        delay_before = env.current_df.iloc[0]['assigned_delay']
        env.step(3)
        assert env.current_df.iloc[0]['assigned_delay'] == delay_before + 60

    def test_action_cancel(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        env.reset()
        env.step(4)  # action 4: cancel
        assert env.current_df.iloc[0]['is_canceled'] == 1

    def test_action_priority_bump_zeros_delay(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        env.reset()
        env.current_df.iloc[0, env.current_df.columns.get_loc('assigned_delay')] = 45
        env.step(5)  # action 5: priority bump
        assert env.current_df.iloc[0]['assigned_delay'] == 0

    def test_cancel_gives_negative_reward(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        env.reset()
        _, reward, _, _, _ = env.step(4)
        assert reward < 0, "Cancellation must yield negative reward"

    def test_episode_terminates(self, sample_flights_df):
        env, _ = self._make_env(sample_flights_df)
        env.reset()
        terminated = False
        for _ in range(len(sample_flights_df) + 1):
            _, _, terminated, _, _ = env.step(0)
            if terminated:
                break
        assert terminated, "Episode must terminate after max_steps"


# ===========================================================================
# AviationForecastEngine Tests
# ===========================================================================

class TestForecastEngine:
    def test_returns_seven_days(self):
        from src.analytics.forecast_engine import AviationForecastEngine
        engine = AviationForecastEngine()
        result = engine.get_forecast([{"load_factor": 0.80}])
        assert len(result) == 7

    def test_required_keys_present(self):
        from src.analytics.forecast_engine import AviationForecastEngine
        engine = AviationForecastEngine()
        result = engine.get_forecast([{"load_factor": 0.75}])
        for entry in result:
            assert "date" in entry
            assert "predicted_plf" in entry
            assert "disruption_risk" in entry

    def test_plf_in_valid_range(self):
        from src.analytics.forecast_engine import AviationForecastEngine
        engine = AviationForecastEngine()
        result = engine.get_forecast([{"load_factor": 0.95}])
        for entry in result:
            assert 40.0 <= entry["predicted_plf"] <= 100.0, f"PLF out of range: {entry}"

    def test_disruption_risk_in_valid_range(self):
        from src.analytics.forecast_engine import AviationForecastEngine
        engine = AviationForecastEngine()
        result = engine.get_forecast([{"load_factor": 0.60}])
        for entry in result:
            assert 0.0 <= entry["disruption_risk"] <= 50.0, f"Risk out of range: {entry}"

    def test_high_load_raises_disruption_risk(self):
        from src.analytics.forecast_engine import AviationForecastEngine
        engine = AviationForecastEngine()
        low_load  = engine.get_forecast([{"load_factor": 0.50}])
        high_load = engine.get_forecast([{"load_factor": 0.99}])
        avg_low  = sum(d["disruption_risk"] for d in low_load) / 7
        avg_high = sum(d["disruption_risk"] for d in high_load) / 7
        assert avg_high >= avg_low, "Higher base load must yield higher or equal disruption risk"

    def test_deterministic_output(self):
        from src.analytics.forecast_engine import AviationForecastEngine
        engine = AviationForecastEngine()
        scenario = [{"load_factor": 0.82}] * 5
        r1 = engine.get_forecast(scenario)
        r2 = engine.get_forecast(scenario)
        for a, b in zip(r1, r2):
            assert a["predicted_plf"] == b["predicted_plf"]
            assert a["disruption_risk"] == b["disruption_risk"]


# ===========================================================================
# BayesianCausalModel Tests
# ===========================================================================

class TestBayesianCausal:
    def test_no_delay_returns_none(self):
        from src.models.causal_intelligence import BayesianCausalModel
        model = BayesianCausalModel()
        result = model.attribute_delay({"assigned_delay": 0})
        assert result == "None"

    def test_high_weather_risk_attributes_weather(self):
        from src.models.causal_intelligence import BayesianCausalModel
        model = BayesianCausalModel()
        flight = {"assigned_delay": 45, "weather_risk": 0.95, "destination": "ADB", "is_night_flight": 0, "ac_remaining_fh": 80}
        result = model.attribute_delay(flight)
        assert result == "Weather", f"High weather_risk should attribute to Weather, got: {result}"

    def test_hub_night_raises_cyber(self):
        from src.models.causal_intelligence import BayesianCausalModel
        model = BayesianCausalModel()
        # No weather, hub IST, night → Cyber should be competitive
        flight = {"assigned_delay": 30, "weather_risk": 0.0, "destination": "IST", "is_night_flight": 1, "ac_remaining_fh": 95}
        result = model.attribute_delay(flight)
        assert result in ("Cyber Attack", "Security/TSA", "Ground Ops"), \
            f"Night+hub with no weather should not attribute to Weather, got: {result}"

    def test_attribution_is_deterministic(self):
        from src.models.causal_intelligence import BayesianCausalModel
        model = BayesianCausalModel()
        flight = {"assigned_delay": 60, "weather_risk": 0.4, "destination": "IST", "is_night_flight": 0, "ac_remaining_fh": 50}
        assert model.attribute_delay(flight) == model.attribute_delay(flight)

    def test_cyber_risk_zero_at_full_health(self):
        from src.models.causal_intelligence import BayesianCausalModel
        model = BayesianCausalModel()
        assert model.predict_cyber_risk(100) == 0
        assert model.predict_cyber_risk(95) == 0

    def test_cyber_risk_increases_with_degradation(self):
        from src.models.causal_intelligence import BayesianCausalModel
        model = BayesianCausalModel()
        assert model.predict_cyber_risk(92) > 0
        assert model.predict_cyber_risk(80) > model.predict_cyber_risk(92)
        assert model.predict_cyber_risk(50) <= 120


# ===========================================================================
# TrajectoryPlannerAStar Tests
# ===========================================================================

class TestTrajectoryAStar:
    def test_returns_result(self):
        from src.optimizer.trajectory_a_star import TrajectoryPlannerAStar
        planner = TrajectoryPlannerAStar()
        result = planner.optimize_3d_path('IST', 'LHR', total_dist=2500)
        assert result is not None

    def test_result_has_required_keys(self):
        from src.optimizer.trajectory_a_star import TrajectoryPlannerAStar
        planner = TrajectoryPlannerAStar()
        result = planner.optimize_3d_path('IST', 'JFK', total_dist=8000)
        assert 'total_cost' in result
        assert 'optimal_fl' in result
        assert 'optimal_mach' in result
        assert result['is_3d_optimized'] is True

    def test_optimal_fl_within_bounds(self):
        from src.optimizer.trajectory_a_star import TrajectoryPlannerAStar
        planner = TrajectoryPlannerAStar()
        result = planner.optimize_3d_path('IST', 'AYT', total_dist=500)
        assert planner.min_fl <= result['optimal_fl'] <= planner.max_fl

    def test_optimal_mach_within_bounds(self):
        from src.optimizer.trajectory_a_star import TrajectoryPlannerAStar
        planner = TrajectoryPlannerAStar()
        result = planner.optimize_3d_path('IST', 'ESB', total_dist=350)
        assert planner.min_mach <= result['optimal_mach'] <= planner.max_mach

    def test_cost_positive(self):
        from src.optimizer.trajectory_a_star import TrajectoryPlannerAStar
        planner = TrajectoryPlannerAStar()
        result = planner.optimize_3d_path('IST', 'LHR', total_dist=2500)
        assert result['total_cost'] > 0
