import requests
import time
from datetime import datetime
import os

HEALTH_SERVICE = os.environ["HEALTH_SERVICE"]
HEALTH_URL = f"http://{HEALTH_SERVICE}/health"


def check_health():
    while True:
        try:
            response = requests.get(HEALTH_URL, timeout=2)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if response.status_code == 200:
                print(
                    f"[{timestamp}] ✓ SUCCESS - Health check passed: {response.json()}"
                )
            else:
                print(f"[{timestamp}] ✗ FAILURE - Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] ✗ FAILURE - Error: {str(e)}")

        time.sleep(1)


if __name__ == "__main__":
    print(f"Starting health checker against {HEALTH_SERVICE}...")
    check_health()
