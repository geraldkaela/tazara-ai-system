"""
Train movement tracking: destination, ETA, and arrival based on wall-clock time.

Distance model
--------------
Leg duration is derived from **route distance (km)** and a conservative **average freight
speed** (km/h), so a run of many hundreds of kilometres yields multi-day transits, not
minutes. Override with *demo* timers only for lab demos.

Pause (emergency hold)
----------------------
`paused_at` set: countdown **freezes** (remaining time = ETA − moment pause began).
On **resume**, `expected_arrival_at` is shifted forward by the pause duration so total
transit time reflects the stop. Auto-arrival does not run while paused.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone, date
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from psycopg2.extras import RealDictCursor

from api.db_utils import get_db_connection
from api.auth.rbac import Permission, require_permission
from api.auth.auth import UserInDB

router = APIRouter(prefix="/api/tracking", tags=["Train tracking"])

# Typical heavy-freight average speed on long TAZARA-style legs (loaded, stops, path).
DEFAULT_FREIGHT_SPEED_KPH = 38.0
# Minimum modelled leg time so very short parsed segments are not instant.
MIN_LEG_DURATION_HOURS = 4.0

# Ordered longest-first so e.g. Dar→Kapiri wins over Dar→Mbeya when both match.
_ROUTE_LEGS_KM: List[Tuple[re.Pattern, re.Pattern, float]] = [
    (re.compile(r"dar\s+es\s+salaam|dar-es-salaam", re.I), re.compile(r"kapiri", re.I), 1860.0),
    (re.compile(r"kapiri", re.I), re.compile(r"dar\s+es\s+salaam|dar-es-salaam", re.I), 1860.0),
    (re.compile(r"dar\s+es\s+salaam|dar-es-salaam", re.I), re.compile(r"mbeya", re.I), 850.0),
    (re.compile(r"mbeya", re.I), re.compile(r"dar\s+es\s+salaam|dar-es-salaam", re.I), 850.0),
    (re.compile(r"mbeya", re.I), re.compile(r"kapiri", re.I), 1010.0),
    (re.compile(r"kapiri", re.I), re.compile(r"mbeya", re.I), 1010.0),
    (re.compile(r"morogoro", re.I), re.compile(r"dodoma", re.I), 260.0),
    (re.compile(r"dodoma", re.I), re.compile(r"morogoro", re.I), 260.0),
    (re.compile(r"dodoma", re.I), re.compile(r"mbeya", re.I), 400.0),
    (re.compile(r"mbeya", re.I), re.compile(r"dodoma", re.I), 400.0),
]
# When endpoints are unknown but both look like real stations: assume ~500 km regional move.
_FALLBACK_DISTANCE_KM = 520.0


def _norm_pair(origin: str, dest: str) -> Tuple[str, str]:
    return (origin or "").strip(), (dest or "").strip()


def estimate_route_km(origin: str, dest: str) -> float:
    o, d = _norm_pair(origin, dest)
    if not o or not d:
        return _FALLBACK_DISTANCE_KM
    for po, pd, km in _ROUTE_LEGS_KM:
        if po.search(o) and pd.search(d):
            return km
    return _FALLBACK_DISTANCE_KM


def estimate_leg_duration_seconds(
    origin: str,
    dest: str,
    speed_kph: float = DEFAULT_FREIGHT_SPEED_KPH,
) -> int:
    km = estimate_route_km(origin, dest)
    hours = km / max(speed_kph, 1.0)
    hours = max(hours, MIN_LEG_DURATION_HOURS)
    return int(hours * 3600)


def parse_route_label(route_display: str) -> Tuple[Optional[str], Optional[str]]:
    if not route_display:
        return None, None
    parts = re.split(r"\s+to\s+", route_display.strip(), maxsplit=1, flags=re.I)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return route_display.strip(), None


def _row_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return value


def _seconds_remaining(row: Dict) -> int:
    if row.get("leg_status") != "in_transit":
        return 0
    eta = _row_ts(row.get("expected_arrival_at"))
    if eta is None:
        return 0
    paused_at = _row_ts(row.get("paused_at"))
    if paused_at is not None:
        # Frozen at pause: remaining time until ETA measured from pause instant.
        return max(0, int((eta - paused_at).total_seconds()))
    now = datetime.now(timezone.utc)
    return max(0, int((eta - now).total_seconds()))


def _ensure_table(cursor) -> None:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'train_trip_legs'
        ) AS table_exists
        """
    )
    row = cursor.fetchone()
    exists = bool(next(iter(row.values()))) if row else False
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="train_trip_legs table missing. Apply database/train_tracking_schema.sql",
        )


