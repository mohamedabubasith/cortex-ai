import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "admin@example.com"
PASSWORD = "admin123"

async def create_admin():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        print(f"Attempting to register {EMAIL}...")
        resp = await client.post("/auth/register", json={
            "email": EMAIL,
            "password": PASSWORD,
            "full_name": "Admin User"
        })
        if resp.status_code == 200:
            print(f"SUCCESS: Admin user created.")
            print(f"Email: {EMAIL}")
            print(f"Password: {PASSWORD}")
        elif resp.status_code == 400 and "already registered" in resp.text:
            print(f"SUCCESS: Admin user already exists.")
            print(f"Email: {EMAIL}")
            print(f"Password: {PASSWORD}")
        else:
            print(f"ERROR: Failed to create admin. Status: {resp.status_code}, Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(create_admin())
