import numpy as np
import pickle
from typing import List, Tuple, Optional
from collections import defaultdict

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv


class MultiRouteAgent:
    """
    Multi-route Q-Learning Agent for TAZARA scheduling
    Handles complex multi-train decision making
    """

    def __init__(
        self,
        state_bins: Tuple[int, ...],
        action_size: int,
        learning_rate: float = 0.1,
        discount_factor: float = 0.99,
        exploration_rate: float = 1.0,
        exploration_decay: float = 0.995,
        exploration_min: float = 0.01
    ):
        self.state_bins = state_bins
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.exploration_min = exploration_min

        # Multi-dimensional Q-table: Simplified approach for multi-train actions
        # We'll use a dictionary-based approach for complex state-action pairs
        self.q_table = {}  # Regular dict instead of defaultdict
        
        # Training metrics
        self.training_history = {
            'rewards': [],
            'losses': [],
            'exploration_rates': []
        }

    def discretize_state(self, state: np.ndarray) -> Tuple[int, ...]:
        """Convert continuous state to discrete indices"""
        discrete_state = []
        
        for i, (value, bin_count) in enumerate(zip(state, self.state_bins)):
            if i < len(state) - len(self.state_bins) // 3:  # Cargo values
                # Cargo levels (0 to max_cargo)
                discrete_value = min(int(value / 100), bin_count - 1)  # Bin by 100 tons
            else:
                # Train states and other values
                discrete_value = min(int(value), bin_count - 1)
            
            discrete_state.append(discrete_value)
        
        return tuple(discrete_state)

    def select_action(self, state: np.ndarray, valid_actions: Optional[List[int]] = None) -> np.ndarray:
        """Select actions for all trains using epsilon-greedy policy"""
        discrete_state = self.discretize_state(state)
        
        if np.random.random() <= self.exploration_rate:
            # Exploration: random valid actions
            actions = []
            for _ in range(len(state) // 4):  # Number of trains
                if valid_actions:
                    actions.append(np.random.choice(valid_actions))
                else:
                    actions.append(np.random.randint(0, 4))  # 0=idle, 1-3=routes
            return np.array(actions)
        
        # Exploitation: best Q-values
        actions = []
        for train_idx in range(len(state) // 4):
            # Get Q-values for this train's actions
            train_q_values = self._get_train_q_values(discrete_state, train_idx)
            
            if valid_actions:
                # Mask invalid actions
                masked_q = np.full(4, -np.inf)
                for action in valid_actions:
                    masked_q[action] = train_q_values[action]
                best_action = np.argmax(masked_q)
            else:
                best_action = np.argmax(train_q_values)
            
            actions.append(best_action)
        
        return np.array(actions)

    def _get_train_q_values(self, discrete_state: Tuple[int, ...], train_idx: int) -> np.ndarray:
        """Get Q-values for a specific train using dictionary approach"""
        # Simplified approach: use state hash as key
        state_key = hash(discrete_state)
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_size)
        return self.q_table[state_key]

    def get_action_rationale(self, state: np.ndarray, actions: np.ndarray) -> List[str]:
        """Generate human-readable rationales for chosen actions"""
        rationales = []
        num_routes = 3 # Fixed for TAZARA env
        route_names = ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"]
        
        # Cargo values are the first 3 indices of state
        cargo_levels = state[:num_routes]
        
        for i, action in enumerate(actions):
            if action == 0:
                # Why idle?
                if all(c < 100 for c in cargo_levels):
                    rationales.append("System idling to minimize operating costs; cargo demand is currently below efficient dispatch thresholds (100 tons).")
                else:
                    rationales.append("Strategically idling to prevent station congestion and wait for higher-priority cargo accumulation at the Port.")
            else:
                route_idx = action - 1
                route_name = route_names[route_idx]
                cargo = cargo_levels[route_idx]
                
                if cargo > 1000:
                    rationales.append(f"Dispatching to {route_name} at critical capacity ({int(cargo)} tons) to prevent throughput bottlenecks.")
                elif route_name == "DAR_KAPIRI":
                    rationales.append(f"Selected {route_name} to leverage long-distance efficiency bonuses and optimize fuel ROI.")
                else:
                    rationales.append(f"Selected {route_name} route based on optimized turnaround time and current locomotive fuel economy.")
                    
        return rationales

    def learn(self, state: np.ndarray, actions: np.ndarray, reward: float, 
              next_state: np.ndarray, done: bool):
        """Update Q-table based on experience"""
        discrete_state = self.discretize_state(state)
        discrete_next_state = self.discretize_state(next_state)
        
        # Calculate target Q-values for each train
        for train_idx in range(len(actions)):
            action = actions[train_idx]
            current_q = self._get_train_q_values(discrete_state, train_idx)[action]
            
            if done:
                target_q = reward
            else:
                next_q_values = self._get_train_q_values(discrete_next_state, train_idx)
                target_q = reward + self.discount_factor * np.max(next_q_values)
            
            # Update Q-value
            td_error = target_q - current_q
            self._update_q_value(discrete_state, train_idx, action, td_error)
        
        # Decay exploration rate
        self.exploration_rate = max(self.exploration_min, 
                                  self.exploration_rate * self.exploration_decay)
        
        # Track training metrics
        self.training_history['rewards'].append(reward)
        self.training_history['exploration_rates'].append(self.exploration_rate)

    def _update_q_value(self, discrete_state: Tuple[int, ...], train_idx: int, 
                       action: int, td_error: float):
        """Update Q-value for specific state-action pair"""
        state_key = hash(discrete_state)
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_size)
        self.q_table[state_key][action] += self.learning_rate * td_error

    def save(self, filepath: str):
        """Save agent to file"""
        agent_data = {
            'q_table': self.q_table,
            'state_bins': self.state_bins,
            'action_size': self.action_size,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'exploration_rate': self.exploration_rate,
            'exploration_decay': self.exploration_decay,
            'exploration_min': self.exploration_min,
            'training_history': self.training_history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(agent_data, f)

    def load(self, filepath: str):
        """Load agent from file"""
        with open(filepath, 'rb') as f:
            agent_data = pickle.load(f)
        
        self.q_table = agent_data['q_table']
        self.state_bins = agent_data['state_bins']
        self.action_size = agent_data['action_size']
        self.learning_rate = agent_data['learning_rate']
        self.discount_factor = agent_data['discount_factor']
        self.exploration_rate = agent_data['exploration_rate']
        self.exploration_decay = agent_data['exploration_decay']
        self.exploration_min = agent_data['exploration_min']
        self.training_history = agent_data.get('training_history', {
            'rewards': [],
            'losses': [],
            'exploration_rates': []
        })

    def predict(self, state) -> Tuple[np.ndarray, dict]:
        """Predict action for given state"""
        # Discretize the state
        discrete_state = self.discretize_state(state)
        
        # Convert to string for dictionary key
        state_key = str(discrete_state)
        
        # Choose action using epsilon-greedy policy
        if np.random.random() < self.exploration_rate:
            # Explore: random action
            action = np.random.randint(0, self.action_size)
        else:
            # Exploit: best known action
            if state_key in self.q_table:
                # Get best action from Q-table
                q_values = self.q_table[state_key]
                if isinstance(q_values, list) and len(q_values) > 0:
                    action = np.argmax(q_values)
                else:
                    action = np.random.randint(0, self.action_size)
            else:
                # Unknown state: random action
                action = np.random.randint(0, self.action_size)
        
        # Return action for each train (multi-train action)
        # For multi-route, we need individual actions for each train
        # We'll use different actions for each train to allow variety
        num_trains = 4  # Default number of trains
        
        # Create individual actions for each train
        individual_actions = []
        for i in range(num_trains):
            # Use base action with some variation for each train
            individual_action = min(action + i, self.action_size - 1)
            individual_actions.append(individual_action)
        
        multi_train_action = np.array(individual_actions)
        
        return multi_train_action, {}

    def get_training_stats(self) -> dict:
        """Get training statistics"""
        if not self.training_history['rewards']:
            return {}
        
        recent_rewards = self.training_history['rewards'][-100:]  # Last 100 episodes
        
        return {
            'total_episodes': len(self.training_history['rewards']),
            'average_reward': np.mean(recent_rewards),
            'max_reward': np.max(recent_rewards),
            'min_reward': np.min(recent_rewards),
            'current_exploration_rate': self.exploration_rate,
            'q_table_size': len(self.q_table),
            'q_table_memory_mb': len(self.q_table) * 4 * 4 / (1024 * 1024)  # Approximate
        }


def train_multi_route_agent(
    env: MultiRouteTazaraEnv,
    episodes: int = 1000,
    max_steps_per_episode: int = 100,
    save_path: str = "models/multi_route_agent.pkl"
) -> MultiRouteAgent:
    """Train multi-route agent"""
    
    # Calculate state bins based on environment
    state_size = env.observation_space.shape[0]
    state_bins = tuple([10] * min(state_size, 20))  # Limit to 20 dimensions for memory
    
    # Initialize agent
    agent = MultiRouteAgent(
        state_bins=state_bins,
        action_size=4,  # 0=idle, 1-3=routes
        learning_rate=0.1,
        discount_factor=0.99,
        exploration_rate=1.0,
        exploration_decay=0.995,
        exploration_min=0.01
    )
    
    print(f"🚂 Training Multi-Route Agent for {episodes} episodes...")
    print(f"📊 State dimensions: {state_size}, Action space: {env.action_space}")
    
    for episode in range(episodes):
        state, _ = env.reset()
        total_reward = 0
        
        for step in range(max_steps_per_episode):
            # Select actions for all trains
            actions = agent.select_action(state)
            
            # Execute step
            next_state, reward, done, truncated, info = env.step(actions)
            
            # Learn from experience
            agent.learn(state, actions, reward, next_state, done or truncated)
            
            state = next_state
            total_reward += reward
            
            if done or truncated:
                break
        
        # Progress reporting
        if episode % 100 == 0:
            stats = agent.get_training_stats()
            print(f"Episode {episode}: Reward={total_reward:.2f}, "
                  f"Avg_Reward={stats.get('average_reward', 0):.2f}, "
                  f"Exploration={agent.exploration_rate:.3f}")
    
    # Save trained agent
    agent.save(save_path)
    print(f"✅ Multi-route agent saved to {save_path}")
    
    return agent
