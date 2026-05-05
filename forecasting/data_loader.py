import pandas as pd
from sklearn.preprocessing import StandardScaler

DATA_PATH = "data/simulated/cargo_demand.csv"

def load_and_prepare_data():
    # Load dataset
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])

    # Feature engineering
    df["day"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear

    # Encode stations if present
    if "station" in df.columns:
        df = pd.get_dummies(df, columns=["station"], drop_first=True)

    # Features and target
    X = df.drop(columns=["date", "cargo_tons"])
    y = df["cargo_tons"]

    # Scale numerical features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler, X.columns
