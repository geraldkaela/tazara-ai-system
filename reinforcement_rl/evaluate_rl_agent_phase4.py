import numpy as np
import joblib
from reinforcement_rl.tazara_env import TazaraEnv
import os

# ----------------------------
# Load trained Q-table
# ----------------------------
q_table_path = "models/q_table_phase4.pkl"
if not os.path.exists(q_table_path):
    raise FileNotFoundError(f"Q-table not found at {q_table_path}")
q_table = joblib.load(q_table_path)
print("Q-table loaded successfully!")

# ----------------------------
# Discretization helper
# ----------------------------
def discretize_state(state, bins=(10, 5, 1), max_vals=(5000, 5, 500)):
    """
    Convert a state (tuple, list, ndarray, or dict) into discrete indices for Q-table.
    """
    discrete = []
    for i in range(len(state)):
        val = state[i]

        # Handle dictionary (e.g., available_trains)
        if isinstance(val, dict):
            val = sum(val.values()) if val else 0

        # Handle NumPy arrays
        elif isinstance(val, np.ndarray):
            val = float(val.sum())

        # Ensure scalar
        else:
            val = float(val)

        step = max_vals[i] / bins[i]
        discrete.append(min(bins[i]-1, int(val / step)))
    return tuple(discrete)

# ----------------------------
# Run the RL agent in the environment
# ----------------------------
env = TazaraEnv(num_trains=5)
state, _ = env.reset()  # reset may return (state, info)
total_reward = 0
max_steps = 7  # for example, 7 days

for step in range(max_steps):
    discrete_state = discretize_state(state, bins=(10, 5, 1), max_vals=(5000, 5, 500))
    action = np.argmax(q_table[discrete_state])

    # Step environment
    next_state, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated

    print(f"Step {step+1}: Action={action}, Next state={next_state}, Reward={reward:.2f}")

    state = next_state
    total_reward += reward

    if done:
        break

print(f"Evaluation finished. Total reward: {total_reward:.2f}")
