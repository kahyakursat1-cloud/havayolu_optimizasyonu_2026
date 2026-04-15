import pytest
from sqlalchemy import select
from src.db.models import AuditEvent

@pytest.mark.asyncio
async def test_audit_logging_on_solve(client, auth_token, test_session):
    """Verify that a 'Solve' request creates an audit event."""
    # Trigger an action (even if it fails due to no data, it's a request)
    await client.post(
        "/api/optimizer/solve?strategy=PROFIT",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    # Check the database for audit logs
    result = await test_session.execute(select(AuditEvent))
    logs = result.scalars().all()
    
    # We should have at least the login and the solve request log
    # (Note: login might not be loggable via AuditMiddleware if it bypasses it, 
    # but the solver request certainly should)
    solve_logs = [l for l in logs if "api/optimizer/solve" in l.action]
    assert len(solve_logs) >= 1
    assert solve_logs[0].user_id is not None
