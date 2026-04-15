from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.db.models import AuditEvent
from src.db import config as db_config
import json
import hashlib
from datetime import datetime, timezone
import logging

logger = logging.getLogger("AviationSingularity.Audit")

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude common noise points
        if request.url.path in ["/health", "/metrics", "/api/sync/live-traffic"]:
            return await call_next(request)

        # Proceed with the request
        response = await call_next(request)

        # Log significant state-changing or tactical actions
        if request.method in ["POST", "PUT", "DELETE", "PATCH"] or "/api/scenario" in request.url.path:
            try:
                # Capture user_id if available from request state
                user_id = getattr(request.state, "user_id", None)
                
                async with db_config.async_session_maker() as session:
                    audit = AuditEvent(
                        user_id=user_id,
                        action=f"{request.method} {request.url.path}",
                        details={
                            "status_code": response.status_code,
                            "query_params": dict(request.query_params)
                        }
                    )
                    session.add(audit)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Audit log failed: {e}")

        return response
