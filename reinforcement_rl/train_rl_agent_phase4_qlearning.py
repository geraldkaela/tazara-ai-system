import numpy as np
import joblib
from reinforcement_rl.tazara_env import TazaraEnv
import os

# Hyperparameters
num_episodes = 1000
max_steps_per_episode = 50
learning_rate = 0.1
discount_factor = 0.99
exploration_rate = 1.0
max_exploration_rate = 1.0
min_exploration_rate = 0.01
exploration_decay_rate = 0.001

# Create environment
env = TazaraEnv(num_trains=5)

# Discretize the observation space for Q-table
state_bins = [10, 5, 1]  # [cargo_forecast, available_trains, predicted_demand]
state_space_sizes = [b + 1 for b in state_bins]

# Initialize Q-table
q_table = np.zeros(state_space_sizes + [3])  # 3 actions

def discretize_state(state):
    """Convert state (tuple, dict, or ndarray) to discrete indices for Q-table"""
    # If tuple
    if isinstance(state, tuple):
        cargo_forecast, available_trains = state

    # If dict
    elif isinstance(state, dict):
        cargo_forecast = state.get("cargo_forecast", 0)
        available_trains = state.get("available_trains", 0)

    # If numpy array
    elif isinstance(state, np.ndarray):
        if state.size == 2:
            cargo_forecast, available_trains = state
        else:
            # Fallback: sum all elements if unexpected shape
            cargo_forecast = float(np.sum(state))
            available_trains = 0
    else:
        raise TypeError(f"Unexpected state type: {type(state)}")

    # Convert to float/int if they are arrays
    if isinstance(cargo_forecast, np.ndarray):
        cargo_forecast = float(cargo_forecast.sum())
    else:
        cargo_forecast = float(cargo_forecast)

    if isinstance(available_trains, np.ndarray):
        available_trains = int(available_trains.sum())
    elif isinstance(available_trains, dict):
        available_trains = int(list(available_trains.values())[0]) if available_trains else 0
    else:
        available_trains = int(available_trains)

    # Discretize
    cargo_idx = min(int(cargo_forecast / (cargo_forecast + 1) * state_bins[0]), state_bins[0])
    train_idx = min(available_trains, state_bins[1])
    demand_idx = 0  # placeholder

    return (cargo_idx, train_idx, demand_idx)


# Training loop
for episode in range(num_episodes):
    state = env.reset()
    done = False

    for step in range(max_steps_per_episode):
        discrete_state = discretize_state(state)

        # Epsilon-greedy action selection
        if np.random.rand() < exploration_rate:
            action = np.random.choice([0, 1, 2])
        else:
            action = np.argmax(q_table[discrete_state])

        # Step environment
        next_state, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        next_discrete_state = discretize_state(next_state)

        # Q-learning update
        q_table[discrete_state + (action,)] = q_table[discrete_state + (action,)] + learning_rate * (
            reward + discount_factor * np.max(q_table[next_discrete_state]) - q_table[discrete_state + (action,)]
        )

        state = next_state
        if done:
            break

    # Decay exploration rate
    exploration_rate = min_exploration_rate + \
        (max_exploration_rate - min_exploration_rate) * np.exp(-exploration_decay_rate * episode)

# Save Q-table
os.makedirs("models", exist_ok=True)
joblib.dump(q_table, "models/q_table_phase4.pkl")
print("Q-table trained and saved to models/q_table_phase4.pkl")
