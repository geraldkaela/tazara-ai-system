import pandas as pd

# Load the Excel file
df = pd.read_excel('uploads/testAI.xlsx')

print("Original Excel file:")
print(df)
print("\nOriginal route names:", df['route'].tolist())

# Route name mapping
route_mapping = {
    'Kapiri-Mposhi–Dar-es-Salaam': 'DAR_KAPIRI',
    'Kapiri-Mposhi–Nakonde': 'DAR_MBEYA', 
    'Mpika–Kasama': 'KAPIRI_NDOLA'
}

# Apply the mapping
df['route'] = df['route'].map(route_mapping)

print("\nUpdated Excel file:")
print(df)
print("\nUpdated route names:", df['route'].tolist())

# Save the updated file
df.to_excel('uploads/testAI.xlsx', index=False)
print("\n✅ Excel file updated successfully!")
