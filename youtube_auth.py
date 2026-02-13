"""One-time script to authorize YouTube uploads. Run: python youtube_auth.py"""
from google_auth_oauthlib.flow import InstalledAppFlow
import json

flow = InstalledAppFlow.from_client_secrets_file(
    "growth/client_secrets.json",
    scopes=["https://www.googleapis.com/auth/youtube.upload"]
)
creds = flow.run_local_server(port=8090)

with open("growth/youtube_credentials.json", "w") as f:
    json.dump({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "token_uri": creds.token_uri
    }, f)

print("Saved credentials to growth/youtube_credentials.json!")
