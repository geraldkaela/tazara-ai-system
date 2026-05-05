from reinforcement_rl.tazara_env import TazaraEnv

env = TazaraEnv(num_trains=5)
print('Number of routes:', len(env.route_names))
print('Route names:', env.route_names)
print('Expected state_bins:', (10,) * len(env.route_names) + (5,))
print('Expected Q-table shape:', tuple(b + 1 for b in (10,) * len(env.route_names) + (5,)) + (len(env.route_names) + 2,))

# Test discretize_state
state = env.reset()
discrete_state = env.discretize_state(state)
print('Actual discrete state:', discrete_state)
print('Discrete state length:', len(discrete_state))
