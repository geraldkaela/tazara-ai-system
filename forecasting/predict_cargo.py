import joblib
import pandas as pd
import numpy as np

import os

# Global cache for lazy loading
_model = None
_scaler = None
_feature_columns = None

def _load_artifacts():
    global _model, _scaler, _feature_columns
    if _model is None:
        try:
            _model = joblib.load("models/cargo_forecast_model.pkl")
            _scaler = joblib.load("models/feature_scaler.pkl")
            _feature_columns = joblib.load("models/feature_columns.pkl")
        except Exception as e:
            # Fallback for environments without models
            print(f"⚠️ Warning: Could not load forecasting models: {e}")
            _model = "MOCK"

def predict_cargo(input_data):
    """
    Predict cargo tons from dict, DataFrame, or numpy array.
    Supports mocking via TAZARA_MOCK_FORECAST env var.
    """
    if os.environ.get("TAZARA_MOCK_FORECAST") == "1":
        return float(np.random.randint(500, 3000))

    _load_artifacts()
    
    if _model == "MOCK":
        return 1500.0  # Safe default

    # -----------------------------
    # Normalize input to DataFrame
    # -----------------------------

    # Case 1: dictionary (original design)
    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])

    # Case 2: DataFrame
    elif isinstance(input_data, pd.DataFrame):
        df = input_data.copy()

    # Case 3: NumPy array (including 3D RL output)
    else:
        arr = np.asarray(input_data)

        # Handle 3D input: (1, timesteps, features)
        if arr.ndim == 3:
            arr = arr[0, -1, :]  # last timestep

        # Handle 2D input: (timesteps, features)
        elif arr.ndim == 2:
            arr = arr[-1, :]

        # Ensure shape is (1, features)
        arr = arr.reshape(1, -1)
        df = pd.DataFrame(arr)

    # -----------------------------
    # Align with training features
    # -----------------------------
    df = df.reindex(columns=_feature_columns, fill_value=0)

    # -----------------------------
    # Scale and predict
    # -----------------------------
    X_scaled = _scaler.transform(df)
    prediction = _model.predict(X_scaled)

    return float(prediction[0])


# -----------------------------
# Standalone test
# -----------------------------
if __name__ == "__main__":
    sample_input = {
        "feature1": 10,
        "feature2": 5,
        "feature3": 2,
        "feature4": 7,
        "feature5": 3,
        "feature6": 0,
        "feature7": 4,
        "feature8": 1,
        "feature9": 6,
        "feature10": 2,
        "feature11": 8,
        "feature12": 3,
        "feature13": 5,
    }

    predicted_cargo = predict_cargo(sample_input)
    print(f"Predicted cargo tons: {predicted_cargo:.2f}")
