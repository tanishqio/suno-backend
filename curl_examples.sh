#!/bin/bash
# Walks through one Digits-in-Noise test with curl. Needs jq.
# Usage: BASE_URL=https://your-app.onrender.com ./curl_examples.sh

BASE_URL=${BASE_URL:-http://localhost:8000}
CALL_ID="call_demo_$(date +%s)"

echo "### Start test"
RESPONSE=$(curl -s -X POST "$BASE_URL/start-hearing-test" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"+911234567890\", \"call_id\": \"$CALL_ID\", \"language\": \"hindi\"}")
echo "$RESPONSE" | jq .

TEST_ID=$(echo "$RESPONSE" | jq -r '.test_id')
AUDIO_URL=$(echo "$RESPONSE" | jq -r '.audio_url')
DIGITS=$(echo "$RESPONSE" | jq -r '.expected_digits')

echo "### Download trial audio to trial_1.mp3"
curl -s -o trial_1.mp3 "$AUDIO_URL" && ls -l trial_1.mp3

while true; do
  echo "### Submit $DIGITS"
  RESPONSE=$(curl -s -X POST "$BASE_URL/submit-answer" \
    -H "Content-Type: application/json" \
    -d "{\"test_id\": \"$TEST_ID\", \"call_id\": \"$CALL_ID\", \"pressed_digits\": \"$DIGITS\"}")
  echo "$RESPONSE" | jq .
  [ "$(echo "$RESPONSE" | jq -r '.is_finished')" = "true" ] && break
  DIGITS=$(echo "$RESPONSE" | jq -r '.next_expected_digits')
done

echo "### Final result"
curl -s -X POST "$BASE_URL/get-test-result" \
  -H "Content-Type: application/json" \
  -d "{\"test_id\": \"$TEST_ID\"}" | jq .
