"""
Simple Authentication Module for TAZARA AI System
Uses SHA-256 hashing instead of bcrypt to avoid compatibility issues
Includes RBAC (Role-Based Access Control)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SECRET_KEY = "tazara-ai-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database connection
def get_db():
    conn = psycopg2.connect(
        host='localhost',
        database='tazara_multi_route',
        user='tazara',
        password='tazara123'
    )
    return conn

# Pydantic models
class User(BaseModel):
    username: str
    email: str
    role: str = "operator"

class UserInDB(User):
    id: int
    password_hash: str
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_role: str
    permissions: list

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    permissions: dict

# User management functions
def get_password_hash(password: str) -> str:
    """Generate SHA-256 password hash"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against SHA-256 hash"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s",
                (username,)
            )
            user_data = cursor.fetchone()
            if user_data:
                return UserInDB(**user_data)
    finally:
        conn.close()
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user credentials"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_user_permissions(role: str) -> dict:
    """Get user permissions based on role"""
    # Define role-based permissions
    role_permissions = {
        "admin": {
            "schedules": ["create", "edit", "delete", "view"],
            "users": ["create", "edit", "delete", "view"],
            "reports": ["view", "export"],
            "system": ["config", "logs", "backup"],
            "operations": ["dashboard", "alerts", "manage_alerts"]
        },
        "manager": {
            "schedules": ["create", "edit", "view"],
            "users": ["view", "edit"],
            "reports": ["view", "export"],
            "system": [],
            "operations": ["dashboard", "alerts", "manage_alerts"]
        },
        "operator": {
            "schedules": ["view", "edit"],
            "users": [],
            "reports": ["view"],
            "system": [],
            "operations": ["dashboard", "alerts"]
        },
        "viewer": {
            "schedules": ["view"],
            "users": [],
            "reports": ["view"],
            "system": [],
            "operations": ["dashboard", "alerts"]
        }
    }
    
    return role_permissions.get(role, {"schedules": [], "users": [], "reports": [], "system": [], "operations": []})

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# API Endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token with role and permissions"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    
    # Get user permissions
    permissions = get_user_permissions(user.role)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_role": user.role,
        "permissions": list(permissions.keys())
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Get current user information with permissions"""
    permissions = get_user_permissions(current_user.role)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "permissions": permissions
    }

@router.post("/register", response_model=User)
async def register_user(user: User, password: str):
    """Register a new user"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Check if user already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (user.username, user.email)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already registered"
                )
            
            # Create new user
            password_hash = get_password_hash(password)
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id, username, email, role, is_active
                """,
                (user.username, user.email, password_hash, user.role)
            )
            user_data = cursor.fetchone()
            conn.commit()
            
            return UserInDB(
                id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                role=user_data[3],
                is_active=user_data[4],
                password_hash=password_hash
            )
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )
    finally:
        conn.close()

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Successfully logged out"}

@router.get("/logout")
async def logout_redirect():
    """Logout endpoint that redirects to login page"""
    return {"message": "Successfully logged out", "redirect": "/dashboard/login.html"}

# Test endpoint
@router.get("/test")
async def test_auth():
    """Test authentication endpoint"""
    return {"message": "Authentication system is working!"}
