import sys
import os
import asyncio
import httpx
from urllib.parse import urlencode

# Ensure backend module is found
current_dir = os.getcwd()
if current_dir.endswith("scripts"):
    sys.path.append(os.path.join(current_dir, ".."))
    sys.path.append(os.path.join(current_dir, "..", "..")) # project root
else:
    sys.path.append(os.path.join(current_dir, "backend"))

try:
    from app.core.config import settings
except ImportError:
    # Try alternate path if running from root
    sys.path.append(os.getcwd())
    from backend.app.core.config import settings

async def verify():
    print("\n--- 🕵️‍♂️ Verifying Google Sign-In Configuration ---")
    
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    
    # 1. Check Credentials Load
    if not client_id:
        print("❌ Error: GOOGLE_CLIENT_ID is missing in settings/env.")
        return
    if not client_secret:
        print("❌ Error: GOOGLE_CLIENT_SECRET is missing in settings/env.")
        return

    print(f"✅ Credentials Loaded:")
    print(f"   - Client ID: {client_id[:15]}...{client_id[-5:]}")
    print(f"   - Secret:    {'*' * 10}{client_secret[-5:]}")
    print(f"   - Redirect:  {settings.FRONTEND_URL}/auth/google/callback")

    # 2. Simulate Backend URL Generation
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": f"{settings.FRONTEND_URL}/auth/google/callback",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    print(f"\n🔗 Generated Auth URL:\n{auth_url}")

    # 3. Test Connectivity
    print("\n🌍 Testing Connectivity to Google...")
    async with httpx.AsyncClient() as client:
        try:
            # We follow redirects to see if we land on the actual login page or an error page
            # Actually, Google Auth URL is the page itself, so just getting it should work.
            response = await client.get(auth_url, follow_redirects=True)
            
            if response.status_code == 200:
                print("✅ Success! Google returned 200 OK.")
                print("   The Client ID and Redirect URI formatting appears correct.")
                print("   (Note: If the Redirect URI is not whitelisted in Google Cloud Console, you might see a 400 error on the page content, but the request itself succeeds).")
                
                if "Error 400: redirect_uri_mismatch" in response.text:
                     print("\n⚠️ WARNING: Google reported 'redirect_uri_mismatch'.")
                     print(f"   Please ensure '{settings.FRONTEND_URL}/auth/google/callback' is added to Authorized Redirect URIs in Google Cloud Console.")
                elif "Error 401: invalid_client" in response.text:
                     print("\n⚠️ WARNING: Google reported 'invalid_client'. Check your Client ID.")
                else:
                     print("   Page content looks roughly like a login page.")
            else:
                print(f"⚠️ Warning: Google returned status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
