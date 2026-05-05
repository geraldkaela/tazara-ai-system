import requests

url = "http://127.0.0.1:8000/upload/"
file_path = "uploads/testAI.xlsx"

try:
    with open(file_path, "rb") as f:
        files = {"file": ("testAI.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        headers = {"accept": "application/json"}
        
        response = requests.post(url, files=files, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"Routes detected: {data['routes_detected']}")
            print(f"Routes used: {data['routes_used']}")
            print(f"Ignored routes: {data['evaluation']['ignored_routes']}")
        
except Exception as e:
    print(f"Error: {e}")
