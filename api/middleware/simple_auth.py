"""
Simple Authentication Middleware for TAZARA AI System
Protects dashboard pages and API endpoints
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = "tazara-ai-secret-key-change-in-production"
ALGORITHM = "HS256"

def add_auth_middleware(app: FastAPI):
    """Add authentication middleware to FastAPI app"""
    
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path
        
        # Define paths that don't require authentication
        public_paths = [
            "/",
            "/dashboard/login.html",
            "/auth/token",
            "/health",
            "/docs",
            "/openapi.json",
            "/system/info"
        ]
        
        # Check if path is public
        is_public = any(path.startswith(public_path) for public_path in public_paths)
        
        # Protect all API endpoints except token endpoint
        if not is_public and (path.startswith("/dashboard/") or path.startswith("/auth/") or path.startswith("/multi-route/") or path.startswith("/api/")):
            # Check for token in cookies or headers
            token = request.cookies.get("access_token")
            if not token:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            
            # Verify token
            if not token:
                if path.startswith("/dashboard/"):
                    return RedirectResponse(url="/dashboard/login.html", status_code=302)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if username is None:
                    if path.startswith("/dashboard/"):
                        return RedirectResponse(url="/dashboard/login.html", status_code=302)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
            except JWTError:
                if path.startswith("/dashboard/"):
                    return RedirectResponse(url="/dashboard/login.html", status_code=302)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        
        # Continue with request
        response = await call_next(request)
        return response
    
    return app
