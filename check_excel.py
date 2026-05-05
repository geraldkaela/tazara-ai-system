import pandas as pd
from api.utils.data_parser import parse_schedule_file
from reinforcement_rl.routes import ROUTES

# Read the Excel file directly
df = pd.read_excel('uploads/testAI.xlsx')
print("Excel file contents:")
print(df)
print("\nColumns:", df.columns.tolist())
print("\nRoute values from Excel:", df['route'].tolist())

# Parse using the parser
parsed_routes = parse_schedule_file('uploads/testAI.xlsx')
print("\nParsed routes:")
for route in parsed_routes:
    print(f"  {route}")

# Show expected route names
print("\nExpected route names in RL environment:")
print(list(ROUTES.keys()))

# Show comparison
print("\nComparison:")
excel_routes = [r['route'] for r in parsed_routes]
expected_routes = list(ROUTES.keys())

print(f"Excel routes: {excel_routes}")
print(f"Expected routes: {expected_routes}")
print(f"Ignored routes: {set(excel_routes) - set(expected_routes)}")
