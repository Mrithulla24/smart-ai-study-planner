import requests


url = "http://127.0.0.1:5000/api/generate-study-plan/1"

response = requests.post(url)

print("Status Code:", response.status_code)
print("Response:", response.json())