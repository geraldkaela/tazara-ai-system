"""
Clear all authentication tokens for testing
"""

def clear_test_tokens():
    """Clear any existing tokens to test fresh authentication"""
    print("🧹 Clearing test authentication tokens...")
    
    # Instructions for manual clearing
    print("Please clear your browser localStorage:")
    print("1. Open browser Developer Tools (F12)")
    print("2. Go to Console tab")
    print("3. Run: localStorage.clear()")
    print("4. Refresh the page")
    
    print("\nOr clear specific tokens:")
    print("localStorage.removeItem('access_token')")
    print("localStorage.removeItem('token_type')")
    print("localStorage.removeItem('expires_in')")

if __name__ == "__main__":
    clear_test_tokens()
