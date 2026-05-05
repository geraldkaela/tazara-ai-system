from forecasting.predict_cargo import predict_cargo


# Replace these with realistic sample values for all 13 features
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
