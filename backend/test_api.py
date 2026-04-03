import requests

BASE_URL = "http://localhost:8000/api"

# Login with OTP
requests.post(f"{BASE_URL}/auth/send-otp", json={"phone": "9800000000"})
res = requests.post(f"{BASE_URL}/auth/verify-otp", json={"phone": "9800000000", "otp": "123456"})
token = res.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}

profile = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
policy = requests.get(f"{BASE_URL}/policy/active", headers=headers)
triggers = requests.get(f"{BASE_URL}/triggers/active", headers=headers)
claims = requests.get(f"{BASE_URL}/v1/claims/my-claims?limit=5", headers=headers)

print("Profile:", profile.status_code, profile.text[:150])
print("Policy:", policy.status_code, policy.text[:150])
print("Triggers:", triggers.status_code, triggers.text[:150])
print("Claims:", claims.status_code, claims.text[:200])
