"""
Configuration for the Digits-in-Noise hearing screening test.
"""
import os
from pathlib import Path

AUDIO_DIR = Path(__file__).parent / "noisy_audio(1to10)"
DIGITS = list(range(1, 10))
DIGITS_PER_TRIAL = 3
LANGUAGES = ["hindi", "english"]

TOTAL_TRIALS = 6
TEST_EXPIRY_MINUTES = 10

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hearing_tests.db")

SAMPLE_RATE = 22050
TARGET_DBFS = -20.0
SILENCE_DROP_DB = 16.0
LEAD_IN_MS = 300
GAP_MS = 500
MP3_BITRATE = "64k"

INSTRUCTION_TEXT = "Listen to the three numbers and press them on your phone keypad in the same order."
FINISHED_TEXT = "Test completed. Thank you for participating."

SCORE_BANDS = [
    (80, "good", "Your hearing in noise looks good. No action needed right now."),
    (50, "mild_difficulty", "You had some difficulty hearing in noise. Consider a hearing check with an audiologist."),
    (0, "needs_doctor", "You had significant difficulty hearing in noise. Please see a doctor or audiologist."),
]
