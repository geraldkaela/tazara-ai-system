import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xlsx")


def parse_schedule_file(file_path: str):
    """
    Reads CSV or Excel and returns structured route data
    """
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")

    required_cols = {"route", "cargo", "priority"}
    if not required_cols.issubset(df.columns):
        raise ValueError("Missing required columns: route, cargo, priority")

    routes = []
    for _, row in df.iterrows():
        routes.append({
            "route": row["route"],
            "cargo": int(row["cargo"]),
            "priority": row["priority"]
        })

    return routes
