# Suno Care Digits-in-Noise API

FastAPI backend for the Suno Care Digits-in-Noise hearing screening test. Bolna plays three noisy spoken digits per trial, the caller types them on the keypad (DTMF), and the backend scores each trial and returns the next one until the test ends.

## Flow

1. **`POST /start-hearing-test`** creates a test id, picks 3 different random digits from 1–9, and picks one random noisy recording for each. It merges them into one MP3 and stores the correct answer on the server, then returns the test id, an absolute audio URL, the expected digits, the instruction, and the trial number.
2. Bolna plays `audio_url` and collects the three keypresses.
3. **`POST /submit-answer`** compares the pressed digits with the stored answer. A trial is correct only when all three digits match in order. If more trials follow, the response carries a fresh triplet with fresh recordings. Otherwise it carries the final score and interpretation.

Within one test a recording is never reused, and all trials use one language (`hindi` or `english`, random unless the start request sets it).

### Start

```json
POST /start-hearing-test
{"phone": "+911234567890", "call_id": "bolna_call_123", "language": "hindi"}

{
  "test_id": "8c0e…",
  "trial": 1,
  "total_trials": 6,
  "audio_url": "https://your-app.onrender.com/audio/8c0e…/1.mp3",
  "expected_digits": "695",
  "instruction": "Listen to the three numbers and press them on your phone keypad in the same order.",
  "language": "hindi"
}
```

### Submit

`pressed_digits` accepts `"695"`, `"6 9 5"` or `"6,9,5"`; anything that isn't a digit is ignored.

```json
POST /submit-answer
{"test_id": "8c0e…", "call_id": "bolna_call_123", "pressed_digits": "695"}

{
  "test_id": "8c0e…",
  "answered_trial": 1,
  "correct": true,
  "correct_trials": 1,
  "trials_completed": 1,
  "total_trials": 6,
  "is_finished": false,
  "instruction": "Listen to the three numbers …",
  "next_trial": 2,
  "next_audio_url": "https://your-app.onrender.com/audio/8c0e…/2.mp3",
  "next_expected_digits": "214",
  "final_score": null,
  "interpretation": null,
  "recommendation": null
}
```

On the last trial `is_finished` is `true`, the `next_*` fields are `null`, and `final_score` (percent of trials correct), `interpretation` and `recommendation` are set:

| Score | `interpretation` |
|---|---|
| ≥ 80% | `good` |
| 50–79% | `mild_difficulty` |
| < 50% | `needs_doctor` |

### Other endpoints

- `GET /audio/{test_id}/{trial}.mp3` returns the merged trial audio (also answers `HEAD`).
- `POST /get-test-result` with `{"test_id": …}` returns the final result with per-trial history.
- `GET /test-status/{test_id}` returns live state.
- `DELETE /test/{test_id}` deletes a test and its audio.
- `GET /health` is a health check.

Interactive docs are at `/docs`.

## Audio

Recordings live in `noisy_audio(1to10)/{digit}_{Hindi|IndianEnglish}/{Female|Male|Unspecified}/*.wav`. At startup the backend indexes digits 1–9 for both languages, and startup fails if any digit has no files. Folders for 10 are ignored, because 10 can't be typed as one keypress.

For each trial, every clip is converted to mono, trimmed of leading and trailing silence, and normalized to the same loudness. The clips are then joined with short gaps into a 64 kbps MP3 (about 3–7 seconds). The MP3 is built once when the trial starts and stored in the database, so fetching it is instant. A few recordings in the dataset can't be decoded; those are skipped, and another recording of the same digit is used.

## Configuration

Settings are in `config.py`: number of trials, score bands, instruction text, and audio processing. Environment variables:

| Variable | Purpose |
|---|---|
| `PUBLIC_BASE_URL` | Base for the absolute audio URLs, e.g. `https://your-app.onrender.com`. On Render it falls back to `RENDER_EXTERNAL_URL`, which Render sets automatically. Otherwise the request's host is used. |
| `DATABASE_URL` | SQLAlchemy URL, default `sqlite:///./hearing_tests.db`. Point it at Postgres to keep results across restarts. |

The number of trials comes from `HearingTestService.should_continue` in `services.py`, which currently stops after `TOTAL_TRIALS` (6). Replace that function to change the rule.

Unfinished tests idle for more than 10 minutes, and audio older than that, are deleted automatically.

## Running locally

Requires ffmpeg (`brew install ffmpeg` / `apt install ffmpeg`).

```bash
pip install -r requirements-dev.txt
uvicorn main:app --reload
pytest
python example_client.py            # simulated Bolna session
./curl_examples.sh                  # same flow with curl
```

## Deploying to Render

The repo includes a `Dockerfile` that installs ffmpeg, plus a `render.yaml` blueprint. Create a **Web Service** from the repo with the Docker runtime (or use the Blueprint). No build or start command is needed. Render sets `PORT` and `RENDER_EXTERNAL_URL`, so audio URLs come out as `https://<service>.onrender.com/audio/...` without extra configuration.

Render's disk is temporary: with the default SQLite database, tests and results are lost on each deploy or restart. Live tests are unaffected unless a restart happens mid-call. Set `DATABASE_URL` to a Render Postgres instance to keep results.
