## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Phone Call)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ (DTMF - phone keypad)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     BOLNA PLATFORM                               │
│  (Voice AI orchestrator - plays audio, captures DTMF)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   /start-       /submit-answer      /get-test-result
   hearing-test                       

┌─────────────────────────────────────────────────────────────────┐
│               FASTAPI Backend (main.py)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Endpoints:                                               │  │
│  │ • POST /start-hearing-test                               │  │
│  │ • POST /submit-answer                                    │  │
│  │ • POST /get-test-result                                  │  │
│  │ • GET /test-status/{test_id}                             │  │
│  │ • DELETE /test/{test_id}                                 │  │
│  │ • GET /health                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Services Layer (services.py)                             │  │
│  │ ┌────────────────────────────────────────────────────┐  │  │
│  │ │ HearingTestService:                                │  │  │
│  │ │ • create_test()                                    │  │  │
│  │ │ • submit_answer()                                  │  │  │
│  │ │ • get_test_result()                                │  │  │
│  │ │ • _get_next_audio_clip()                           │  │  │
│  │ │ • _get_interpretation()                            │  │  │
│  │ │ • cleanup_expired_tests()                          │  │  │
│  │ └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Models Layer (models.py)                                 │  │
│  │ ┌────────────────────────────────────────────────────┐  │  │
│  │ │ SQLAlchemy ORM:                                    │  │  │
│  │ │ • HearingTest (main model)                         │  │  │
│  │ │ • AudioClip (audio storage)                        │  │  │
│  │ │ • TestResponse (response tracking)                 │  │  │
│  │ └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│          NEON PostgreSQL Database (Cloud)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Tables:                                                  │  │
│  │ • hearing_tests                                          │  │
│  │ • audio_clips                                            │  │
│  │ • test_responses                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table 1: `audio_clips`
Stores all audio files with their metadata. Each row represents one audio clip.

