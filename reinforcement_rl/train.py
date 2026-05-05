import numpy as np
import pickle
from reinforcement_rl.tazara_env import TazaraEnv
from reinforcement_rl.agent import QLearningAgent

# ----------------------------
# Training configuration
# ----------------------------
NUM_EPISODES = 1000
MAX_STEPS_PER_EPISODE = 50
MODEL_PATH = "models/q_table_phase5.pkl"

# ----------------------------
# Environment & Agent
# ----------------------------
env = TazaraEnv(num_trains=5)

agent = QLearningAgent(
    state_bins=(10, 5, 1),
    action_size=3,
    learning_rate=0.1,
    discount_factor=0.99,
    exploration_rate=1.0,
    min_exploration_rate=0.01,
    exploration_decay_rate=0.001,
)

# ----------------------------
# Training loop
# ----------------------------
print("🚆 Training RL agent started...\n")

for episode in range(NUM_EPISODES):
    state = env.reset()
    total_reward = 0

    for step in range(MAX_STEPS_PER_EPISODE):
        discrete_state = agent.discretize_state(state)
        action = agent.select_action(discrete_state)

        # Gymnasium-style step
        step_result = env.step(action)
        # Handle environment outputs safely
        if len(step_result) == 5:
            next_state, reward, terminated, truncated, _ = step_result
        elif len(step_result) == 4:
            next_state, reward, done, _ = step_result
            terminated = done
            truncated = False
        else:
            next_state, reward, done = step_result
            terminated = done
            truncated = False

        done = terminated or truncated

        next_discrete_state = agent.discretize_state(next_state)

        agent.learn(
            discrete_state,
            action,
            reward,
            next_discrete_state,
        )

        state = next_state
        total_reward += reward

        if done:
            break

    agent.decay_exploration(episode)

    if (episode + 1) % 100 == 0:
        print(
            f"Episode {episode + 1}/{NUM_EPISODES} | "
            f"Total Reward: {total_reward:.2f} | "
            f"Epsilon: {agent.exploration_rate:.3f}"
        )

# ----------------------------
# Save trained Q-table directly
# ----------------------------
with open(MODEL_PATH, "wb") as f:
    pickle.dump(agent.q_table, f)

print("\n✅ Training complete!")
print(f"📦 Q-table saved to: {MODEL_PATH}")
