import os
from reinforcement_rl.tazara_env import TazaraEnv
from reinforcement_rl.agent import QLearningAgent
from reinforcement_rl.metrics_logger import MetricsLogger

# =========================
# CONFIG
# =========================
DAYS = 50
MODEL_DIR = "models"
MODEL_PATH = "models/q_table_phase2.pkl"

os.makedirs(MODEL_DIR, exist_ok=True)

# =========================
# INITIALIZE ENV + AGENT
# =========================
env = TazaraEnv(num_trains=5)

agent = QLearningAgent(
    state_bins=(10, 10, 10, 5),   # 3 routes + available trains
    action_size=env.action_space.n,
    learning_rate=0.1,
    discount_factor=0.99,
    exploration_rate=1.0          # exploration stays constant
)

logger = MetricsLogger(save_path="metrics/rl_training_phase2.csv")

print("🚆 Training RL Agent – Phase 2 (Multi-Route)")

# =========================
# TRAINING LOOP
# =========================
for day in range(1, DAYS + 1):
    state, _ = env.reset()
    discrete_state = env.discretize_state(state)

    done = False
    print(f"\n📅 Training Day {day} started")

    while not done:
        action = agent.select_action(discrete_state)

        trains_before = env.available_trains
        next_state, reward, done, _, _ = env.step(action)
        trains_after = env.available_trains

        next_discrete_state = env.discretize_state(next_state)

        agent.learn(
            discrete_state,
            action,
            reward,
            next_discrete_state
        )

        logger.log_step(
            action=action,
            reward=reward,
            cargo=max(reward, 0),
            trains_before=trains_before,
            trains_after=trains_after
        )

        discrete_state = next_discrete_state
        print(f"Action={action}, Reward={reward:.2f}")

    logger.end_day(day)

# =========================
# SAVE MODEL
# =========================
agent.save(MODEL_PATH)
logger.save()

print("\n✅ RL training complete")
print(f"💾 Model saved to: {MODEL_PATH}")
