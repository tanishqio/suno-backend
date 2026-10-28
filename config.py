"""
Audio configuration for hearing screening test.
Each audio file represents a noisy number (1-9) at different noise levels.
"""

# Audio files configuration
# Format: {key: (filename, expected_digit, noise_level)}
AUDIO_CLIPS = {
    1: {
        "filename": "number_1_noise_40db.mp3",
        "expected_key": "1",
        "noise_level": "low",
        "description": "Number 1 with low background noise"
    },
    2: {
        "filename": "number_2_noise_35db.mp3",
        "expected_key": "2",
        "noise_level": "low",
        "description": "Number 2 with low background noise"
    },
    3: {
        "filename": "number_3_noise_30db.mp3",
        "expected_key": "3",
        "noise_level": "low",
        "description": "Number 3 with low background noise"
    },
    4: {
        "filename": "number_4_noise_25db.mp3",
        "expected_key": "4",
        "noise_level": "moderate",
        "description": "Number 4 with moderate background noise"
    },
    5: {
        "filename": "number_5_noise_20db.mp3",
        "expected_key": "5",
        "noise_level": "moderate",
        "description": "Number 5 with moderate background noise"
    },
    6: {
        "filename": "number_6_noise_15db.mp3",
        "expected_key": "6",
        "noise_level": "moderate",
        "description": "Number 6 with moderate background noise"
    },
    7: {
        "filename": "number_7_noise_10db.mp3",
        "expected_key": "7",
        "noise_level": "high",
        "description": "Number 7 with high background noise"
    },
    8: {
        "filename": "number_8_noise_8db.mp3",
        "expected_key": "8",
        "noise_level": "high",
        "description": "Number 8 with high background noise"
    },
    9: {
        "filename": "number_9_noise_5db.mp3",
        "expected_key": "9",
        "noise_level": "high",
        "description": "Number 9 with high background noise"
    }
}

# Audio hosting configuration
# Change this to your actual CDN/hosting URL
AUDIO_BASE_URL = "https://your-audio-cdn.example.com/hearing-test/"

# Test configuration
TOTAL_STEPS = 5
TEST_EXPIRY_MINUTES = 10
INSTRUCTION_TEXT = "Press the number you hear on your phone keypad"

# Scoring interpretation ranges
SCORE_INTERPRETATION = {
    "mild": (80, 100),
    "moderate": (50, 79),
    "severe": (0, 49)
}

# Recommendations
RECOMMENDATIONS = {
    "mild": "Your hearing appears to be normal or have mild issues. Continue monitoring.",
    "moderate": "Your hearing shows moderate loss. Please consult an audiologist.",
    "severe": "Your hearing shows significant loss. Please see a doctor or audiologist immediately."
}
