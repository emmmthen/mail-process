import requests

# 测试健康检查 API
url = 'http://localhost:8000/health'

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
