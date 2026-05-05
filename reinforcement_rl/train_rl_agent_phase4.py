import numpy as np
import random
from reinforcement_rl.tazara_env import TazaraEnv

# ----------------------------
# Q-Learning Hyperparameters
# ----------------------------
NUM_EPISODES = 500
MAX_STEPS = 50
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.95
EPSILON = 0.2  # Exploration probability

# ----------------------------
# Discretization helper
# ----------------------------
def discretize_state(state, bins=(10, 2, 10), max_vals=(5000, 1, 500)):
    """Convert continuous state to discrete indices for Q-table"""
    discrete = []
    for i in range(len(state)):
        step = max_vals[i] / bins[i]
        discrete.append(min(bins[i]-1, int(state[i] / step)))
    return tuple(discrete)

# ----------------------------
# Initialize environment and Q-table
# ----------------------------
env = TazaraEnv(max_cargo=5000)
state_sample, _ = env.reset()
state_bins = (10, 2, 10)
q_table = np.zeros(state_bins + (env.action_space.n,))

# ----------------------------
# Training loop
# ----------------------------
for episode in range(NUM_EPISODES):
    state, _ = env.reset()
    discrete_state = discretize_state(state, bins=state_bins)
    total_reward = 0

    for step in range(MAX_STEPS):
        # Epsilon-greedy action selection
        if random.uniform(0, 1) < EPSILON:
            action = env.action_space.sample()
        else:
            action = np.argmax(q_table[discrete_state])

        # Take action
        next_state, reward, done, truncated, _ = env.step(action)
        discrete_next_state = discretize_state(next_state, bins=state_bins)

        # Q-learning update
        old_value = q_table[discrete_state + (action,)]
        next_max = np.max(q_table[discrete_next_state])
        new_value = old_value + LEARNING_RATE * (reward + DISCOUNT_FACTOR * next_max - old_value)
        q_table[discrete_state + (action,)] = new_value

        discrete_state = discrete_next_state
        total_reward += reward

        if done:
            break

    if (episode + 1) % 50 == 0:
        print(f"Episode {episode+1}, Total Reward: {total_reward}")

# ----------------------------
# Save trained Q-table
# ----------------------------
import joblib
joblib.dump(q_table, "models/q_table_phase4.pkl")
print("Q-table saved successfully!")
