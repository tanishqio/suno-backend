# Hearing Screening Agent API

A FastAPI backend for a voice AI hearing screening agent using **Bolna** (voice AI platform). This service runs a multi-step hearing test over phone calls, with users responding via DTMF (phone keypad).

## Features

- **Multi-step hearing test** (5 steps by default, configurable)
- **DTMF response handling** - users press phone keypad digits
- **Dynamic audio selection** - avoids repeating clips within a test
- **Automatic scoring** - calculates hearing score and interpretation
- **SQLite persistence** - stores test results and history
- **Test expiry** - automatically cleans up incomplete tests after 10 minutes
- **Comprehensive logging** - tracks all test events

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 3. View Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## How It Works

### Test Flow

```
1. Bolna initiates: POST /start-hearing-test
   ↓
   Backend returns: test_id + first audio_url
   
2. Bolna plays audio_url to user
   
3. User presses keypad digit (DTMF)
   
4. Bolna sends: POST /submit-answer with pressed_key
   ↓
   Backend validates, updates score
   
5. If test not finished:
   Backend returns: next audio_url
   → Loop back to step 2
   
6. If test finished:
   Backend returns: final_score, interpretation, recommendation
   ↓
   Bolna terminates call or retrieves: POST /get-test-result
```

## API Endpoints

### 1. Start Hearing Test

**Endpoint:** `POST /start-hearing-test`

**Request:**
```json
{
  "phone": "+1234567890",
  "call_id": "call_abc123xyz"
}
```

**Response:**
```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_url": "https://your-audio-cdn.example.com/hearing-test/number_1_noise_40db.mp3",
  "expected_key": "1",
  "instruction": "Press the number you hear on your phone keypad",
  "step": 1,
  "total_steps": 5
}
```

**Flow:**
- Creates a new test session
- Selects first audio clip
- Returns audio URL for Bolna to play
- **Note:** `expected_key` is for backend validation only, never expose to user

---

### 2. Submit Answer (Main Loop)

**Endpoint:** `POST /submit-answer`

**Request:**
```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "pressed_key": "1",
  "call_id": "call_abc123xyz"
}
```

**Response (Continue Test):**
```json
{
  "correct": true,
  "current_score": 100.0,
  "next_audio_url": "https://your-audio-cdn.example.com/hearing-test/number_5_noise_20db.mp3",
  "next_expected_key": "5",
  "instruction": "Press the number you hear on your phone keypad",
  "step": 2,
  "is_finished": false,
  "final_score": null,
  "interpretation": null,
  "recommendation": null
}
```

**Response (Test Finished):**
```json
{
  "correct": true,
  "current_score": 80.0,
  "next_audio_url": null,
  "next_expected_key": null,
  "instruction": "Test completed. Thank you for participating.",
  "step": 5,
  "is_finished": true,
  "final_score": 80.0,
  "interpretation": "mild",
  "recommendation": "Your hearing appears to be normal or have mild issues. Continue monitoring."
}
```

**Scoring Interpretation:**
- **80-100 (Mild)**: Good hearing or mild loss
- **50-79 (Moderate)**: Moderate hearing loss, consult audiologist
- **0-49 (Severe)**: Significant hearing loss, see doctor immediately

---

### 3. Get Test Result

**Endpoint:** `POST /get-test-result`

**Request:**
```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone": "+1234567890",
  "final_score": 80.0,
  "interpretation": "mild",
  "recommendation": "Your hearing appears to be normal or have mild issues. Continue monitoring.",
  "total_steps": 5,
  "correct_answers": 4,
  "answers": [
    {
      "step": 1,
      "expected": "1",
      "pressed": "1",
      "correct": true,
      "timestamp": "2024-01-15T10:30:45.123456"
    },
    {
      "step": 2,
      "expected": "5",
      "pressed": "5",
      "correct": true,
      "timestamp": "2024-01-15T10:30:50.123456"
    }
  ],
  "is_finished": true,
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:31:00.123456"
}
```

---

### 4. Get Test Status (Optional)

**Endpoint:** `GET /test-status/{test_id}`

**Response:**
```json
{
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "phone": "+1234567890",
  "current_step": 3,
  "total_steps": 5,
  "current_score": 66.67,
  "correct_answers": 2,
  "is_finished": false,
  "final_score": null,
  "interpretation": null,
  "answers": [...]
}
```

---

### 5. Delete Test (Cleanup)

**Endpoint:** `DELETE /test/{test_id}`

**Response:**
```json
{
  "status": "success",
  "message": "Test 550e8400-e29b-41d4-a716-446655440000 deleted",
  "test_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 6. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "Hearing Screening Agent API"
}
```

## Audio Files

The backend expects audio files to be hosted on a CDN or accessible URL. See [AUDIO_FILES.md](AUDIO_FILES.md) for the complete list.

### Quick Reference

