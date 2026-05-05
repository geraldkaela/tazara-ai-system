import numpy as np
import pickle
from reinforcement_rl.tazara_env import TazaraEnv
from reinforcement_rl.q_learning_agent import QLearningAgent

EPISODES = 500

env = TazaraEnv()
agent = QLearningAgent()

for episode in range(EPISODES):
    state, _ = env.reset()
    done = False
    total_reward = 0

    # Inject predicted demand (mocked for now)
    env.state[2] = np.random.randint(100, 600)

    while not done:
        action = agent.choose_action(state)
        next_state, reward, done, _, _ = env.step(action)

        agent.learn(state, action, reward, next_state)
        state = next_state
        total_reward += reward

    agent.decay_epsilon()

    if episode % 50 == 0:
        print(f"Episode {episode}, Total Reward: {total_reward}, Epsilon: {agent.epsilon:.3f}")

# Save trained Q-table
with open("reinforcement_rl/q_table.pkl", "wb") as f:
    pickle.dump(agent.q_table, f)

print("✅ RL training complete. Q-table saved.")
