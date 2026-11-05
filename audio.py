"""
Indexes the noisy digit recordings and builds the merged triplet audio for a trial.
"""
import io
import logging
import random
import re

from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.silence import detect_leading_silence

from config import (
    AUDIO_DIR, DIGITS, LANGUAGES, SAMPLE_RATE, TARGET_DBFS,
    SILENCE_DROP_DB, LEAD_IN_MS, GAP_MS, MP3_BITRATE
)

logger = logging.getLogger(__name__)

FOLDER_PATTERN = re.compile(r"^(\d+)_(hindi|indianenglish)$", re.IGNORECASE)
LANGUAGE_BY_FOLDER = {"hindi": "hindi", "indianenglish": "english"}


def index_clips() -> dict:
    """Map language -> digit -> sorted clip paths relative to AUDIO_DIR."""
    clips = {language: {digit: [] for digit in DIGITS} for language in LANGUAGES}
    for folder in AUDIO_DIR.iterdir():
        match = FOLDER_PATTERN.match(folder.name)
        if not match or int(match[1]) not in DIGITS:
            continue
        clips[LANGUAGE_BY_FOLDER[match[2].lower()]][int(match[1])] = sorted(
            str(path.relative_to(AUDIO_DIR)) for path in folder.rglob("*.wav")
        )
    missing = [f"{language}/{digit}" for language in LANGUAGES for digit in DIGITS if not clips[language][digit]]
    if missing:
        raise RuntimeError(f"No audio clips found for: {', '.join(missing)}")
    return clips


CLIPS = index_clips()
unreadable_clips: set = set()


def load_clip(path: str) -> AudioSegment:
    """Decode a clip as mono, trim leading/trailing silence and normalize its loudness."""
    clip = AudioSegment.from_file(AUDIO_DIR / path).set_channels(1).set_frame_rate(SAMPLE_RATE)
    if clip.dBFS == float("-inf"):
        raise ValueError("clip is silent")
    threshold = clip.dBFS - SILENCE_DROP_DB
    start = detect_leading_silence(clip, silence_threshold=threshold)
    end = len(clip) - detect_leading_silence(clip.reverse(), silence_threshold=threshold)
    if start < end:
        clip = clip[start:end]
    return clip.apply_gain(TARGET_DBFS - clip.dBFS)


def build_trial_audio(language: str, digits: list, used: set) -> tuple:
    """
    Pick one random variant per digit, preferring clips not yet used in this test,
    and merge them into one MP3.

    Returns:
        Tuple of (chosen clip paths, mp3 bytes)
    """
    files, parts = [], []
    for digit in digits:
        readable = [path for path in CLIPS[language][digit] if path not in unreadable_clips]
        candidates = [path for path in readable if path not in used] or readable
        random.shuffle(candidates)
        for path in candidates:
            try:
                parts.append(load_clip(path))
            except (CouldntDecodeError, ValueError) as e:
                logger.warning(f"Skipping unreadable clip {path}: {e}")
                unreadable_clips.add(path)
                continue
            files.append(path)
            break
        else:
            raise RuntimeError(f"No readable clip for digit {digit} in {language}")

    gap = AudioSegment.silent(duration=GAP_MS, frame_rate=SAMPLE_RATE)
    merged = AudioSegment.silent(duration=LEAD_IN_MS, frame_rate=SAMPLE_RATE)
    for part in parts:
        merged += part + gap

    buffer = io.BytesIO()
    merged.export(buffer, format="mp3", bitrate=MP3_BITRATE)
    return files, buffer.getvalue()
