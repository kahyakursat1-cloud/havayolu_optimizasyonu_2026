import pytest
import pandas as pd
from src.optimizer.dt_solver import DigitalTwinSolver, SolverError

@pytest.fixture
def mock_flights():
    data = {
        'flight_id': ['TK100', 'TK200'],
        'aircraft_id': ['A320-1', 'B737-1'],
        'crew_id': ['CRW-01', 'CRW-02'],
        'departure_time': [pd.Timestamp('2026-04-14 10:00:00'), pd.Timestamp('2026-04-14 14:00:00')],
        'arrival_time': [pd.Timestamp('2026-04-14 12:00:00'), pd.Timestamp('2026-04-14 16:00:00')],
        'origin': ['IST', 'LHR'],
        'destination': ['LHR', 'JFK'],
        'origin_lat': [41.275, 51.470],
        'origin_lon': [28.751, -0.454],
        'dest_lat': [51.470, 40.641],
        'dest_lon': [-0.454, -73.778],
        'passenger_count': [150, 180],
        'ac_capacity': [180, 189],
        'ac_cat': ['NARROW', 'NARROW'],
        'ac_type': ['A320', 'B737'],
        'crew_cert': ['NARROW', 'NARROW'],
        'block_time': [120, 120],
        'ac_remaining_fh': [100, 100],
        'dist_km': [2400, 5500],
        'revenue_tl': [100000, 120000],
        'op_cost_tl': [20000, 25000],
        'fuel_cost_tl': [10000, 12000],
        'delay_cost_per_min': [500, 500],
        'load_factor': [0.83, 0.95],
        'pax_connection_count': [20, 30],
        'co2_kg': [5000, 6000],
        'weather_risk': [0.0, 0.0],
        'engine_health': [0.95, 0.92],
        'maintenance_reason': ['', ''],
        'market_qsi_weight': [1.0, 1.0],
        'business_pax': [50, 60],
        'leisure_pax': [100, 120],
        'is_canceled': [0, 0],
        'assigned_delay': [0, 0],
        'is_night_flight': [0, 0],
        'ntn_link_active': [1, 1],
        'slot_pressure_flag': [0, 0]
    }
    df = pd.DataFrame(data).set_index('flight_id')
    return df

def test_solver_feasible_baseline(mock_flights):
    """Test if solver can find a feasible baseline mapping."""
    solver = DigitalTwinSolver(mock_flights)
    result = solver.solve_with_windows()
    
    assert result is not None
    assert 'is_canceled' in result.columns
    assert 'assigned_aircraft' in result.columns
    # Ensure they were not dropped
    assert len(result) == 2

def test_solver_capacity_constraint(mock_flights):
    """Test if algorithm strictly blocks unsafe load factors (Pax > Capacity)."""
    # Overload TK100 beyond all legal aircraft capacities
    mock_flights.loc['TK100', 'passenger_count'] = 250 
    
    solver = DigitalTwinSolver(mock_flights)
    result = solver.solve_with_windows()
    
    assert result is not None
    # TK100 MUST be canceled or delayed since 250 > 189 (max fleet capacity)
    assert result.loc['TK100', 'is_canceled'] == 1


def test_solver_enforces_crew_duty_cap(mock_flights):
    """When all eligible pairings share one crew and total block time exceeds
    MAX_CREW_DUTY_MINS, at least one flight must be canceled."""
    from src.optimizer.dt_solver import MAX_CREW_DUTY_MINS

    df = mock_flights.copy()
    # Force both flights onto the same crew so the duty cap is the only
    # safety valve; bump block_time so the pair exceeds the FTL ceiling.
    df['crew_id'] = 'CRW-01'
    df['crew_cert'] = 'NARROW'
    df.loc['TK100', 'block_time'] = 400
    df.loc['TK200', 'block_time'] = 400
    # Keep routes chained so crew continuity is not the blocker.
    df.loc['TK200', 'origin'] = 'LHR'
    df.loc['TK200', 'destination'] = 'IST'

    solver = DigitalTwinSolver(df)
    result = solver.solve_winning(max_time_sec=10)

    assert int(result['is_canceled'].sum()) >= 1, (
        f"Duty cap ({MAX_CREW_DUTY_MINS}m) should have forced a cancellation "
        f"when total block time = 800m on a single crew"
    )


def test_solver_uses_hybrid_recovery_on_window_failure(mock_flights, monkeypatch):
    """If CP-SAT window solve fails, the hybrid GA recovery path should return a plan."""

    def _boom(self, strategy="PROFIT", max_time_sec=60):
        raise SolverError("forced failure")

    monkeypatch.setattr(DigitalTwinSolver, "solve_winning", _boom)

    solver = DigitalTwinSolver(mock_flights)
    result = solver.solve_with_windows()

    assert result is not None
    assert len(result) == 2
    assert "assigned_aircraft" in result.columns
    assert "hybrid_recoveries" in result.attrs
    assert len(result.attrs["hybrid_recoveries"]) >= 1
