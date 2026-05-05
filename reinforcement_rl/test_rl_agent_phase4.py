import numpy as np
import joblib
from reinforcement_rl.tazara_env import TazaraEnv

# ----------------------------
# Load trained Q-table
# ----------------------------
q_table = joblib.load("models/q_table_phase4.pkl")
print("Q-table loaded successfully!")

# ----------------------------
# Discretization helper
# ----------------------------
state_bins = (10, 5, 1)  # [cargo_forecast, available_trains, predicted_demand]
max_vals = (5000, 5, 1)  # max values for discretization

def discretize_state(state, bins=state_bins, max_vals=max_vals):
    """Convert state (tuple, dict, list, or np.ndarray) to discrete indices for Q-table"""

    # Convert numpy array to list if needed
    if isinstance(state, np.ndarray):
        state = state.tolist()

    # Unpack tuple or list
    if isinstance(state, (tuple, list)):
        cargo_forecast, available_trains = state
    # Handle dict
    elif isinstance(state, dict):
        cargo_forecast = state.get("cargo_forecast", 0)
        available_trains = state.get("available_trains", 0)
    else:
        raise TypeError(f"Unexpected state type: {type(state)}")

    # If cargo_forecast is an array/list, convert to scalar
    if isinstance(cargo_forecast, (np.ndarray, list)):
        cargo_forecast = float(np.sum(cargo_forecast))  # sum all elements to scalar

    # If available_trains is an array/list/dict, convert to scalar
    if isinstance(available_trains, dict):
        available_trains = list(available_trains.values())[0] if available_trains else 0
    elif isinstance(available_trains, (np.ndarray, list)):
        available_trains = int(np.sum(available_trains))
    else:
        available_trains = int(available_trains)

    # Discretize
    cargo_idx = min(int(cargo_forecast / (max_vals[0] + 1) * bins[0]), bins[0])
    train_idx = min(available_trains, bins[1])
    demand_idx = 0  # placeholder

    return (cargo_idx, train_idx, demand_idx)

# ----------------------------
# Run the agent
# ----------------------------
env = TazaraEnv(num_trains=5)
state = env.reset()
total_reward = 0

max_steps = getattr(env, "max_steps", 50)

for step in range(max_steps):
    discrete_state = discretize_state(state)
    action = np.argmax(q_table[discrete_state])

    # Step in environment
    result = env.step(action)  # grab whatever step() returns
    if len(result) == 3:
        next_state, reward, done = result
    else:
        # fallback in case step() returns extra info
        next_state, reward, done = result[:3]

    print(f"Step {step+1}: Action={action}, Next state={next_state}, Reward={reward:.2f}")

    state = next_state
    total_reward += reward

    if done:
        break

print(f"Episode finished. Total reward: {total_reward:.2f}")
