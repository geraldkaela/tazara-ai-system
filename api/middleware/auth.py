"""
Authentication Middleware for TAZARA AI System
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

class AuthMiddleware:
    """Middleware to check authentication for protected routes"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.protected_paths = [
            "/dashboard/index.html",
            "/dashboard/multi_route.html",
            "/dashboard/alerts.html",
            "/dashboard/analytics.html"
        ]
        self.api_protected_paths = [
            "/multi-route/",
            "/alerts/",
            "/api/dashboard/",
            "/api/config/"
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            path = request.url.path
            
            # Check if this is a protected path
            if self.is_protected_path(path):
                # Check for token in cookies or headers
                token = self.get_token_from_request(request)
                
                if not token or not self.verify_token(token):
                    # Redirect to login for web pages
                    if path.startswith("/dashboard/"):
                        response = RedirectResponse(url="/dashboard/login.html", status_code=302)
                        await response(scope, receive, send)
                        return
                    # Return 401 for API calls
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication required",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
        
        # Continue with the normal request processing
        await self.app(scope, receive, send)
    
    def is_protected_path(self, path: str) -> bool:
        """Check if the path requires authentication"""
        # Check protected dashboard pages
        for protected_path in self.protected_paths:
            if path == protected_path or path.startswith(protected_path):
                return True
        
        # Check protected API endpoints
        for protected_path in self.api_protected_paths:
            if path.startswith(protected_path):
                return True
        
        return False
    
    def get_token_from_request(self, request: Request) -> str:
        """Extract token from request"""
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        
        # Try to get token from cookies
        token = request.cookies.get("access_token")
        if token:
            return token
        
        return None
    
    def verify_token(self, token: str) -> bool:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return False
            return True
        except JWTError:
            return False

def add_auth_middleware(app: FastAPI):
    """Add authentication middleware to FastAPI app"""
    # Create a custom middleware wrapper
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path
        
        # Define paths that don't require authentication
        public_paths = [
            "/",
            "/dashboard/login.html",
            "/auth/",
            "/health",
            "/docs",
            "/openapi.json",
            "/system/info"
        ]
        
        # Check if path is public
        is_public = any(path.startswith(public_path) for public_path in public_paths)
        
        if not is_public and path.startswith("/dashboard/"):
            # Check for token in cookies or headers
            token = request.cookies.get("access_token")
            if not token:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            
            # Verify token
            if not token:
                return RedirectResponse(url="/dashboard/login.html", status_code=302)
            
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if username is None:
                    return RedirectResponse(url="/dashboard/login.html", status_code=302)
            except JWTError:
                return RedirectResponse(url="/dashboard/login.html", status_code=302)
        
        # Continue with request
        response = await call_next(request)
        return response
    
    return app
