import pandas as pd

REQUIRED_COLUMNS = {
    "route_name",
    "distance_km",
    "cargo_tons",
    "priority"
}

def parse_routes_csv(file_path: str):
    df = pd.read_csv(file_path)

    # Validate columns
    if not REQUIRED_COLUMNS.issubset(df.columns):
        missing = REQUIRED_COLUMNS - set(df.columns)
        raise ValueError(f"Missing columns: {missing}")

    routes = []

    for _, row in df.iterrows():
        routes.append({
            "route": row["route_name"],
            "distance": float(row["distance_km"]),
            "cargo": float(row["cargo_tons"]),
            "priority": row["priority"].lower()
        })

    return routes
