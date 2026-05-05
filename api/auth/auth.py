"""
Authentication Module for TAZARA AI System
Handles user authentication, JWT tokens, and get_current_user dependency.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

from api.config import DB_CONFIG, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain: str, hashed: str) -> bool:
    # Handle plain text passwords
    if hashed == plain:
        return True
    # Try bcrypt verification if it looks like a bcrypt hash
    if hashed.startswith('$2'):
        try:
            return pwd_context.verify(plain, hashed)
        except:
            return False
    # Try SHA256 verification (for existing hashed passwords)
    import hashlib
    try:
        sha256_hash = hashlib.sha256(plain.encode()).hexdigest()
        return sha256_hash == hashed
    except:
        return False


def get_password_hash(password: str) -> str:
    # Truncate password to 72 characters (bcrypt limit)
    truncated_password = password[:72] if len(password) > 72 else password
    try:
        return pwd_context.hash(truncated_password)
    except Exception as e:
        print(f"ERROR in password hashing: {e}")
        # Fallback to SHA256 if bcrypt fails
        import hashlib
        return hashlib.sha256(truncated_password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

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
    role: str   # ← included so the frontend knows the user's role immediately


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


def get_user(username: str) -> Optional[UserInDB]:
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            return UserInDB(**row) if row else None
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if user and verify_password(password, user.password_hash):
        return user
    return None


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT.

    The payload always includes:
      sub  – username
      role – user's role (used by RBAC checks without a DB round-trip)
      exp  – expiry timestamp
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    FastAPI dependency — decodes the JWT and returns the UserInDB.
    Used directly in routes that only need authentication (not a specific permission).
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = get_user(username)
    if user is None:
        raise credentials_exc
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Dependency that additionally checks the user account is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login — returns a JWT token that includes the user's role."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token = create_access_token(
        data={"sub": user.username, "role": user.role},   # ← role in token
        expires_delta=timedelta(minutes=JWT_EXPIRE_MINUTES),
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,
        "role": user.role,
    }


@router.get("/me", response_model=User)
async def me(current_user: UserInDB = Depends(get_current_active_user)):
    """Return the currently authenticated user's profile."""
    # Add timeout handling and better error response
    try:
        return current_user
    except Exception as e:
        print(f"ERROR in /auth/me endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication service temporarily unavailable")


@router.post("/logout")
async def logout():
    """Logout (client is responsible for discarding the token)."""
    return {"message": "Successfully logged out"}


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def create_auth_tables():
    """Create users and audit tables (idempotent — safe to run on every startup)."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      VARCHAR(50)  UNIQUE NOT NULL,
                    email         VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role          VARCHAR(20)  NOT NULL DEFAULT 'operator'
                                  CHECK (role IN ('admin','manager','operator','viewer')),
                    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
                    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id         SERIAL PRIMARY KEY,
                    user_id    INTEGER REFERENCES users(id),
                    action     VARCHAR(50)  NOT NULL,
                    resource   VARCHAR(100),
                    details    JSONB,
                    ip_address INET,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Default admin (password must be changed immediately in production)
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES ('admin', 'admin@tazara.rail', %s, 'admin')
                ON CONFLICT (username) DO NOTHING
            """, (get_password_hash("admin"),))

        conn.commit()
        logger.info("Auth tables created / verified OK")
    except Exception:
        conn.rollback()
        logger.exception("Failed to create auth tables")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# User management endpoints (admin only — enforced via RBAC in router)
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "operator"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/me/permissions")
async def my_permissions(current_user: UserInDB = Depends(get_current_active_user)):
    """Return the current user's role and accessible features."""
    from api.auth.rbac import get_accessible_features
    return {
        "username": current_user.username,
        "role": current_user.role,
        "features": get_accessible_features(current_user.role),
    }


@router.get("/users")
async def list_users(current_user: UserInDB = Depends(get_current_active_user)):
    """List all users — admin only."""
    from api.auth.rbac import require_permission, Permission
    # inline permission check (alternative to Depends — both work)
    from api.auth.rbac import has_permission
    if not has_permission(current_user.role, Permission.VIEW_USERS):
        raise HTTPException(status_code=403, detail="Admin or manager access required")

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id")
            return cur.fetchall()
    finally:
        conn.close()


@router.post("/users", response_model=User, status_code=201)
async def create_user(
    payload: UserCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Create a user — admin only."""
    from api.auth.rbac import has_permission, Permission
    if not has_permission(current_user.role, Permission.CREATE_USER):
        raise HTTPException(status_code=403, detail="Admin access required")

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id FROM users WHERE username=%s OR email=%s",
                (payload.username, payload.email),
            )
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Username or email already taken")

            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id, username, email, role, is_active
                """,
                (payload.username, payload.email, get_password_hash(payload.password), payload.role),
            )
            row = cur.fetchone()
        conn.commit()
        return dict(row)
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Update a user — admin only."""
    from api.auth.rbac import has_permission, Permission
    if not has_permission(current_user.role, Permission.EDIT_USER):
        raise HTTPException(status_code=403, detail="Admin or manager access required")

    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"UPDATE users SET {set_clause} WHERE id = %s RETURNING id, username, email, role, is_active",
                (*updates.values(), user_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return dict(row)
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()


@router.get("/users", response_model=List[User])
async def list_users(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """List all users — admin only."""
    from api.auth.rbac import has_permission, Permission
    if not has_permission(current_user.role, Permission.VIEW_USERS):
        raise HTTPException(status_code=403, detail="Admin access required")

    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, username, email, role, is_active, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
            """)
            users = cur.fetchall()
        return [dict(row) for row in users]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()


@router.put("/users/{username}/status")
async def toggle_user_status(
    username: str,
    payload: dict,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Toggle user active status — admin only."""
    from api.auth.rbac import has_permission, Permission
    if not has_permission(current_user.role, Permission.EDIT_USER):
        raise HTTPException(status_code=403, detail="Admin access required")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_active = %s, updated_at = NOW() WHERE username = %s",
                (payload.get('is_active', False), username)
            )
        conn.commit()
        return {"message": f"User {username} status updated successfully"}
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()


@router.delete("/users/{username}")
async def delete_user(
    username: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Delete a user — admin only."""
    from api.auth.rbac import has_permission, Permission
    if not has_permission(current_user.role, Permission.DELETE_USER):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Prevent self-deletion
    if current_user.username == username:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE username = %s", (username,))
            affected_rows = cur.rowcount
        conn.commit()
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": f"User {username} deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()


if __name__ == "__main__":
    create_auth_tables()
