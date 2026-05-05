"""
HTTP middleware — enforces authentication on protected paths.

This middleware handles *authentication* (is the user logged in?).
*Authorization* (does the user have the right role?) is handled per-route
via `Depends(require_permission(...))` from api/auth/rbac.py.
"""

import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt

from api.config import JWT_SECRET_KEY, JWT_ALGORITHM

logger = logging.getLogger(__name__)

# Paths that never require a token
PUBLIC_PATHS = {
    "/",
    "/auth/token",
    "/auth/me",
    "/health",
    "/health/",
    "/alerts/summary",
    "/multi-route/dashboard/stats",
    "/api/dashboard/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/dashboard/login.html",
    "/dashboard/index.html",
    "/dashboard/multi_route.html",
    "/dashboard/alerts.html",
    "/dashboard/comparison.html",
    "/dashboard/rl.html",
    "/dashboard/users.html",
    "/dashboard/priority_impact_test.html",
    "/dashboard/test_risk_api.html",
    "/dashboard/debug_auth.html",
    "/favicon.ico",
    "/favicon",
    "/robots.txt",
    "/sitemap.xml",
    "/.well-known/appspecific/com.chrome.devtools.json",  # Chrome DevTools
}

# Prefixes that are always public (e.g. static assets for the login page)
PUBLIC_PREFIXES = ("/dashboard/assets/", "/dashboard/css/", "/dashboard/js/")


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(p) for p in PUBLIC_PREFIXES)


def add_auth_middleware(app: FastAPI) -> FastAPI:
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path
        logger.debug(f"Auth middleware checking path: {path}")

        if _is_public(path):
            logger.debug(f"Path {path} is public, allowing access")
            return await call_next(request)

        # Extract token from cookie or Authorization header
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            logger.debug(f"No token found for path: {path}")
            # For dashboard routes, redirect to login
            if path.startswith("/dashboard/") and not path.endswith("/login.html"):
                return RedirectResponse("/dashboard/login.html", status_code=302)
            # For API routes, return 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            logger.debug(f"Attempting to decode token for path: {path}")
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            logger.debug(f"Token decoded successfully for user: {payload.get('sub')}")
        except JWTError as e:
            logger.debug(f"JWT decode failed for path {path}: {e}")
            # For dashboard routes, redirect to login
            if path.startswith("/dashboard/") and not path.endswith("/login.html"):
                return RedirectResponse("/dashboard/login.html", status_code=302)
            # For API routes, return 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    return app
