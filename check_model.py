import joblib
import numpy as np

try:
    q_table = joblib.load('models/q_table_phase2.pkl')
    print('Q-table shape:', q_table.shape)
    print('Expected state dimensions:', len(q_table.shape) - 1)
    print('Action size:', q_table.shape[-1])
except Exception as e:
    print('Error loading model:', e)
