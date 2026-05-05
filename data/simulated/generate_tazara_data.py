import pandas as pd
import numpy as np

# Reproducibility
np.random.seed(42)

# -----------------------------
# Simulation parameters
# -----------------------------
DAYS = 365            # one year of operations
STATIONS = [
    "Kapiri Mposhi",
    "Serenje",
    "Mpika",
    "Nakonde",
    "Tunduma",
    "Mbeya",
    "Makambako",
    "Morogoro",
    "Dar es Salaam"
]

LOCOMOTIVES = 30
WAGONS = 900

# -----------------------------
# Generate daily cargo demand
# -----------------------------
dates = pd.date_range(start="2025-01-01", periods=DAYS, freq="D")

data = []

for date in dates:
    for station in STATIONS:
        cargo_tons = np.random.randint(300, 2500)          # daily cargo
        wagons_needed = int(cargo_tons / 50)               # avg 50 tons/wagon
        congestion = np.random.uniform(0.1, 0.9)           # station congestion
        season_factor = 1 + 0.3 * np.sin(2 * np.pi * date.dayofyear / 365)

        data.append([
            date,
            station,
            int(cargo_tons * season_factor),
            wagons_needed,
            round(congestion, 2)
        ])

df_demand = pd.DataFrame(
    data,
    columns=[
        "date",
        "station",
        "cargo_tons",
        "wagons_required",
        "station_congestion"
    ]
)

# -----------------------------
# Locomotive availability
# -----------------------------
locomotive_data = []

for date in dates:
    available = np.random.randint(
        int(0.7 * LOCOMOTIVES),
        LOCOMOTIVES + 1
    )
    locomotive_data.append([date, available])

df_locomotives = pd.DataFrame(
    locomotive_data,
    columns=["date", "available_locomotives"]
)

# -----------------------------
# Wagon availability
# -----------------------------
wagon_data = []

for date in dates:
    available = np.random.randint(
        int(0.75 * WAGONS),
        WAGONS + 1
    )
    wagon_data.append([date, available])

df_wagons = pd.DataFrame(
    wagon_data,
    columns=["date", "available_wagons"]
)

# -----------------------------
# Save datasets
# -----------------------------
df_demand.to_csv("data/simulated/cargo_demand.csv", index=False)
df_locomotives.to_csv("data/simulated/locomotive_availability.csv", index=False)
df_wagons.to_csv("data/simulated/wagon_availability.csv", index=False)

print("Synthetic TAZARA datasets generated successfully!")
