#!/usr/bin/env python3
"""
Create a sample Excel file for testing the upload functionality
"""

import pandas as pd

def create_sample_excel():
    # Create sample data
    sample_data = {
        'Route': ['DAR_KAPIRI', 'DAR_MBEYA', 'KAPIRI_NDOLA', 'DAR_KAPIRI', 'DAR_MBEYA'],
        'Cargo_Tons': [1200, 800, 600, 1500, 900],
        'Trains': [8, 6, 4, 10, 7],
        'Days': [14, 14, 14, 21, 14]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Save to Excel
    df.to_excel('sample_tazara_schedules.xlsx', index=False)
    print("✅ Sample Excel file created: sample_tazara_schedules.xlsx")
    print("\n📊 Sample data:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    create_sample_excel()
