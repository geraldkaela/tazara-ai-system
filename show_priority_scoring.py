"""
Show Priority Scoring Breakdown
Displays how priority scores are calculated for your orders
"""

import requests
import json

def show_priority_scoring():
    """Fetch and display priority scoring breakdown"""
    try:
        print("TAZARA Priority Scoring Breakdown")
        print("=" * 60)
        
        # Get scoring data
        response = requests.get("http://127.0.0.1:8000/priority/debug/scoring")
        data = response.json()
        
        if not data.get('success'):
            print("Failed to get scoring data")
            return
        
        print("\nSCORING EXPLANATION:")
        explanation = data['scoring_explanation']
        for key, value in explanation.items():
            print(f"  {key}: {value}")
        
        print(f"\nTOP 10 ORDERS BY PRIORITY SCORE:")
        print("-" * 60)
        
        for i, order in enumerate(data['orders'][:10], 1):
            print(f"\n#{i}. {order['customer_name']} - {order['cargo_type']}")
            print(f"   Order ID: {order['order_id']}")
            print(f"   Cargo: {order['cargo_weight']} tons")
            print(f"   Priority Level: {order['priority_level']} (from database)")
            print(f"   Final Score: {order['final_score']}/100")
            print(f"   Urgency Level: {order['urgency_level']}")
            
            print("   Score Breakdown:")
            for factor, points in order['scoring_breakdown'].items():
                if points > 0:
                    print(f"     +{points} points: {factor}")
                elif points < 0:
                    print(f"     {points} points: {factor}")
            
            total = sum(v for v in order['scoring_breakdown'].values() if v > 0)
            print(f"   Total: {total} points (capped at {order['final_score']})")
        
        print(f"\n" + "=" * 60)
        print("SCORING FORMULA:")
        print("Score = Priority Level + Deadline + Cargo Weight + Cargo Type + Route + Customer")
        print("Maximum score = 100 points")
        print("Higher score = Higher priority")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_priority_scoring()
