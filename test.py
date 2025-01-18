import httpx
import os

BASE_URL: str = os.environ.get("MAPBOX_URL")  # type: ignore
API_KEY: str = os.environ.get("MAPBOX_KEY")  # type: ignore

client = httpx.Client(base_url=BASE_URL, params={"access_token": API_KEY})
    
req = client.get(
    "optimized-trips/v1/mapbox/driving/-122.42,37.78;-122.45,37.91;-122.48,37.73"
)

print(req.json())