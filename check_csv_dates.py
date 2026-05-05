"""
Check the dates in cargo_demand.csv
"""

import pandas as pd

def check_csv_dates():
    """Check the date range in cargo_demand.csv"""
    try:
        df = pd.read_csv("data/simulated/cargo_demand.csv", parse_dates=["date"])
        
        print("CARGO DEMAND CSV DATE ANALYSIS:")
        print(f"   - Start Date: {df['date'].min()}")
        print(f"   - End Date: {df['date'].max()}")
        print(f"   - Total Records: {len(df)}")
        print(f"   - Last 5 Records:")
        
        for i in range(max(0, len(df)-5), len(df)):
            print(f"     {df.iloc[i]['date']}: {df.iloc[i]['cargo_tons']} tons")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_csv_dates()
