import numpy as np
import matplotlib.pyplot as plt

from reinforcement_rl.tazara_env import TazaraEnv
from reinforcement_rl.agent import QLearningAgent
from reinforcement_rl.metrics_logger import MetricsLogger
from reinforcement_rl.audit_logger import AuditLogger
from reinforcement_rl.cost_model import (
    dispatch_reward,
    train_usage_penalty,
    delay_penalty,
    idle_penalty
)

# =========================
# CONFIG
# =========================
DAYS = 5
MODEL_PATH = "models/q_table_phase2.pkl"

# =========================
# INIT
# =========================
env = TazaraEnv(num_trains=5)

agent = QLearningAgent(
    state_bins=(10,) * len(env.route_names) + (5,),
    action_size=len(env.route_names) + 2,
    learning_rate=0.1,
    discount_factor=0.99,
    exploration_rate=0.0
)
agent.load(MODEL_PATH)

logger = MetricsLogger(save_path="metrics/rl_daily_report_phase2.csv")
audit = AuditLogger()

print("🚆 Evaluating RL Agent – TAZARA Multi-Route Daily Operations\n")

daily_rewards = []
daily_cargo = []
daily_trains_used = []

# =========================
# EVALUATION LOOP
# =========================
for day in range(1, DAYS + 1):
    print(f"📅 Day {day} operations started")

    state, _ = env.reset()
    done = False
    step = 0

    day_reward = 0
    day_cargo = 0
    day_trains_used = 0

    while not done:
        step += 1
        discrete_state = env.discretize_state(state)
        action = agent.select_action(discrete_state)

        trains_before = env.available_trains
        next_state, base_reward, done, _, _ = env.step(action)
        trains_after = env.available_trains

        # -------------------------
        # COST MODEL
        # -------------------------
        if action < len(env.route_names):
            reward = dispatch_reward(max(base_reward, 0)) - train_usage_penalty(trains_before - trains_after)
        elif action == len(env.route_names):
            reward = -delay_penalty()
        else:
            reward = -idle_penalty()

        cargo_delivered = max(reward, 0)

        # -------------------------
        # ALERTS + AUDIT SEVERITY
        # -------------------------
        severity = "INFO"
        message = "Normal operation"

        if action < len(env.route_names) and trains_before == 0:
            severity = "CRITICAL"
            message = "Dispatch attempted with zero trains"
            print(f"⚠️  Alert: RL agent tried to dispatch with no trains at Step {step}")

        total_cargo_left = sum(env.route_cargo[r] for r in env.route_names)
        if total_cargo_left > 0 and env.available_trains == 0:
            severity = "WARNING"
            message = "Cargo remaining but no trains available"
            print(f"⚠️  Alert: Cargo left undelivered at Day {day}")

        # -------------------------
        # AUDIT LOG
        # -------------------------
        audit.log(
            day=day,
            step=step,
            actor="rl_agent",
            action=action,
            available_trains=env.available_trains,
            cargo_remaining=total_cargo_left,
            reward=reward,
            severity=severity,
            message=message
        )

        # -------------------------
        # METRICS
        # -------------------------
        day_reward += reward
        day_cargo += cargo_delivered
        day_trains_used += (trains_before - trains_after)

        logger.log_step(
            action=action,
            reward=reward,
            cargo=cargo_delivered,
            trains_before=trains_before,
            trains_after=trains_after
        )

        print(f"Day {day} Step {step}: Action={action}, Reward={reward:.2f}")
        state = next_state

    daily_rewards.append(day_reward)
    daily_cargo.append(day_cargo)
    daily_trains_used.append(day_trains_used)

    logger.end_day(day)
    print(f"Day {day} finished.\n")

# =========================
# FINALIZE
# =========================
logger.save()
audit.close()

print("📊 Daily operations report saved to metrics/rl_daily_report_phase2.csv")
print("✅ Evaluation complete.")

# =========================
# PLOTTING
# =========================
plt.figure(figsize=(10, 5))
plt.plot(range(1, DAYS + 1), daily_rewards, marker='o', label="Daily Reward")
plt.plot(range(1, DAYS + 1), daily_cargo, marker='s', label="Cargo Delivered")
plt.plot(range(1, DAYS + 1), daily_trains_used, marker='^', label="Trains Used")
plt.xlabel("Day")
plt.ylabel("Value")
plt.title("RL Agent – Multi-Route Daily Metrics")
plt.legend()
plt.grid(True)
plt.show()
