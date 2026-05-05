# reinforcement_rl/route_model.py

class Route:
    def __init__(self, name, distance_km, max_daily_trains):
        self.name = name
        self.distance_km = distance_km
        self.max_daily_trains = max_daily_trains


# Predefined TAZARA routes (simplified)
ROUTES = {
    "DAR_KAPIRI": Route(
        name="Dar es Salaam → Kapiri Mposhi",
        distance_km=1860,
        max_daily_trains=6
    )
}
