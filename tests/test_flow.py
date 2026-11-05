import io
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["PUBLIC_BASE_URL"] = "https://suno-test.onrender.com"

from fastapi.testclient import TestClient
from pydub import AudioSegment

from main import app

client = TestClient(app)


def start(**extra):
    response = client.post("/start-hearing-test", json={"phone": "+911234567890", "call_id": "call_1", **extra})
    assert response.status_code == 200, response.text
    return response.json()


def submit(test_id, pressed, call_id="call_1"):
    return client.post("/submit-answer", json={"test_id": test_id, "call_id": call_id, "pressed_digits": pressed})


def fetch_audio(url):
    assert url.startswith("https://suno-test.onrender.com/audio/")
    response = client.get(url.removeprefix("https://suno-test.onrender.com"))
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    return AudioSegment.from_file(io.BytesIO(response.content), format="mp3")


def test_full_session_scores_triplets_and_avoids_reused_files():
    first = start(language="hindi")
    assert first["trial"] == 1
    assert first["language"] == "hindi"
    digits = first["expected_digits"]
    assert len(digits) == 3 and len(set(digits)) == 3 and "0" not in digits
    assert len(fetch_audio(first["audio_url"])) > 1000

    test_id, expected, results = first["test_id"], digits, []
    answers = ["right", "wrong", "right", "spaced", "right", "wrong"]
    for number, answer in enumerate(answers, start=1):
        pressed = {"right": expected, "spaced": " ".join(expected), "wrong": expected[::-1]}[answer]
        body = submit(test_id, pressed).json()
        assert body["answered_trial"] == number
        assert body["correct"] is (answer != "wrong")
        results.append(body)
        if not body["is_finished"]:
            assert body["next_trial"] == number + 1
            fetch_audio(body["next_audio_url"])
            expected = body["next_expected_digits"]

    final = results[-1]
    assert final["is_finished"] and final["next_audio_url"] is None
    assert final["final_score"] == 66.7
    assert final["interpretation"] == "mild_difficulty"

    result = client.post("/get-test-result", json={"test_id": test_id}).json()
    assert result["correct_trials"] == 4 and len(result["trials"]) == 6
    files = [path for trial in result["trials"] for path in trial["files"]]
    assert len(files) == len(set(files))
    assert all(path.lower().startswith(f"{trial['digits'][i]}_hindi") for trial in result["trials"] for i, path in enumerate(trial["files"]))

    assert submit(test_id, "123").status_code == 400


def test_rejects_wrong_call_and_unknown_test():
    first = start()
    assert submit(first["test_id"], "123", call_id="other").status_code == 400
    assert submit("missing", "123").status_code == 404
    assert client.get("/audio/missing/1.mp3").status_code == 404
