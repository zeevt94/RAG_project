import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")

def main():
    health = requests.get(f"{BASE_URL}/health", timeout=30)
    print("HEALTH:", health.status_code, health.json())

    question = {
        "question": "Give me a short summary of the uploaded documents.",
        "top_k": 3
    }
    ask = requests.post(f"{BASE_URL}/ask", json=question, timeout=120)
    print("ASK:", ask.status_code)
    print(json.dumps(ask.json(), indent=2))

if __name__ == "__main__":
    main()
