from rl_environment import TazaraEnv
import random

# Initialize environment
env = TazaraEnv(max_cargo=5000)

# Reset environment
state, info = env.reset()
print("Initial state:", state)

# Example: Set predicted demand for this episode
predicted_demand = 300  # realistic demand in tons
env.set_predicted_demand(predicted_demand)

# Run one episode
done = False
while not done:
    # Choose random action (0 = do nothing, 1 = dispatch, 2 = delay)
    action = random.choice([0, 1, 2])

    next_state, reward, done, truncated, info = env.step(action)
    print(f"Step {env.steps}: Action={action}, Next state={next_state}, Reward={reward}")

    # Render current state
    env.render()

print("Episode finished after", env.steps, "steps")
