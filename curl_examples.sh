#!/bin/bash
# cURL examples for testing the Hearing Screening Agent API
# Copy and paste these commands into your terminal

echo "=== Hearing Screening Agent API - cURL Examples ==="
echo ""
echo "Make sure the server is running: python main.py"
echo ""

# Health check
echo "### 1. Health Check ###"
echo "curl -X GET http://localhost:8000/health"
echo ""

# Start hearing test
echo "### 2. Start Hearing Test ###"
TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/start-hearing-test \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "call_id": "call_demo_001"
  }')
echo "curl -X POST http://localhost:8000/start-hearing-test \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{'"
echo "    \"phone\": \"+1234567890\","
echo "    \"call_id\": \"call_demo_001\""
echo "  }'"
echo ""
echo "Response:"
echo "$TEST_RESPONSE" | jq .
echo ""

# Extract test_id from response
TEST_ID=$(echo "$TEST_RESPONSE" | jq -r '.test_id')
echo "Extracted test_id: $TEST_ID"
echo ""

# Get test status
echo "### 3. Get Test Status ###"
echo "curl -X GET http://localhost:8000/test-status/$TEST_ID"
curl -s -X GET "http://localhost:8000/test-status/$TEST_ID" | jq .
echo ""

# Submit answer (correct)
echo "### 4. Submit Answer (Correct) ###"
SUBMIT_RESPONSE=$(curl -s -X POST http://localhost:8000/submit-answer \
  -H "Content-Type: application/json" \
  -d "{
    \"test_id\": \"$TEST_ID\",
    \"pressed_key\": \"1\",
    \"call_id\": \"call_demo_001\"
  }")
echo "curl -X POST http://localhost:8000/submit-answer \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{'"
echo "    \"test_id\": \"$TEST_ID\","
echo "    \"pressed_key\": \"1\","
echo "    \"call_id\": \"call_demo_001\""
echo "  }'"
echo ""
echo "Response:"
echo "$SUBMIT_RESPONSE" | jq .
echo ""

# Submit answer (incorrect)
echo "### 5. Submit Answer (Incorrect) ###"
SUBMIT_RESPONSE=$(curl -s -X POST http://localhost:8000/submit-answer \
  -H "Content-Type: application/json" \
  -d "{
    \"test_id\": \"$TEST_ID\",
    \"pressed_key\": \"9\",
    \"call_id\": \"call_demo_001\"
  }")
echo "curl -X POST http://localhost:8000/submit-answer \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{'"
echo "    \"test_id\": \"$TEST_ID\","
echo "    \"pressed_key\": \"9\","
echo "    \"call_id\": \"call_demo_001\""
echo "  }'"
echo ""
echo "Response:"
echo "$SUBMIT_RESPONSE" | jq .
echo ""

# Continue with more answers to complete the test
echo "### 6. Continue Submitting Answers to Complete Test ###"
for i in {3..5}; do
    echo "Step $i - Submitting answer..."
    SUBMIT_RESPONSE=$(curl -s -X POST http://localhost:8000/submit-answer \
      -H "Content-Type: application/json" \
      -d "{
        \"test_id\": \"$TEST_ID\",
        \"pressed_key\": \"$i\",
        \"call_id\": \"call_demo_001\"
      }")
    
    IS_FINISHED=$(echo "$SUBMIT_RESPONSE" | jq -r '.is_finished')
    SCORE=$(echo "$SUBMIT_RESPONSE" | jq -r '.current_score')
    echo "  Finished: $IS_FINISHED, Score: $SCORE%"
    echo ""
    
    if [ "$IS_FINISHED" = "true" ]; then
        echo "Test completed!"
        break
    fi
done

echo ""

# Get final result
echo "### 7. Get Final Test Result ###"
echo "curl -X POST http://localhost:8000/get-test-result \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{'"
echo "    \"test_id\": \"$TEST_ID\""
echo "  }'"
echo ""
echo "Response:"
curl -s -X POST http://localhost:8000/get-test-result \
  -H "Content-Type: application/json" \
  -d "{
    \"test_id\": \"$TEST_ID\"
  }" | jq .
echo ""

# Delete test (cleanup)
echo "### 8. Delete Test (Cleanup) ###"
echo "curl -X DELETE http://localhost:8000/test/$TEST_ID"
curl -s -X DELETE "http://localhost:8000/test/$TEST_ID" | jq .
echo ""

echo "=== Test Complete ==="
