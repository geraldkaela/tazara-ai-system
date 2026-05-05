import numpy as np
import matplotlib.pyplot as plt
from reinforcement_rl.tazara_env import TazaraEnv
from reinforcement_rl.metrics_logger import MetricsLogger
from reinforcement_rl.cost_model import dispatch_reward, train_usage_penalty, delay_penalty, idle_penalty

# Import the Phase 2 Baseline Scheduler
from reinforcement_rl.baseline_scheduler import BaselineScheduler

DAYS = 5

env = TazaraEnv(num_trains=5)
baseline = BaselineScheduler()
logger = MetricsLogger(save_path="metrics/baseline_daily_report_phase2.csv")

print("🚆 Evaluating BASELINE scheduler – TAZARA Multi-Route Daily Operations\n")

daily_rewards = []
daily_cargo = []
daily_trains_used = []

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
        route_cargo = [state[i] for i in range(len(env.route_names))]
        action = baseline.select_action(route_cargo, env.available_trains)

        trains_before = env.available_trains
        next_state, base_reward, done, _, _ = env.step(action)
        trains_after = env.available_trains

        # Phase 2 deterministic cost model
        if action < len(env.route_names):
            reward = dispatch_reward(max(base_reward, 0)) - train_usage_penalty(trains_before - trains_after)
        elif action == len(env.route_names):
            reward = -delay_penalty()
        else:
            reward = -idle_penalty()

        cargo_delivered = max(reward, 0)

        # Alerts
        if action < len(env.route_names) and trains_before == 0:
            print(f"⚠️  Alert: Baseline tried to dispatch a train but none were available at Step {step}!")
        total_cargo_left = sum(env.route_cargo[r] for r in env.route_names)
        if total_cargo_left > 0 and env.available_trains == 0:
            print(f"⚠️  Alert: Cargo left undelivered at Day {day}!")

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

logger.save()
print("📊 Daily operations report saved to metrics/baseline_daily_report_phase2.csv")
print("✅ Evaluation complete.")

# ------------------------
# Simple Plotting
# ------------------------
plt.figure(figsize=(10, 5))
plt.plot(range(1, DAYS + 1), daily_rewards, marker='o', label="Daily Reward")
plt.plot(range(1, DAYS + 1), daily_cargo, marker='s', label="Cargo Delivered")
plt.plot(range(1, DAYS + 1), daily_trains_used, marker='^', label="Trains Used")
plt.xlabel("Day")
plt.ylabel("Value")
plt.title("Baseline Scheduler – Multi-Route Daily Metrics")
plt.legend()
plt.grid(True)
plt.show()
