#!/usr/bin/env python3
"""
Test the regex pattern for parsing order text
"""

import re

def test_order_parsing():
    """Test the regex patterns for parsing order text"""
    
    test_orders = [
        "Tanzania Export Ltd - 300.00 tons (Dar es Salaam → Mbeya)",
        "Mining Corp Zambia - 500.00 tons (Dar es Salaam → Kapiri Mposhi)",
        "Test Customer - 500.00 tons (Dar es Salaam → Kapiri Mposhi)"
    ]
    
    print("TESTING ORDER PARSING REGEX")
    print("=" * 50)
    
    for order_text in test_orders:
        print(f"\nOrder: {order_text}")
        
        # Test weight regex
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*tons', order_text)
        if weight_match:
            weight = float(weight_match.group(1))
            print(f"  ✅ Weight: {weight} tons")
        else:
            print(f"  ❌ Weight not found")
        
        # Test stations regex
        stations_match = re.search(r'\((.+?)\s*→\s*(.+?)\)', order_text)
        if stations_match:
            origin = stations_match.group(1).strip()
            destination = stations_match.group(2).strip()
            print(f"  ✅ Origin: {origin}")
            print(f"  ✅ Destination: {destination}")
        else:
            print(f"  ❌ Stations not found")
        
        # Test route mapping
        route_map = {
            'Dar es Salaam-Kapiri Mposhi': 'DarKapiri',
            'Dar es Salaam-Mbeya': 'DarMbeya',
            'Mbeya-Kasama': 'MbeyaKasama',
            'Kapiri Mposhi-Ndola': 'KapiriNdola',
            'Dar es Salaam-Kidatu': 'DarKidatu',
            'Kidatu': 'KidatuTrans'
        }
        
        if stations_match:
            origin = stations_match.group(1).strip()
            destination = stations_match.group(2).strip()
            
            # Try both directions
            key1 = f"{origin}-{destination}"
            key2 = f"{destination}-{origin}"
            
            route_key = route_map.get(key1) or route_map.get(key2)
            if route_key:
                print(f"  ✅ Route: {route_key}")
            else:
                print(f"  ❌ Route not mapped: {key1} or {key2}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_order_parsing()
