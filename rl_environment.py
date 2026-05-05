import gymnasium as gym
from gymnasium import spaces
import numpy as np

class TazaraEnv(gym.Env):
    """
    Custom RL environment for TAZARA cargo scheduling.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, max_cargo=5000):
        super().__init__()

        # State: [current cargo, train availability, predicted demand]
        self.observation_space = spaces.Box(low=0, high=max_cargo, shape=(3,), dtype=np.float32)

        # Actions: 0 = do nothing, 1 = dispatch train, 2 = delay train
        self.action_space = spaces.Discrete(3)

        # Initialize state
        self.state = np.array([0, 1, 0], dtype=np.float32)
        self.max_cargo = max_cargo
        self.steps = 0
        self.max_steps = 50

    def set_predicted_demand(self, value):
        """
        Set the predicted demand in the current state.
        """
        self.state[2] = value

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.array([0, 1, 0], dtype=np.float32)
        self.steps = 0
        return self.state, {}

    def step(self, action):
        current_cargo, train_available, predicted_demand = self.state

        # Example dynamics
        if action == 1 and train_available > 0:
            current_cargo = min(current_cargo + predicted_demand, self.max_cargo)
            train_available -= 1
            reward = predicted_demand
        elif action == 2:
            reward = -5  # Penalty for delaying
        else:
            reward = 0

        self.state = np.array([current_cargo, train_available, predicted_demand], dtype=np.float32)
        self.steps += 1
        done = self.steps >= self.max_steps

        return self.state, reward, done, False, {}  # Gymnasium uses 5-element tuple

    def render(self, mode="human"):
        print(f"Step: {self.steps}, State: {self.state}")
