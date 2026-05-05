import numpy as np
import joblib
import os


class QLearningAgent:
    """
    Unified Q-learning agent for TAZARA system
    """

    def __init__(
        self,
        state_bins=(10, 5, 1),
        action_size=3,
        learning_rate=0.1,
        discount_factor=0.99,
        exploration_rate=1.0,
        min_exploration_rate=0.01,
        exploration_decay_rate=0.001,
    ):
        self.state_bins = state_bins
        self.action_size = action_size

        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

        self.exploration_rate = exploration_rate
        self.min_exploration_rate = min_exploration_rate
        self.exploration_decay_rate = exploration_decay_rate

        # Q-table shape: (cargo, trains, demand, actions)
        self.q_table = np.zeros(tuple(b + 1 for b in state_bins) + (action_size,))

    # --------------------------------------------------
    # State discretization (ROBUST & FINAL)
    # --------------------------------------------------
    def discretize_state(self, state):
        """
        Accepts dict, tuple, list, or numpy array
        Returns discrete (cargo_idx, train_idx, demand_idx)
        """

        # Normalize state into numeric components
        if isinstance(state, dict):
            cargo = state.get("cargo_forecast", 0)
            trains = state.get("available_trains", 0)
        elif isinstance(state, (tuple, list, np.ndarray)):
            cargo = state[0]
            trains = state[1]
        else:
            raise TypeError(f"Unsupported state type: {type(state)}")

        # Handle arrays / dicts safely
        cargo = float(np.sum(cargo)) if isinstance(cargo, (np.ndarray, list)) else float(cargo)

        if isinstance(trains, dict):
            trains = sum(trains.values()) if trains else 0
        trains = int(np.sum(trains)) if isinstance(trains, (np.ndarray, list)) else int(trains)

        # Discretization
        cargo_idx = min(
            int(cargo / (cargo + 1) * self.state_bins[0]),
            self.state_bins[0],
        )
        train_idx = min(trains, self.state_bins[1])
        demand_idx = 0  # reserved for future predicted-demand expansion

        return (cargo_idx, train_idx, demand_idx)

    # --------------------------------------------------
    # Action selection
    # --------------------------------------------------
    def select_action(self, discrete_state):
        if np.random.rand() < self.exploration_rate:
            return np.random.randint(self.action_size)
        return np.argmax(self.q_table[discrete_state])

    # --------------------------------------------------
    # Learning update
    # --------------------------------------------------
    def learn(self, state, action, reward, next_state):
        current_q = self.q_table[state + (action,)]
        max_future_q = np.max(self.q_table[next_state])

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_future_q - current_q
        )

        self.q_table[state + (action,)] = new_q

    # --------------------------------------------------
    # Exploration decay
    # --------------------------------------------------
    def decay_exploration(self, episode):
        self.exploration_rate = self.min_exploration_rate + (
            (1.0 - self.min_exploration_rate)
            * np.exp(-self.exploration_decay_rate * episode)
        )

    # --------------------------------------------------
    # Persistence
    # --------------------------------------------------
    def save(self, path="models/q_table.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.q_table, path)

    def load(self, path="models/q_table.pkl"):
        self.q_table = joblib.load(path)
