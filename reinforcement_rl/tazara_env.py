import gymnasium as gym
from gymnasium import spaces
import numpy as np

from forecasting.predict_cargo import predict_cargo
from reinforcement_rl.routes import ROUTES
from reinforcement_rl.cost_model import (
    dispatch_reward,
    train_usage_penalty,
    delay_penalty,
    idle_penalty
)

# 🚆 Route travel times (days)
ROUTE_TRAVEL_DAYS = {
    "DAR_KAPIRI": 1,
    "DAR_MBEYA": 2,
    "KAPIRI_NDOLA": 1
}


class TazaraEnv(gym.Env):
    """
    Multi-route TAZARA environment
    Phase 2 – Step 2: Time & Delay Propagation
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, num_trains=6, max_cargo=5000, feature_template=None):
        super().__init__()

        self.total_trains = num_trains
        self.max_cargo = max_cargo
        self.routes = ROUTES
        self.route_names = list(self.routes.keys())

        self.feature_template = feature_template or {
            f"feature{i}": 0 for i in range(1, 14)
        }

        # Observation:
        # [cargo_route_1, cargo_route_2, ..., available_trains]
        obs_size = len(self.routes) + 1

        self.observation_space = spaces.Box(
            low=0,
            high=max_cargo,
            shape=(obs_size,),
            dtype=np.float32
        )

        # Action:
        # 0..N-1 → dispatch train to route i
        # N → delay
        # N+1 → idle
        self.action_space = spaces.Discrete(len(self.routes) + 2)

        self.reset()

    # --------------------------------------------------
    # Gym methods
    # --------------------------------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.available_trains = self.total_trains
        self.day = 0

        # 🚆 Train return schedule
        self.train_schedule = []

        # --------------------------------------------------
        # ✅ FIX: Force predicted cargo into scalar float
        # --------------------------------------------------
        predicted = predict_cargo(self.feature_template)

        if isinstance(predicted, (list, np.ndarray)):
            predicted_value = float(np.mean(predicted))
        else:
            predicted_value = float(predicted)

        predicted_value = min(predicted_value, self.max_cargo)

        # Cargo per route
        self.route_cargo = {
            name: predicted_value for name in self.route_names
        }

        return self._get_state(), {}

    def step(self, action):
        reward = 0.0
        trains_before = self.available_trains

        # --------------------------------------------------
        # ⏱ Release trains that completed trips
        # --------------------------------------------------
        returned_trains = [d for d in self.train_schedule if d <= self.day]
        self.available_trains += len(returned_trains)
        self.train_schedule = [d for d in self.train_schedule if d > self.day]

        # --------------------------------------------------
        # 🚆 Dispatch to a route
        # --------------------------------------------------
        if action < len(self.route_names) and self.available_trains > 0:
            route_name = self.route_names[action]
            route = self.routes[route_name]

            if self.route_cargo[route_name] > 0:
                cargo_moved = self.route_cargo[route_name] / route.max_daily_trains
                self.route_cargo[route_name] -= cargo_moved
                self.available_trains -= 1

                travel_days = ROUTE_TRAVEL_DAYS.get(route_name, 1)
                self.train_schedule.append(self.day + travel_days)

                reward = dispatch_reward(cargo_moved)
            else:
                reward = -idle_penalty()

        # --------------------------------------------------
        # ⏳ Delay
        # --------------------------------------------------
        elif action == len(self.route_names):
            for r in self.route_cargo:
                self.route_cargo[r] *= 1.05
            reward = -delay_penalty()

        # --------------------------------------------------
        # ❌ Idle
        # --------------------------------------------------
        else:
            reward = -idle_penalty()

        trains_used = trains_before - self.available_trains
        reward -= train_usage_penalty(trains_used)

        self.day += 1
        terminated = self.day >= 7
        truncated = False

        return self._get_state(), reward, terminated, truncated, {}

    def _get_state(self):
        cargo_state = [float(self.route_cargo[r]) for r in self.route_names]
        return np.array(cargo_state + [float(self.available_trains)], dtype=np.float32)

    def render(self, mode="human"):
        print(f"\n📅 Day {self.day}")
        for r in self.route_names:
            print(f"  Route {r}: Cargo {self.route_cargo[r]:.2f}")
        print(f"  Available trains: {self.available_trains}")
        print(f"  Trains returning on days: {self.train_schedule}")

    # --------------------------------------------------
    # Discretization (RL-safe)
    # --------------------------------------------------
    def discretize_state(self, state, cargo_bins=10, train_bins=5):
        state = np.array(state, dtype=np.float32)

        cargo_bins_state = tuple(
            int(np.clip((c / self.max_cargo) * cargo_bins, 0, cargo_bins - 1))
            for c in state[:-1]
        )

        train_bin = int(
            np.clip((state[-1] / self.total_trains) * train_bins, 0, train_bins - 1)
        )

        return cargo_bins_state + (train_bin,)