```sql
CREATE TABLE audio_clips (
    id SERIAL PRIMARY KEY,
    clip_index INTEGER NOT NULL UNIQUE,           -- 1-9 for digits
    filename VARCHAR(255) NOT NULL,               -- e.g., "number_1_noise_40db.mp3"
    audio_url VARCHAR(500) NOT NULL,              -- Full CDN URL
    expected_key VARCHAR(1) NOT NULL,             -- Expected digit (1-9)
    noise_level VARCHAR(50),                      -- "low", "moderate", "high"
    description TEXT,                             -- Description of the audio
    snr_db INTEGER,                               -- Signal-to-Noise Ratio in dB
    duration_seconds FLOAT,                       -- Audio duration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Example data:**
```
id | clip_index | filename                      | audio_url                                              | expected_key | noise_level | snr_db
---|------------|-------------------------------|------------------------------------------------------|--------------|-------------|-------
1  | 1          | number_1_noise_40db.mp3      | https://cdn.com/hearing-test/number_1_noise_40db.mp3 | 1            | low         | 40
2  | 2          | number_2_noise_35db.mp3      | https://cdn.com/hearing-test/number_2_noise_35db.mp3 | 2            | low         | 35
3  | 3          | number_3_noise_30db.mp3      | https://cdn.com/hearing-test/number_3_noise_30db.mp3 | 3            | low         | 30
```

### Table 2: `hearing_tests`
Main table storing test sessions and their state.

```sql
CREATE TABLE hearing_tests (
    id UUID PRIMARY KEY,                          -- test_id
    phone VARCHAR(20) NOT NULL,                   -- User's phone number
    call_id VARCHAR(100) NOT NULL UNIQUE,         -- Bolna call ID
    current_step INTEGER DEFAULT 0,               -- Current step (0-5)
    total_steps INTEGER DEFAULT 5,                -- Total steps in test
    correct_answers INTEGER DEFAULT 0,            -- Number of correct answers
    final_score FLOAT NULL,                       -- Final score (0-100)
    interpretation VARCHAR(50) NULL,              -- "mild", "moderate", "severe"
    recommendation TEXT NULL,                     -- Medical recommendation
    is_finished BOOLEAN DEFAULT FALSE,            -- Test completion status
    used_audio_indices INTEGER[] DEFAULT ARRAY[]::INTEGER[],  -- Used clip IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Example data:**
```
id                                   | phone       | call_id      | current_step | total_steps | correct_answers | final_score | interpretation
-------------------------------------|-------------|--------------|--------------|------------|-----------------|-------------|---------------
550e8400-e29b-41d4-a716-446655440000 | +1234567890 | call_demo_001| 5            | 5          | 4               | 80.0        | mild
```

### Table 3: `test_responses`
Stores individual responses for each step of a test.

```sql
CREATE TABLE test_responses (
    id SERIAL PRIMARY KEY,
    test_id UUID NOT NULL,                        -- Foreign key to hearing_tests
    step INTEGER NOT NULL,                        -- Step number (1-5)
    audio_clip_id INTEGER NOT NULL,               -- Foreign key to audio_clips
    expected_key VARCHAR(1) NOT NULL,             -- Expected answer
    pressed_key VARCHAR(1) NOT NULL,              -- User's answer
    is_correct BOOLEAN NOT NULL,                  -- Correctness
    response_time_seconds FLOAT,                  -- Time to respond
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES hearing_tests(id) ON DELETE CASCADE,
    FOREIGN KEY (audio_clip_id) REFERENCES audio_clips(id)
);
```

**Example data:**
```
id | test_id                              | step | audio_clip_id | expected_key | pressed_key | is_correct | response_time_seconds
---|--------------------------------------|------|---------------|--------------|-------------|------------|----------------------
1  | 550e8400-e29b-41d4-a716-446655440000 | 1    | 1             | 1            | 1           | true       | 2.5
2  | 550e8400-e29b-41d4-a716-446655440000 | 2    | 5             | 5            | 5           | true       | 3.1
3  | 550e8400-e29b-41d4-a716-446655440000 | 3    | 3             | 3            | 9           | false      | 2.8
```

---

## Project Structure

```
hearing-screening-api/
├── main.py                 # FastAPI application & endpoints
├── models.py               # SQLAlchemy ORM models (Neon PostgreSQL)
├── schemas.py              # Pydantic request/response schemas
├── services.py             # Business logic layer
├── config.py               # Configuration & constants
├── requirements.txt        # Python dependencies
├── ARCHITECTURE.md         # This file
├── README.md               # User guide
├── DEPLOYMENT.md           # Deployment instructions
├── AUDIO_FILES.md          # Audio documentation
├── curl_examples.sh        # Example API calls
├── example_client.py       # Python client example
└── .env.example            # Environment variables template
```

---

## File-by-File Explanation

### 1. **models.py** - Database Models
**Purpose:** Defines SQLAlchemy ORM models for Neon PostgreSQL

**Key Components:**
- `AudioClip` - Stores audio file metadata and URLs
- `HearingTest` - Main test session model
- `TestResponse` - Individual response tracking
- `get_db()` - Database session dependency

**Database Connection:**
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db.neon.tech/dbname")
engine = create_engine(DATABASE_URL)
```

**Responsibilities:**
- Define table structures
- Handle relationships between tables
- Provide ORM methods for querying
- Auto-create tables on startup

---

### 2. **schemas.py** - Request/Response Models
**Purpose:** Pydantic models for API validation

**Key Classes:**
- `StartHearingTestRequest` - Input: phone, call_id
- `StartHearingTestResponse` - Output: test_id, audio_url, etc.
- `SubmitAnswerRequest` - Input: test_id, pressed_key, call_id
- `SubmitAnswerResponse` - Output: correct, score, next audio, etc.
- `GetTestResultRequest` - Input: test_id
- `GetTestResultResponse` - Output: final results
- `ErrorResponse` - Standard error format

**Responsibilities:**
- Validate incoming requests
- Define response structure
- Auto-generate API documentation
- Type checking

---

### 3. **config.py** - Configuration
**Purpose:** Centralized configuration and constants

**Key Variables:**
- `AUDIO_CLIPS` - Dictionary of all audio files (moved to DB in updated version)
- `TOTAL_STEPS` - Number of test steps (default: 5)
- `TEST_EXPIRY_MINUTES` - Auto-cleanup timeout (default: 10)
- `SCORE_INTERPRETATION` - Score ranges for mild/moderate/severe
- `RECOMMENDATIONS` - Medical recommendations by interpretation

**Responsibilities:**
- Store all constants
- Define scoring thresholds
- Configure test parameters
- Provide recommendation text

---

### 4. **services.py** - Business Logic
**Purpose:** Core logic for test management

**Key Methods:**

#### `HearingTestService.create_test(db, phone, call_id)`
- Creates new test record in `hearing_tests` table
- Generates UUID for test_id
- Initializes score tracking
- Returns test object

**Flow:**
```
1. Generate UUID for test_id
2. Create HearingTest record in DB
3. Commit to database
4. Return test object
```

#### `HearingTestService._get_next_audio_clip(db, test)`
- Queries `audio_clips` table
- Selects random unused clip
- Marks clip as used
- Updates `hearing_tests.used_audio_indices`
- Returns audio URL and expected key

**Flow:**
```
1. Get used_audio_indices from test
2. Query available clips from audio_clips table
3. Random select one
4. Update used_audio_indices
5. Return clip with full URL from DB
```

#### `HearingTestService.submit_answer(db, test_id, pressed_key, call_id)`
- Retrieves test from database
- Validates call_id matches
- Queries audio_clips for expected key
- Compares pressed_key with expected_key
- Creates TestResponse record
- Updates score
- Decides if test finished

**Flow:**
```
1. Get test from hearing_tests by test_id
2. Validate test not finished
3. Get expected key from last audio_clip used
4. Compare pressed_key == expected_key
5. Insert row in test_responses table
6. Update correct_answers count
7. If finished: calculate final_score, interpretation, recommendation
8. Return result with next audio (or null if finished)
```

#### `HearingTestService.get_test_result(db, test_id)`
- Retrieves completed test
- Gets all test_responses
- Formats final result
- Returns JSON response

**Flow:**
```
1. Query hearing_tests by test_id
2. Query test_responses for this test
3. Verify is_finished == true
4. Format all data as dictionary
5. Return complete test results
```

---

### 5. **main.py** - FastAPI Application
**Purpose:** API endpoints and request handling

**Key Endpoints:**

#### `POST /start-hearing-test`
**Request:**
```json
{
  "phone": "+1234567890",
  "call_id": "call_abc123"
}
```

**Process:**
1. Call `HearingTestService.create_test()`
2. Get first audio from `audio_clips` table
3. Return audio_url, test_id, instruction

**Response:**
```json
{
  "