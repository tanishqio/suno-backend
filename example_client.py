"""
Example client script demonstrating how to use the Hearing Screening Agent API.

This simulates a Bolna integration, showing the complete flow:
1. Start test
2. Get audio and play to user (simulated)
3. Capture keypad digit (simulated)
4. Submit answer and get next audio
5. Repeat until finished
6. Retrieve final results
"""

import requests
import json
import time
from typing import Dict, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
PHONE_NUMBER = "+1234567890"
CALL_ID = "call_example_001"

# Simulate user responses (for demo)
SIMULATED_RESPONSES = {
    1: "1",  # Correct answer for first audio
    2: "5",  # Correct answer for second audio
    3: "3",  # Correct answer for third audio
    4: "4",  # Correct answer for fourth audio
    5: "7",  # Correct answer for fifth audio
}


class HearingTestClient:
    """Client for hearing screening test API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_id: Optional[str] = None
        self.current_step = 0
        self.responses = []
    
    def start_test(self, phone: str, call_id: str) -> bool:
        """Start a new hearing test."""
        print("\n" + "="*60)
        print("STARTING HEARING TEST")
        print("="*60)
        
        url = f"{self.base_url}/start-hearing-test"
        payload = {
            "phone": phone,
            "call_id": call_id
        }
        
        print(f"\nRequest: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            print(f"\nResponse: {response.status_code}")
            print(json.dumps(data, indent=2))
            
            self.test_id = data["test_id"]
            self.current_step = data["step"]
            
            # Simulate playing audio and capturing response
            self._simulate_user_response(data)
            
            return True
        
        except requests.exceptions.RequestException as e:
            print(f"\nError: {e}")
            return False
    
    def submit_answer(self, pressed_key: str) -> bool:
        """Submit a keypad answer."""
        if not self.test_id:
            print("Error: Test not started")
            return False
        
        print("\n" + "-"*60)
        print(f"SUBMITTING ANSWER (Step {self.current_step})")
        print("-"*60)
        
        url = f"{self.base_url}/submit-answer"
        payload = {
            "test_id": self.test_id,
            "pressed_key": pressed_key,
            "call_id": CALL_ID
        }
        
        print(f"\nRequest: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            print(f"\nResponse: {response.status_code}")
            print(json.dumps(data, indent=2))
            
            # Record this step
            self.responses.append({
                "step": self.current_step,
                "pressed": pressed_key,
                "correct": data.get("correct"),
                "score": data.get("current_score")
            })
            
            # Check if finished
            if data.get("is_finished"):
                print("\n" + "="*60)
                print("TEST COMPLETED")
                print("="*60)
                print(f"Final Score: {data.get('final_score')}")
                print(f"Interpretation: {data.get('interpretation')}")
                print(f"Recommendation: {data.get('recommendation')}")
                print("="*60)
                return False  # Stop loop
            
            # Update step for next iteration
            self.current_step = data.get("step", self.current_step + 1)
            
            # Simulate playing next audio and capturing response
            if data.get("next_audio_url"):
                self._simulate_user_response(data)
            
            return True
        
        except requests.exceptions.RequestException as e:
            print(f"\nError: {e}")
            return False
    
    def get_result(self) -> bool:
        """Retrieve final test results."""
        if not self.test_id:
            print("Error: Test not started")
            return False
        
        print("\n" + "="*60)
        print("RETRIEVING FINAL RESULTS")
        print("="*60)
        
        url = f"{self.base_url}/get-test-result"
        payload = {
            "test_id": self.test_id
        }
        
        print(f"\nRequest: POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            print(f"\nResponse: {response.status_code}")
            print(json.dumps(data, indent=2))
            
            return True
        
        except requests.exceptions.RequestException as e:
            print(f"\nError: {e}")
            return False
    
    def get_status(self) -> bool:
        """Check current test status."""
        if not self.test_id:
            print("Error: Test not started")
            return False
        
        print("\n" + "-"*60)
        print("CHECKING TEST STATUS")
        print("-"*60)
        
        url = f"{self.base_url}/test-status/{self.test_id}"
        
        print(f"\nRequest: GET {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            print(f"\nResponse: {response.status_code}")
            print(json.dumps(data, indent=2))
            
            return True
        
        except requests.exceptions.RequestException as e:
            print(f"\nError: {e}")
            return False
    
    def _simulate_user_response(self, data: dict):
        """Simulate playing audio and capturing user response."""
        step = data.get("step", self.current_step)
        audio_url = data.get("audio_url") or data.get("next_audio_url")
        
        print(f"\n[BOLNA SIMULATION]")
        print(f"  Playing audio: {audio_url}")
        print(f"  Instruction: {data.get('instruction')}")
        print(f"  (Audio would play to user here)")
        
        # Simulate user hearing audio and pressing a key
        if step in SIMULATED_RESPONSES:
            pressed_key = SIMULATED_RESPONSES[step]
            print(f"  User pressed: {pressed_key}")
            
            # Simulate network delay
            time.sleep(0.5)
            
            # Submit the response
            self.submit_answer(pressed_key)
    
    def run_full_test(self):
        """Run a complete test flow."""
        print("\n" + "#"*60)
        print("# HEARING SCREENING AGENT - FULL TEST SIMULATION")
        print("#"*60)
        
        # Health check
        print("\n[HEALTH CHECK]")
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            print(f"API Status: {response.json()['status']}")
        except Exception as e:
            print(f"API health check failed: {e}")
            return
        
        # Start test
        if not self.start_test(PHONE_NUMBER, CALL_ID):
            print("Failed to start test")
            return
        
        # The loop is handled by _simulate_user_response calling submit_answer
        # Check final status
        time.sleep(1)
        self.get_status()
        
        # Get final results
        time.sleep(1)
        self.get_result()
        
        print("\n" + "#"*60)
        print("# TEST COMPLETE")
        print("#"*60)


def main():
    """Main entry point."""
    client = HearingTestClient()
    
    # Run the complete test flow
    client.run_full_test()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Test ID: {client.test_id}")
    print(f"Total Steps: {client.current_step}")
    print(f"Responses: {len(client.responses)}")
    for resp in client.responses:
        status = "✓ Correct" if resp["correct"] else "✗ Incorrect"
        print(f"  Step {resp['step']}: {status} (Score: {resp['score']:.1f}%)")
    print("="*60)


if __name__ == "__main__":
    main()
