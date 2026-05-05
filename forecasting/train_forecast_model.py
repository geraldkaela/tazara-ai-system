import joblib
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

from forecasting.data_loader import load_and_prepare_data


def train_model():
    X, y, scaler, feature_columns = load_and_prepare_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    models_to_train = {
        "rf": RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1),
        "gbm": HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1, max_depth=5, random_state=42)
    }

    results = {}

    for name, model in models_to_train.items():
        print(f"🌲 Training {name.upper()} model...")
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        results[name] = {"model": model, "mae": mae, "rmse": rmse}
        print(f"   {name.upper()} - MAE: {mae:.2f}, RMSE: {rmse:.2f}")

    # Save artifacts
    joblib.dump(results["rf"]["model"], "models/cargo_forecast_model.pkl")
    joblib.dump(results["gbm"]["model"], "models/cargo_forecast_gbm.pkl")
    joblib.dump(scaler, "models/feature_scaler.pkl")
    joblib.dump(feature_columns, "models/feature_columns.pkl")

    # Save metrics for model registry sync
    metrics = {
        "rf": {"mae": results["rf"]["mae"], "rmse": results["rf"]["rmse"], "model_path": "models/cargo_forecast_model.pkl"},
        "gbm": {"mae": results["gbm"]["mae"], "rmse": results["gbm"]["rmse"], "model_path": "models/cargo_forecast_gbm.pkl"}
    }
    with open("metrics/training_metrics.json", "w") as f:
        import json
        json.dump(metrics, f, indent=2)

    print("Models and artifacts saved successfully.")


if __name__ == "__main__":
    train_model()
