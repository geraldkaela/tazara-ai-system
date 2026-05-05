from reinforcement_rl.tazara_env import TazaraEnv
import numpy as np

env = TazaraEnv(num_trains=5)
state = env.reset()
print('State type:', type(state))
print('State:', state)
print('State length:', len(state) if hasattr(state, '__len__') else 'N/A')

if isinstance(state, tuple):
    for i, part in enumerate(state):
        print(f'State[{i}]: {part} (type: {type(part)})')
