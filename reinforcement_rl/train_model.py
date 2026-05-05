# reinforcement_rl/train_model.py

class Train:
    def __init__(self, capacity_tons, cost_per_km):
        self.capacity_tons = capacity_tons
        self.cost_per_km = cost_per_km


# Standard TAZARA freight train (example)
DEFAULT_TRAIN = Train(
    capacity_tons=800,     # realistic freight capacity
    cost_per_km=25         # ZMW per km (fuel + maintenance)
)
