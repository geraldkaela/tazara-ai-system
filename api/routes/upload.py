import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from api.utils.data_parser import parse_schedule_file
from reinforcement_rl.tazara_env import TazaraEnv
from reinforcement_rl.agent import QLearningAgent
from reinforcement_rl.cost_model import get_cost_breakdown

router = APIRouter()

# -----------------------------
# Paths (SAFE & STABLE)
# -----------------------------
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MODEL_PATH = os.path.join(BASE_DIR, "models", "q_table_phase2.pkl")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# Upload + AI Evaluation
# -----------------------------
@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV or XLSX allowed")

    # -----------------------------
    # Save file
    # -----------------------------
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # -----------------------------
    # Parse uploaded schedule
    # -----------------------------
    try:
        routes = parse_schedule_file(file_path)
        if not routes:
            raise ValueError("No routes detected in uploaded file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # -----------------------------
    # Ensure trained model exists
    # -----------------------------
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"RL model not found at {MODEL_PATH}. Train Phase 2 first."
        )

    # -----------------------------
    # RL Evaluation (STATE-SAFE)
    # -----------------------------
    try:
        env = TazaraEnv(num_trains=5)

        agent = QLearningAgent(
            state_bins=(10,) * len(env.route_names) + (5,),
            action_size=len(env.route_names) + 2,
            learning_rate=0.1,
            discount_factor=0.99,
            exploration_rate=0.0  # evaluation only
        )

        agent.load(MODEL_PATH)

        # -----------------------------
        # Reset environment (DO NOT MODIFY STATE)
        # -----------------------------
        state, _ = env.reset()

        ignored_routes = []

        # -----------------------------
        # Validate routes only
        # -----------------------------
        for r in routes:
            route_name = r.get("route")
            if route_name not in env.route_names:
                ignored_routes.append(route_name)

        # -----------------------------
        # Simulate one operational week
        # -----------------------------
        done = False
        total_reward = 0.0
        recommended_schedule = []
        total_cargo_delivered = 0
        total_trains_used = 0
        delay_days = 0
        idle_days = 0

        while not done:
            # Use environment's discretization method directly
            discrete_state = env.discretize_state(state)
            action = agent.select_action(discrete_state)

            if action < len(env.route_names):
                recommended_schedule.append(env.route_names[action])
            else:
                recommended_schedule.append("idle/delay")
                if action == len(env.route_names):
                    delay_days += 1
                else:
                    idle_days += 1

            state, reward, done, _, _ = env.step(action)
            total_reward += float(reward)
            
            # Track metrics for cost calculation
            if action < len(env.route_names):
                route_name = env.route_names[action]
                route = env.routes[route_name]
                cargo_moved = route.max_daily_trains * 50  # Estimated cargo per train
                total_cargo_delivered += cargo_moved
                total_trains_used += 1

        # Calculate ZMW cost breakdown
        cost_breakdown = get_cost_breakdown(
            cargo_delivered=total_cargo_delivered,
            trains_used=total_trains_used,
            delay_days=delay_days,
            idle_days=idle_days
        )

        evaluation = {
            "predicted_total_reward": round(total_reward, 2),
            "recommended_schedule": recommended_schedule,
            "ignored_routes": ignored_routes,
            "cost_breakdown_zmw": cost_breakdown
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI evaluation failed: {str(e)}"
        )

    return {
        "filename": filename,
        "routes_detected": len(routes),
        "routes_used": len(routes) - len(ignored_routes),
        "evaluation": evaluation,
        "message": "File processed and evaluated successfully"
    }
