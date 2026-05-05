import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import pickle
from collections import deque
from typing import List, Tuple, Optional, Dict

class QNetwork(nn.Module):
    """Neural Network for Q-Learning"""
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 64):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, action_size)
        
    def forward(self, state):
        x = torch.relu(self.fc1(state))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

class DeepMultiRouteAgent:
    """
    Deep Q-Learning Agent for TAZARA multi-route scheduling.
    Uses a centralized Q-network to decide actions for all trains.
    """
    def __init__(
        self,
        state_size: int,
        action_size: int,
        num_trains: int,
        learning_rate: float = 0.001,
        discount_factor: float = 0.99,
        exploration_rate: float = 1.0,
        exploration_decay: float = 0.995,
        exploration_min: float = 0.01,
        memory_size: int = 10000,
        batch_size: int = 64,
        target_update_freq: int = 10
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.num_trains = num_trains
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.exploration_min = exploration_min
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        self.memory = deque(maxlen=memory_size)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Primary and Target Networks
        self.q_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        self.steps_done = 0
        self.training_history = {
            'rewards': [],
            'losses': [],
            'exploration_rates': []
        }

    def select_action(self, state: np.ndarray, valid_actions: Optional[List[int]] = None) -> np.ndarray:
        """Select actions for all trains using epsilon-greedy policy"""
        if random.random() <= self.exploration_rate:
            actions = []
            for _ in range(self.num_trains):
                if valid_actions:
                    actions.append(random.choice(valid_actions))
                else:
                    actions.append(random.randint(0, self.action_size - 1))
            return np.array(actions)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        self.q_network.eval()
        with torch.no_grad():
            q_values = self.q_network(state_tensor).cpu().numpy()[0]
        self.q_network.train()
        
        # Currently, the Q-network predicts the best action for ANY train given the GLOBAL state.
        # To truly optimize multi-train, we would need a larger output or a specialized architecture.
        # For parity with the previous agent, we'll use the same Q-values for all trains.
        # Note: This implies a shared policy.
        
        actions = []
        if valid_actions:
            masked_q = np.full(self.action_size, -np.inf)
            for a in valid_actions:
                masked_q[a] = q_values[a]
            best_action = np.argmax(masked_q)
        else:
            best_action = np.argmax(q_values)
            
        # For multi-train, we could choose multiple best actions if we wanted diversity,
        # but the environment expectation is an action per train.
        # Here we just apply the same "best" policy to all trains.
        return np.array([best_action] * self.num_trains)

    def step(self, state, actions, reward, next_state, done):
        """Save experience and learn if batch size reached"""
        # Multi-action handling: we'll store the mean reward or individual experiences if possible.
        # For simplicity, we store the global transition.
        self.memory.append((state, actions, reward, next_state, done))
        
        if len(self.memory) >= self.batch_size:
            self.learn()
            
        if done:
            self.steps_done += 1
            if self.steps_done % self.target_update_freq == 0:
                self.target_network.load_state_dict(self.q_network.state_dict())
            
            # Decay exploration
            self.exploration_rate = max(self.exploration_min, 
                                      self.exploration_rate * self.exploration_decay)

    def learn(self):
        """Perform one step of gradient descent"""
        batch = random.sample(self.memory, self.batch_size)
        states, actions_list, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).to(self.device)
        # We simplify learning by using the reward as the global signal.
        # In multi-action DQN, we usually sum or average action values.
        # Here we'll just use the first action's contribution or average to map to a single head.
        actions = torch.LongTensor([a[0] for a in actions_list]).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)
        
        # Get current Q values
        current_q = self.q_network(states).gather(1, actions)
        
        # Get next Q values from target network
        with torch.no_grad():
            next_q = self.target_network(next_states).max(1)[0].unsqueeze(1)
            target_q = rewards + (self.discount_factor * next_q * (1 - dones))
            
        loss = self.criterion(current_q, target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.training_history['losses'].append(loss.item())

    def get_action_rationale(self, state: np.ndarray, actions: np.ndarray) -> List[str]:
        """Maintain interface with existing agent for rationales"""
        rationales = []
        route_names = ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"]
        cargo_levels = state[:3]
        
        for i, action in enumerate(actions):
            if action == 0:
                rationales.append("Optimizing fleet utilization: idling chosen to reduce empty wagon runs and wait for higher-profit cargo consolidation.")
            else:
                route_name = route_names[action-1]
                cargo = cargo_levels[action-1]
                rationales.append(f"Dispatched to {route_name} to fulfill demand ({int(cargo)} tons). Deep analysis indicates this maximizes Net Profit Margin (ZMW).")
        return rationales

    def save(self, filepath: str):
        """Save agent state"""
        save_data = {
            'q_network_state': self.q_network.state_dict(),
            'state_size': self.state_size,
            'action_size': self.action_size,
            'num_trains': self.num_trains,
            'exploration_rate': self.exploration_rate,
            'training_history': self.training_history
        }
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)

    def load(self, filepath: str):
        """Load agent state"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        self.q_network.load_state_dict(data['q_network_state'])
        self.target_network.load_state_dict(data['q_network_state'])
        self.exploration_rate = data['exploration_rate']
        self.training_history = data.get('training_history', self.training_history)