| Step | Filename | Expected Key | Noise Level | Description |
|------|----------|--------------|-------------|-------------|
| 1 | number_1_noise_40db.mp3 | 1 | Low | Number 1 with low background noise |
| 2 | number_2_noise_35db.mp3 | 2 | Low | Number 2 with low background noise |
| 3 | number_3_noise_30db.mp3 | 3 | Low | Number 3 with low background noise |
| 4 | number_4_noise_25db.mp3 | 4 | Moderate | Number 4 with moderate background noise |
| 5 | number_5_noise_20db.mp3 | 5 | Moderate | Number 5 with moderate background noise |
| 6 | number_6_noise_15db.mp3 | 6 | Moderate | Number 6 with moderate background noise |
| 7 | number_7_noise_10db.mp3 | 7 | High | Number 7 with high background noise |
| 8 | number_8_noise_8db.mp3 | 8 | High | Number 8 with high background noise |
| 9 | number_9_noise_5db.mp3 | 9 | High | Number 9 with high background noise |

**To use:** Update `AUDIO_BASE_URL` in `config.py` to your CDN URL.

## Configuration

Edit `config.py` to customize:

```python
# Number of test steps
TOTAL_STEPS = 5

# Test expiry time (minutes)
TEST_EXPIRY_MINUTES = 10

# Audio CDN base URL
AUDIO_BASE_URL = "https://your-audio-cdn.example.com/hearing-test/"

# Instruction text for users
INSTRUCTION_TEXT = "Press the number you hear on your phone keypad"

# Scoring thresholds
SCORE_INTERPRETATION = {
    "mild": (80, 100),
    "moderate": (50, 79),
    "severe": (0, 49)
}
```

## Database

- **Type:** SQLite
- **File:** `hearing_tests.db` (auto-created)
- **Tables:** `hearing_tests`

### Schema

```sql
CREATE TABLE hearing_tests (
    id VARCHAR PRIMARY KEY,
    phone VARCHAR,
    call_id VARCHAR,
    current_step INTEGER,
    total_steps INTEGER,
    correct_answers INTEGER,
    final_score FLOAT,
    interpretation VARCHAR,
    recommendation VARCHAR,
    answers JSON,
    used_audio_indices JSON,
    is_finished BOOLEAN,
    created_at DATETIME,
    updated_at DATETIME
);
```

## Example Integration with Bolna

### Pseudo-code for Bolna Integration

```python
# 1. Start test
response = requests.post("http://localhost:8000/start-hearing-test", json={
    "phone": user_phone,
    "call_id": call_id
})
test_id = response["test_id"]
audio_url = response["audio_url"]

# 2. Play audio and capture DTMF
bolna.play_audio(audio_url)
pressed_digit = bolna.capture_dtmf()

# 3. Submit answer
while True:
    response = requests.post("http://localhost:8000/submit-answer", json={
        "test_id": test_id,
        "pressed_key": pressed_digit,
        "call_id": call_id
    })
    
    if response["is_finished"]:
        print(f"Score: {response['final_score']}")
        print(f"Interpretation: {response['interpretation']}")
        print(f"Recommendation: {response['recommendation']}")
        break
    
    # Play next audio
    audio_url = response["next_audio_url"]
    bolna.play_audio(audio_url)
    pressed_digit = bolna.capture_dtmf()
```

## Testing

### Using cURL

**Start Test:**
```bash
curl -X POST http://localhost:8000/start-hearing-test \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "call_id": "call_001"}'
```

**Submit Answer:**
```bash
curl -X POST http://localhost:8000/submit-answer \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "550e8400-e29b-41d4-a716-446655440000",
    "pressed_key": "1",
    "call_id": "call_001"
  }'
```

### Using Python

See `example_client.py` for a complete example.

## Logging

All events are logged to console with timestamps. Log levels:
- **INFO**: Test creation, answer submission, test completion
- **ERROR**: Validation errors, processing errors

Example logs:
```
2024-01-15 10:30:00 - __main__ - INFO - Starting hearing test for phone: +1234567890, call_id: call_001
2024-01-15 10:30:00 - __main__ - INFO - Created hearing test 550e8400-e29b-41d4-a716-446655440000 for phone +1234567890
2024-01-15 10:30:05 - __main__ - INFO - Answer submitted for test 550e8400-e29b-41d4-a716-446655440000, step 1: expected=1, pressed=1, correct=True
2024-01-15 10:31:00 - __main__ - INFO - Test 550e8400-e29b-41d4-a716-446655440000 finished. Score: 80.0, Interpretation: mild
```

## Deployment

### Using Gunicorn (Production)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t hearing-screening-api .
docker run -p 8000:8000 hearing-screening-api
```

## Troubleshooting

### Test not found error

- Ensure `test_id` is correct
- Check if test has expired (> 10 minutes old)
- Verify call_id matches the one used in `/start-hearing-test`

### Audio URL not accessible

- Update `AUDIO_BASE_URL` in `config.py`
- Ensure audio files are publicly accessible
- Check CDN/hosting configuration

### Database locked error

- Close any other connections to `hearing_tests.db`
- Restart the application

## Project Structure

```
.
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic request/response models
├── services.py          # Business logic
├── config.py            # Configuration and audio clips
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── AUDIO_FILES.md       # Audio file documentation
├── .env.example         # Environment variables template
└── hearing_tests.db     # SQLite database (auto-created)
```

## License

MIT

## Support

For issues or questions, refer to the API documentation at `/docs` after starting the server.