def _ensure_pause_column(cursor) -> None:
    """Older DBs: add paused_at without re-running full schema."""
    cursor.execute(
        """
        ALTER TABLE train_trip_legs
        ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ
        """
    )


class ActivateTrackingBody(BaseModel):
    """If use_demo_timers is True, each leg uses demo_leg_seconds instead of distance-based time."""

    use_demo_timers: bool = False
    demo_leg_seconds: int = Field(120, ge=15, le=86400)
    stagger_seconds: int = Field(3, ge=0, le=3600)
    average_speed_kph: Optional[float] = Field(
        None,
        ge=15.0,
        le=120.0,
        description="Override freight speed for distance-based ETA (default 38 km/h).",
    )


class TripLegOut(BaseModel):
    id: int
    schedule_id: str
    train_id: str
    route_display: str
    origin_station: Optional[str]
    destination_station: Optional[str]
    cargo_tons: Optional[float]
    day_number: int
    leg_status: str
    departed_at: Optional[datetime]
    expected_arrival_at: Optional[datetime]
    arrived_at: Optional[datetime]
    expected_duration_seconds: int
    estimated_route_km: float
    is_paused: bool
    paused_at: Optional[datetime]
    seconds_remaining: int


def _mark_arrived(cursor) -> int:
    cursor.execute(
        """
        UPDATE train_trip_legs
        SET leg_status = 'arrived',
            arrived_at = COALESCE(arrived_at, NOW()),
            updated_at = NOW()
        WHERE leg_status = 'in_transit'
          AND paused_at IS NULL
          AND expected_arrival_at IS NOT NULL
          AND expected_arrival_at <= NOW()
        """
    )
    return cursor.rowcount


def _leg_to_out(row: Dict) -> TripLegOut:
    origin = row.get("origin_station")
    dest = row.get("destination_station")
    km = estimate_route_km(origin or "", dest or "")
    paused_at = _row_ts(row.get("paused_at"))
    return TripLegOut(
        id=row["id"],
        schedule_id=row["schedule_id"],
        train_id=row["train_id"],
        route_display=row["route_display"],
        origin_station=row.get("origin_station"),
        destination_station=row.get("destination_station"),
        cargo_tons=float(row["cargo_tons"]) if row.get("cargo_tons") is not None else None,
        day_number=row.get("day_number") or 1,
        leg_status=row["leg_status"],
        departed_at=_row_ts(row.get("departed_at")),
        expected_arrival_at=_row_ts(row.get("expected_arrival_at")),
        arrived_at=_row_ts(row.get("arrived_at")),
        expected_duration_seconds=int(row.get("expected_duration_seconds") or 0),
        estimated_route_km=round(km, 1),
        is_paused=paused_at is not None,
        paused_at=paused_at,
        seconds_remaining=_seconds_remaining(dict(row)),
    )


