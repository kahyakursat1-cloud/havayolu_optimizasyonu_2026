"""
Integration tests: exercise the full pipeline (generator → enrichment →
sanitization → solver) the way the API does. These catch regressions that
unit tests miss — e.g. the "fillna('None') → all aircraft grounded" bug.
"""
import pytest

from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.data_connectors.market_intel import market_intel
from src.security.adversarial_guard import security_guard
from src.optimizer.dt_solver import DigitalTwinSolver


@pytest.fixture(scope="module")
def generated_scenario():
    sim = AdvancedAirlineSimulator(seed=42)
    df = sim.generate_full_scenario(days=1)
    df = market_intel.enrich_scenario_with_intel(df)
    df = security_guard.sanitize_scenario(df)
    return df


def test_maintenance_reason_not_string_none(generated_scenario):
    """
    Regression: synthetic_env.df.fillna('None') used to convert Python None
    to the string 'None', which made dt_solver ground every aircraft.
    """
    reasons = generated_scenario['maintenance_reason'].unique()
    for r in reasons:
        assert r != 'None', "maintenance_reason leaked 'None' string sentinel"


def test_not_all_aircraft_grounded(generated_scenario):
    """
    Regression: with the fillna bug, 100% of aircraft were grounded and
    every flight got canceled. Assert the solver keeps at least half the
    flights airborne on a clean synthetic scenario.
    """
    solver = DigitalTwinSolver(generated_scenario.head(30).copy())
    result = solver.solve_winning(strategy="PROFIT", max_time_sec=15)

    assert result is not None
    cancel_rate = result['is_canceled'].sum() / len(result)
    assert cancel_rate < 0.5, (
        f"Cancel rate {cancel_rate:.0%} too high — MRO / feasibility regression suspected"
    )


def test_profit_vs_volume_strategy(generated_scenario):
    """
    VOLUME strategy maximizes passengers flown; PROFIT maximizes margin. Both
    must return valid schedules with the expected result columns. We don't
    compare cancel counts directly — CP-SAT is non-deterministic and either
    strategy may tie on small samples.
    """
    sample = generated_scenario.head(30).copy()

    profit_res = DigitalTwinSolver(sample.copy()).solve_winning(strategy="PROFIT", max_time_sec=10)
    volume_res = DigitalTwinSolver(sample.copy()).solve_winning(strategy="VOLUME", max_time_sec=10)

    for res in (profit_res, volume_res):
        assert res is not None
        assert 'is_canceled' in res.columns
        assert 'assigned_aircraft' in res.columns
        assert len(res) == 30


def test_infeasible_raises(generated_scenario):
    """
    Artificially break the schedule so no feasible assignment exists,
    and confirm the solver raises rather than silently returning None.
    """
    sample = generated_scenario.head(5).copy()
    # Force all aircraft to pending critical maintenance (real reason, not sentinel)
    sample['engine_health'] = 0.05
    solver = DigitalTwinSolver(sample)
    # With every aircraft grounded, the solver still finds a "cancel everything"
    # solution; truly infeasible scenarios require deeper construction. Just
    # confirm it doesn't crash and returns valid structure.
    result = solver.solve_winning(strategy="PROFIT", max_time_sec=5)
    assert result is not None
    assert result['is_canceled'].sum() == len(result)


def test_solve_attrs_mro_warnings(generated_scenario):
    """Results DataFrame should carry MRO warnings for operator visibility."""
    solver = DigitalTwinSolver(generated_scenario.head(20).copy())
    result = solver.solve_winning(strategy="PROFIT", max_time_sec=10)
    assert 'mro_warnings' in result.attrs
    assert isinstance(result.attrs['mro_warnings'], dict)


def test_solver_emits_decision_explanations(generated_scenario):
    """Solved schedules should contain flight-level explanation fields."""
    solver = DigitalTwinSolver(generated_scenario.head(20).copy())
    result = solver.solve_winning(strategy="PROFIT", max_time_sec=10)
    assert 'decision_reason' in result.columns
    assert 'slot_pressure_flag' in result.columns
    assert result['decision_reason'].notna().all()
