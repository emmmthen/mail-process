import requests
import os

# 测试邮件导入 API
url = 'http://localhost:8000/api/emails/import'
file_path = 'c:\\Users\\123\\Desktop\\AI-coding\\test-email.html'

# 准备文件数据
with open(file_path, 'rb') as f:
    files = {
        'file': (os.path.basename(file_path), f),
        'process_type': (None, 'auto')
    }

    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
