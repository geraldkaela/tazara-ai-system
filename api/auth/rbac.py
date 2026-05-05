"""
Role-Based Access Control (RBAC) for TAZARA AI System

HOW IT WORKS
------------
1. On login, the user's role is embedded in JWT token (claim "role").
2. Every protected route declares which permission it needs via
   `Depends(require_permission(Permission.X))`.
3. FastAPI resolves the dependency chain:
       JWT token → get_current_user() → RequirePermission.__call__()
   and returns HTTP 403 if the role lacks the required permission.

USAGE IN A ROUTE
----------------
    from api.auth.rbac import Permission, require_permission
    from api.auth.auth import UserInDB

    @router.post("/schedules")
    async def create_schedule(
        data: ScheduleIn,
        current_user: UserInDB = Depends(require_permission(Permission.CREATE_SCHEDULE)),
    ):
        ...   # only admins and managers reach here
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, Set

from fastapi import Depends, HTTPException, status

from api.auth.auth import get_current_user, UserInDB

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class Permission(str, Enum):
    # Schedules
    CREATE_SCHEDULE = "create_schedule"
    EDIT_SCHEDULE   = "edit_schedule"
    DELETE_SCHEDULE = "delete_schedule"
    VIEW_SCHEDULES  = "view_schedules"

    # Orders
    CREATE_ORDER = "create_order"
    EDIT_ORDER   = "edit_order"
    DELETE_ORDER = "delete_order"
    VIEW_ORDERS  = "view_orders"

    # Users
    CREATE_USER = "create_user"
    EDIT_USER   = "edit_user"
    DELETE_USER = "delete_user"
    VIEW_USERS  = "view_users"

    # Reports & analytics
    VIEW_REPORTS    = "view_reports"
    EXPORT_REPORTS  = "export_reports"
    VIEW_ANALYTICS  = "view_analytics"

    # System administration
    SYSTEM_CONFIG   = "system_config"
    VIEW_LOGS       = "view_logs"
    SYSTEM_BACKUP   = "system_backup"

    # Operations
    VIEW_DASHBOARD  = "view_dashboard"
    VIEW_ALERTS     = "view_alerts"
    MANAGE_ALERTS   = "manage_alerts"

    # Priority queue / auto-scheduler
    RUN_SCHEDULER   = "run_scheduler"
    VIEW_PRIORITY   = "view_priority"


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

class Role(str, Enum):
    ADMIN    = "admin"
    MANAGER  = "manager"
    OPERATOR = "operator"
    VIEWER   = "viewer"


# ---------------------------------------------------------------------------
# Role → Permission mapping
# Edit this table to change what each role can do.
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),   # admin has every permission

    Role.MANAGER: {
        Permission.CREATE_SCHEDULE, Permission.EDIT_SCHEDULE, Permission.VIEW_SCHEDULES,
        Permission.CREATE_ORDER, Permission.EDIT_ORDER, Permission.VIEW_ORDERS,
        Permission.VIEW_USERS, Permission.EDIT_USER,
        Permission.VIEW_REPORTS, Permission.EXPORT_REPORTS, Permission.VIEW_ANALYTICS,
        Permission.VIEW_DASHBOARD, Permission.VIEW_ALERTS, Permission.MANAGE_ALERTS,
        Permission.RUN_SCHEDULER, Permission.VIEW_PRIORITY,
    },

    Role.OPERATOR: {
        Permission.VIEW_SCHEDULES, Permission.EDIT_SCHEDULE,
        Permission.CREATE_ORDER, Permission.EDIT_ORDER, Permission.VIEW_ORDERS,
        Permission.VIEW_REPORTS, Permission.VIEW_ANALYTICS,
        Permission.VIEW_DASHBOARD, Permission.VIEW_ALERTS,
        Permission.RUN_SCHEDULER, Permission.VIEW_PRIORITY,
    },

    Role.VIEWER: {
        Permission.VIEW_SCHEDULES, Permission.VIEW_ORDERS,
        Permission.VIEW_REPORTS, Permission.VIEW_ANALYTICS,
        Permission.VIEW_DASHBOARD, Permission.VIEW_ALERTS,
        Permission.VIEW_PRIORITY,
    },
}


# ---------------------------------------------------------------------------
# Core helper
# ---------------------------------------------------------------------------

def has_permission(role: str, permission: Permission) -> bool:
    """Return True if *role* includes *permission*."""
    try:
        role_enum = Role(role.lower())
    except ValueError:
        logger.warning("Unknown role '%s' — denying permission '%s'", role, permission)
        return False
    return permission in ROLE_PERMISSIONS.get(role_enum, set())


# ---------------------------------------------------------------------------
# FastAPI dependency factory  ← main thing you use in routes
# ---------------------------------------------------------------------------

def require_permission(permission: Permission):
    """
    Returns a FastAPI dependency that:
      • validates the JWT (via get_current_user)
      • checks the user's role has *permission*
      • raises HTTP 403 if not
      • returns the UserInDB object so routes can use it

    Example
    -------
        @router.delete("/schedules/{id}")
        async def delete_schedule(
            id: int,
            user: UserInDB = Depends(require_permission(Permission.DELETE_SCHEDULE)),
        ):
            ...
    """
    async def _check(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Your role '{current_user.role}' does not have "
                    f"the '{permission}' permission."
                ),
            )
        return current_user

    # Give the dependency a unique name so FastAPI's OpenAPI docs show it clearly
    _check.__name__ = f"require_{permission.value}"
    return _check


# ---------------------------------------------------------------------------
# Convenience: get accessible features for a role (useful for frontend menus)
# ---------------------------------------------------------------------------

def get_accessible_features(role: str) -> Dict[str, list[str]]:
    """Return a dict of feature categories → list of permitted action names."""
    try:
        role_enum = Role(role.lower())
    except ValueError:
        return {}

    perms = ROLE_PERMISSIONS.get(role_enum, set())

    schedule_perms = {Permission.CREATE_SCHEDULE, Permission.EDIT_SCHEDULE,
                      Permission.DELETE_SCHEDULE, Permission.VIEW_SCHEDULES}
    order_perms    = {Permission.CREATE_ORDER, Permission.EDIT_ORDER,
                      Permission.DELETE_ORDER, Permission.VIEW_ORDERS}
    user_perms     = {Permission.CREATE_USER, Permission.EDIT_USER,
                      Permission.DELETE_USER, Permission.VIEW_USERS}
    report_perms   = {Permission.VIEW_REPORTS, Permission.EXPORT_REPORTS, Permission.VIEW_ANALYTICS}
    system_perms   = {Permission.SYSTEM_CONFIG, Permission.VIEW_LOGS, Permission.SYSTEM_BACKUP}
    ops_perms      = {Permission.VIEW_DASHBOARD, Permission.VIEW_ALERTS, Permission.MANAGE_ALERTS,
                      Permission.RUN_SCHEDULER, Permission.VIEW_PRIORITY}

    return {
        "schedules":  [p.value for p in perms & schedule_perms],
        "orders":     [p.value for p in perms & order_perms],
        "users":      [p.value for p in perms & user_perms],
        "reports":    [p.value for p in perms & report_perms],
        "system":     [p.value for p in perms & system_perms],
        "operations": [p.value for p in perms & ops_perms],
    }
