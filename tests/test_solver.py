import pytest
import pandas as pd
from src.optimizer.dt_solver import DigitalTwinSolver

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
        'passenger_count': [150, 180],
        'ac_capacity': [180, 189],
        'ac_cat': ['NARROW', 'NARROW'],
        'crew_cert': ['NARROW', 'NARROW'],
        'block_time': [120, 120],
        'ac_remaining_fh': [100.0, 100.0],
        'revenue_tl': [100000, 120000],
        'op_cost_tl': [20000, 25000],
        'fuel_cost_tl': [10000, 12000],
        'delay_cost_per_min': [500, 500],
        'load_factor': [0.83, 0.95],
        'pax_connection_count': [20, 30],
        'co2_kg': [5000, 6000],
        'weather_risk': [0.0, 0.0],
        'status': ['SCHEDULED', 'SCHEDULED']
    }
    df = pd.DataFrame(data).set_index('flight_id')
    return df

def test_solver_feasible_baseline(mock_flights):
    """Test if solver can find a feasible baseline mapping."""
    solver = DigitalTwinSolver(mock_flights)
    result = solver.solve_baseline(max_time_sec=5)
    
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
    result = solver.solve_baseline(max_time_sec=5)
    
    assert result is not None
    # TK100 MUST be canceled or delayed since 250 > 189 (max fleet capacity)
    assert result.loc['TK100', 'is_canceled'] == 1
