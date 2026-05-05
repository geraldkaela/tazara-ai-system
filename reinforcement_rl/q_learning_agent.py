import numpy as np

class QLearningAgent:
    def __init__(
        self,
        state_bins=(10, 2, 10),
        action_size=3,
        learning_rate=0.1,
        discount_factor=0.95,
        epsilon=1.0,
        epsilon_decay=0.995,
        epsilon_min=0.01,
    ):
        """
        Simple tabular Q-learning agent.
        """
        self.state_bins = state_bins
        self.action_size = action_size
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        self.q_table = np.zeros(state_bins + (action_size,))

    def discretize_state(self, state):
        cargo, train_available, demand = state

        cargo_bin = min(int(cargo / 500), self.state_bins[0] - 1)
        train_bin = int(train_available)
        demand_bin = min(int(demand / 300), self.state_bins[2] - 1)

        return cargo_bin, train_bin, demand_bin

    def choose_action(self, state):
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.action_size)

        s = self.discretize_state(state)
        return np.argmax(self.q_table[s])

    def learn(self, state, action, reward, next_state):
        s = self.discretize_state(state)
        ns = self.discretize_state(next_state)

        best_next = np.max(self.q_table[ns])
        td_target = reward + self.gamma * best_next
        td_error = td_target - self.q_table[s][action]

        self.q_table[s][action] += self.lr * td_error

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
