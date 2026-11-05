"""
Simulates Bolna running one Digits-in-Noise test against the API.

Usage: python example_client.py [base_url]
"""
import random
import sys

import requests

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
CALL_ID = f"call_example_{random.randint(1000, 9999)}"


def simulated_keypress(expected: str) -> str:
    """Answer correctly most of the time, like a listener with mild difficulty."""
    return expected if random.random() < 0.7 else "".join(random.sample("123456789", 3))


def main():
    trial = requests.post(f"{BASE_URL}/start-hearing-test", json={"phone": "+911234567890", "call_id": CALL_ID}).json()
    test_id = trial["test_id"]
    print(f"Test {test_id} in {trial['language']}: {trial['instruction']}")

    audio_url, expected, number = trial["audio_url"], trial["expected_digits"], trial["trial"]
    while True:
        size = len(requests.get(audio_url).content)
        pressed = simulated_keypress(expected)
        result = requests.post(f"{BASE_URL}/submit-answer", json={
            "test_id": test_id, "call_id": CALL_ID, "pressed_digits": pressed
        }).json()
        print(f"Trial {number}: played {size} bytes, expected {expected}, pressed {pressed}, correct={result['correct']}")
        if result["is_finished"]:
            break
        audio_url, expected, number = result["next_audio_url"], result["next_expected_digits"], result["next_trial"]

    print(f"Score {result['final_score']}% -> {result['interpretation']}: {result['recommendation']}")


if __name__ == "__main__":
    main()