@router.get("/trips/active", response_model=Dict[str, Any])
async def get_active_and_recent_trips(
    limit_arrived: int = 25,
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_SCHEDULES)),
):
    """
    Returns in-transit legs (with seconds_remaining) and recently arrived legs.
    Automatically marks legs as arrived when wall clock passes expected_arrival_at
    (never while paused).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        _ensure_table(cursor)
        _ensure_pause_column(cursor)
        _mark_arrived(cursor)
        conn.commit()

        cursor.execute(
            """
            SELECT * FROM train_trip_legs
            WHERE leg_status = 'in_transit'
            ORDER BY expected_arrival_at NULLS LAST, id
            """
        )
        active = [_leg_to_out(dict(r)).model_dump() for r in cursor.fetchall()]

        cursor.execute(
            """
            SELECT * FROM train_trip_legs
            WHERE leg_status = 'arrived'
            ORDER BY arrived_at DESC NULLS LAST, id DESC
            LIMIT %s
            """,
            (limit_arrived,),
        )
        arrived = [_leg_to_out(dict(r)).model_dump() for r in cursor.fetchall()]

        cursor.close()
        conn.close()
        return {"success": True, "in_transit": active, "recently_arrived": arrived}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/schedules/{schedule_id}/legs", response_model=Dict[str, Any])
async def list_legs_for_schedule(
    schedule_id: str,
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_SCHEDULES)),
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        _ensure_table(cursor)
        _ensure_pause_column(cursor)
        _mark_arrived(cursor)
        conn.commit()

        cursor.execute(
            """
            SELECT * FROM train_trip_legs
            WHERE schedule_id = %s
            ORDER BY day_number, id
            """,
            (schedule_id,),
        )
        legs = [_leg_to_out(dict(r)).model_dump() for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {"success": True, "schedule_id": schedule_id, "legs": legs}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/schedules/{schedule_id}/activate", response_model=Dict[str, Any])
async def activate_tracking_for_schedule(
    schedule_id: str,
    body: ActivateTrackingBody = ActivateTrackingBody(),
    current_user: UserInDB = Depends(require_permission(Permission.EDIT_SCHEDULE)),
):
    """
    Build trip legs from daily_assignments for this schedule, mark them in_transit, and set ETAs.
    Clears any non-arrived legs for this schedule_id first so re-activation is idempotent.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        _ensure_table(cursor)
        _ensure_pause_column(cursor)

        cursor.execute(
            "SELECT schedule_id FROM schedules WHERE schedule_id = %s LIMIT 1",
            (schedule_id,),
        )
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Schedule not found")

        cursor.execute(
            "DELETE FROM train_trip_legs WHERE schedule_id = %s AND leg_status != 'arrived'",
            (schedule_id,),
        )

        cursor.execute(
            """
            SELECT id, day, train_id, route, cargo_tons, action
            FROM daily_assignments
            WHERE schedule_id = %s
            ORDER BY day, train_id, id
            """,
            (schedule_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            conn.commit()
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="No daily_assignments for this schedule. Create a schedule first.",
            )

        speed = body.average_speed_kph or DEFAULT_FREIGHT_SPEED_KPH
        now = datetime.now(timezone.utc)
        inserted = 0
        for i, row in enumerate(rows):
            r = dict(row)
            if (r.get("action") or "").lower() == "idle":
                continue
            route_display = (r.get("route") or "").strip() or "Unknown"
            origin, dest = parse_route_label(route_display)
            if body.use_demo_timers:
                duration_sec = body.demo_leg_seconds
            else:
                duration_sec = estimate_leg_duration_seconds(origin or "", dest or "", speed_kph=speed)

            departed = now + timedelta(seconds=body.stagger_seconds * i)
            expected_arrival = departed + timedelta(seconds=duration_sec)

            cursor.execute(
                """
                INSERT INTO train_trip_legs (
                    schedule_id, train_id, route_display, origin_station, destination_station,
                    cargo_tons, day_number, leg_status, departed_at, expected_arrival_at,
                    expected_duration_seconds, paused_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'in_transit', %s, %s, %s, NULL)
                """,
                (
                    schedule_id,
                    str(r.get("train_id") or ""),
                    route_display,
                    origin,
                    dest,
                    r.get("cargo_tons"),
                    int(r.get("day") or 1),
                    departed,
                    expected_arrival,
                    duration_sec,
                ),
            )
            inserted += 1

        conn.commit()
        cursor.close()
        conn.close()
        return {
            "success": True,
            "schedule_id": schedule_id,
            "legs_created": inserted,
            "use_demo_timers": body.use_demo_timers,
            "average_speed_kph": speed,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/legs/{leg_id}/pause", response_model=Dict[str, Any])
async def pause_leg(
    leg_id: int,
    current_user: UserInDB = Depends(require_permission(Permission.EDIT_SCHEDULE)),
):
    """Emergency / operational hold: freezes countdown until resume."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        _ensure_table(cursor)
        _ensure_pause_column(cursor)

        cursor.execute(
            """
            UPDATE train_trip_legs
            SET paused_at = NOW(), updated_at = NOW()
            WHERE id = %s AND leg_status = 'in_transit' AND paused_at IS NULL
            RETURNING id
            """,
            (leg_id,),
        )
        if not cursor.fetchone():
            conn.rollback()
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Leg not found, not in transit, or already paused",
            )
        conn.commit()
        cursor.close()
        conn.close()
        return {"success": True, "leg_id": leg_id, "paused": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/legs/{leg_id}/resume", response_model=Dict[str, Any])
async def resume_leg(
    leg_id: int,
    current_user: UserInDB = Depends(require_permission(Permission.EDIT_SCHEDULE)),
):
    """Resume after pause: ETA moves forward by the pause duration."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        _ensure_table(cursor)
        _ensure_pause_column(cursor)

        cursor.execute(
            """
            UPDATE train_trip_legs
            SET expected_arrival_at = expected_arrival_at + (NOW() - paused_at),
                paused_at = NULL,
                updated_at = NOW()
            WHERE id = %s AND leg_status = 'in_transit' AND paused_at IS NOT NULL
            RETURNING id
            """,
            (leg_id,),
        )
        if not cursor.fetchone():
            conn.rollback()
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Leg not found, not in transit, or not paused",
            )
        conn.commit()
        cursor.close()
        conn.close()
        return {"success": True, "leg_id": leg_id, "paused": False}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _assignment_departure_at(schedule_created: Any, day: int, departure_date_raw: Any) -> datetime:
    """Prefer order departure_date; else approximate from schedule creation + plan day."""
    base = _row_ts(schedule_created) or datetime.now(timezone.utc)
    if departure_date_raw is not None:
        if isinstance(departure_date_raw, datetime):
            dt = _row_ts(departure_date_raw)
            if dt:
                return dt
        if isinstance(departure_date_raw, date):
            return datetime.combine(departure_date_raw, datetime.min.time()).replace(
                tzinfo=timezone.utc
            ) + timedelta(hours=6)
    return base + timedelta(days=max(0, int(day or 1) - 1))


@router.get("/auto-schedule/latest-summary", response_model=Dict[str, Any])
async def latest_auto_schedule_summary(
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_SCHEDULES)),
):
    """
    Latest row from `schedules` plus each daily assignment with modelled departure / ETA
    (same distance–speed model as train tracking). Does not require tracking to be activated.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT schedule_id, created_at, num_trains, max_days,
                   total_cargo_delivered, efficiency_score, total_reward
            FROM schedules
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        sched = cursor.fetchone()
        if not sched:
            cursor.close()
            conn.close()
            return {"success": False, "message": "No auto schedules found", "schedule": None, "assignments": []}

        sched = dict(sched)
        sid = sched["schedule_id"]

        try:
            cursor.execute(
                """
                SELECT id, day, train_id, route, cargo_tons, action, departure_date
                FROM daily_assignments
                WHERE schedule_id = %s
                ORDER BY day, train_id, id
                """,
                (sid,),
            )
        except Exception:
            cursor.execute(
                """
                SELECT id, day, train_id, route, cargo_tons, action
                FROM daily_assignments
                WHERE schedule_id = %s
                ORDER BY day, train_id, id
                """,
                (sid,),
            )

        rows = [dict(r) for r in cursor.fetchall()]
        assignments_out: List[Dict[str, Any]] = []
        cargo_assigned = 0.0

        for r in rows:
            if (r.get("action") or "").lower() == "idle":
                continue
            route_display = (r.get("route") or "").strip() or "Unknown"
            origin, dest = parse_route_label(route_display)
            day = int(r.get("day") or 1)
            dep_raw = r.get("departure_date")
            depart_at = _assignment_departure_at(sched.get("created_at"), day, dep_raw)
            duration_sec = estimate_leg_duration_seconds(origin or "", dest or "")
            eta_at = depart_at + timedelta(seconds=duration_sec)
            tons = float(r.get("cargo_tons") or 0)
            cargo_assigned += tons

            assignments_out.append(
                {
                    "id": r.get("id"),
                    "day": day,
                    "train_id": str(r.get("train_id") or ""),
                    "route": route_display,
                    "origin_station": origin,
                    "destination_station": dest,
                    "cargo_tons": tons,
                    "action": r.get("action"),
                    "departure_at": depart_at.isoformat(),
                    "estimated_arrival_at": eta_at.isoformat(),
                    "modelled_transit_hours": round(duration_sec / 3600, 1),
                    "estimated_route_km": round(estimate_route_km(origin or "", dest or ""), 1),
                }
            )

        cursor.close()
        conn.close()

        return {
            "success": True,
            "schedule": {
                "schedule_id": sid,
                "created_at": sched.get("created_at"),
                "num_trains": sched.get("num_trains"),
                "max_days": sched.get("max_days"),
                "total_cargo_delivered": float(sched["total_cargo_delivered"] or 0),
                "efficiency_score": float(sched["efficiency_score"] or 0),
                "total_reward": float(sched["total_reward"] or 0),
                "assignments_cargo_tons": round(cargo_assigned, 2),
            },
            "assignments": assignments_out,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/arrivals/reminders", response_model=Dict[str, Any])
async def arrival_reminders_for_schedules(
    limit: int = 80,
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_SCHEDULES)),
):
    """
    Timer-based arrivals: legs marked `arrived` on the server (train tracking).
    Shown as reminders for all schedules that had tracking activated.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'train_trip_legs'
            ) AS table_exists
            """
        )
        row = cursor.fetchone()
        exists = bool(next(iter(row.values()))) if row else False
        if not exists:
            cursor.close()
            conn.close()
            return {
                "success": True,
                "reminders": [],
                "hint": "Run database/train_tracking_schema.sql and activate tracking to see arrival reminders.",
            }

        _ensure_pause_column(cursor)
        _mark_arrived(cursor)
        conn.commit()

        lim = max(1, min(limit, 200))
        cursor.execute(
            """
            SELECT id, schedule_id, train_id, route_display, origin_station, destination_station,
                   arrived_at, cargo_tons
            FROM train_trip_legs
            WHERE leg_status = 'arrived'
              AND arrived_at IS NOT NULL
            ORDER BY arrived_at DESC
            LIMIT %s
            """,
            (lim,),
        )
        reminders = []
        for r in cursor.fetchall():
            d = dict(r)
            ct = d.get("cargo_tons")
            cargo_part = f" Modelled cargo: {float(ct):.1f} t." if ct is not None else ""
            reminders.append(
                {
                    "id": d["id"],
                    "schedule_id": d["schedule_id"],
                    "train_id": d["train_id"],
                    "route_display": d["route_display"],
                    "destination_station": d.get("destination_station"),
                    "cargo_tons": float(ct) if ct is not None else None,
                    "arrived_at": _row_ts(d.get("arrived_at")).isoformat() if d.get("arrived_at") else None,
                    "reminder_title": "Train arrived",
                    "reminder_text": (
                        f"Schedule {d['schedule_id']}: train {d['train_id']} has arrived "
                        f"({d['route_display']}).{cargo_part}"
                    ),
                }
            )

        cursor.close()
        conn.close()
        return {"success": True, "reminders": reminders}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
