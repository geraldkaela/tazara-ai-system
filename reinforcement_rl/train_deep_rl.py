import os
import sys
import torch
import numpy as np
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable mock forecasting for faster training
os.environ["TAZARA_MOCK_FORECAST"] = "1"

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.deep_multi_route_agent import DeepMultiRouteAgent

def train_deep_rl_agent(
    episodes: int = 500,
    max_steps_per_episode: int = 100,
    save_path: str = "models/deep_multi_route_agent.pkl"
):
    """Train Deep Q-Learning agent for TAZARA multi-route scheduling"""
    
    # Initialize environment
    env = MultiRouteTazaraEnv(num_trains=6, max_cargo=5000)
    state_size = env.observation_space.shape[0]
    action_size = 4  # 0=idle, 1-3=routes
    
    # Initialize Deep Agent
    agent = DeepMultiRouteAgent(
        state_size=state_size,
        action_size=action_size,
        num_trains=6,
        learning_rate=0.001,
        exploration_decay=0.99,
        exploration_min=0.05
    )
    
    print(f"🚂 Training Deep RL Agent for {episodes} episodes...")
    print(f"📊 State size: {state_size}, Action size: {action_size}")
    
    best_avg_reward = -float('inf')
    
    for episode in range(episodes):
        state, _ = env.reset()
        total_reward = 0
        
        for step in range(max_steps_per_episode):
            # Select actions for all trains
            actions = agent.select_action(state)
            
            # Execute step
            next_state, reward, done, truncated, info = env.step(actions)
            
            # Record experience and learn
            agent.step(state, actions, reward, next_state, done or truncated)
            
            state = next_state
            total_reward += reward
            
            if done or truncated:
                break
        
        # Tracking progress
        agent.training_history['rewards'].append(total_reward)
        
        if (episode + 1) % 50 == 0:
            avg_reward = np.mean(agent.training_history['rewards'][-50:])
            print(f"Episode {episode+1}/{episodes}: Avg Reward={avg_reward:.2f}, "
                  f"Exploration={agent.exploration_rate:.3f}")
            
            # Save best model
            if avg_reward > best_avg_reward:
                best_avg_reward = avg_reward
                agent.save(save_path)
                print(f"⭐ New best avg reward! Model saved to {save_path}")
    
    # Final save
    agent.save(save_path)
    print(f"✅ Training complete. Final model saved to {save_path}")
    return agent

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    train_deep_rl_agent(episodes=300) # Reduced for initial test
