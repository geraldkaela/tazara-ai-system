from predict_cargo import predict_cargo

# Realistic sample values for all 13 features
sample_input = {
    "feature1": 120,   # e.g., number of wagons
    "feature2": 350,   # e.g., distance in km
    "feature3": 8,     # e.g., average speed in km/h
    "feature4": 3,     # e.g., number of stations
    "feature5": 5,     # e.g., priority level
    "feature6": 15,    # e.g., crew size
    "feature7": 200,   # e.g., cargo weight limit
    "feature8": 1,     # e.g., maintenance flag
    "feature9": 7,     # e.g., number of stops
    "feature10": 400,  # e.g., fuel available
    "feature11": 2,    # e.g., extra load wagons
    "feature12": 6,    # e.g., weather severity
    "feature13": 10,   # e.g., time of day factor
}

predicted_cargo = predict_cargo(sample_input)
print(f"Predicted cargo tons: {predicted_cargo:.2f}")
