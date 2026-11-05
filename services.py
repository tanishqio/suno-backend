"""
Business logic for hearing test management.
"""
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional
import logging

from sqlalchemy.orm import Session
from models import HearingTest, TrialAudio, SessionLocal
from audio import build_trial_audio
from config import (
    DIGITS, DIGITS_PER_TRIAL, LANGUAGES, TOTAL_TRIALS,
    SCORE_BANDS, INSTRUCTION_TEXT, FINISHED_TEXT
)

logger = logging.getLogger(__name__)


class HearingTestService:
    """Service for managing hearing tests."""

    @staticmethod
    def create_test(db: Session, phone: str, call_id: str, language: Optional[str]) -> HearingTest:
        """Create a new hearing test with its first trial ready."""
        test = HearingTest(
            id=str(uuid.uuid4()),
            phone=phone,
            call_id=call_id,
            language=language or random.choice(LANGUAGES),
            total_trials=TOTAL_TRIALS,
            correct_trials=0,
            trials=[]
        )
        db.add(test)
        HearingTestService._start_trial(db, test)
        db.commit()
        logger.info(f"Created hearing test {test.id} ({test.language}) for phone {phone}, call {call_id}")
        return test

    @staticmethod
    def _start_trial(db: Session, test: HearingTest) -> None:
        """Pick a fresh random triplet and variants, and store its answer and merged audio."""
        digits = random.sample(DIGITS, DIGITS_PER_TRIAL)
        used = {path for trial in test.trials for path in trial["files"]}
        files, mp3 = build_trial_audio(test.language, digits, used)
        number = len(test.trials) + 1
        test.trials = [*test.trials, {
            "trial": number,
            "digits": "".join(str(digit) for digit in digits),
            "files": files,
            "pressed": None,
            "correct": None,
            "answered_at": None
        }]
        db.add(TrialAudio(test_id=test.id, trial=number, mp3=mp3))

    @staticmethod
    def should_continue(test: HearingTest) -> bool:
        """Decide whether another trial follows. Replace with the trial-count rules."""
        return len(test.trials) < test.total_trials

    @staticmethod
    def submit_answer(db: Session, test_id: str, call_id: str, pressed_digits: str) -> HearingTest:
        """Score the current trial, then start the next one or finish the test."""
        test = HearingTestService.get_test(db, test_id)
        if test.call_id != call_id:
            raise ValueError(f"Call ID mismatch for test {test_id}")
        if test.is_finished:
            raise ValueError(f"Test {test_id} is already finished")

        current = test.trials[-1]
        pressed = "".join(char for char in pressed_digits if char.isdigit())
        is_correct = pressed == current["digits"]
        test.trials = [*test.trials[:-1], {
            **current,
            "pressed": pressed,
            "correct": is_correct,
            "answered_at": datetime.utcnow().isoformat()
        }]
        if is_correct:
            test.correct_trials += 1

        logger.info(f"Test {test_id} trial {current['trial']}: expected={current['digits']}, "
                    f"pressed={pressed}, correct={is_correct}")

        if HearingTestService.should_continue(test):
            HearingTestService._start_trial(db, test)
        else:
            test.final_score = round(test.correct_trials / len(test.trials) * 100, 1)
            _, test.interpretation, test.recommendation = next(
                band for band in SCORE_BANDS if test.final_score >= band[0]
            )
            test.is_finished = True
            logger.info(f"Test {test_id} finished. Score: {test.final_score}, Interpretation: {test.interpretation}")

        db.commit()
        return test

    @staticmethod
    def get_test(db: Session, test_id: str) -> HearingTest:
        test = db.query(HearingTest).filter(HearingTest.id == test_id).first()
        if not test:
            raise LookupError(f"Test {test_id} not found")
        return test

    @staticmethod
    def get_trial_audio(db: Session, test_id: str, trial: int) -> bytes:
        audio = db.query(TrialAudio).filter(TrialAudio.test_id == test_id, TrialAudio.trial == trial).first()
        if not audio:
            raise LookupError(f"No audio for test {test_id} trial {trial}")
        return audio.mp3

    @staticmethod
    def instruction(test: HearingTest) -> str:
        return FINISHED_TEXT if test.is_finished else INSTRUCTION_TEXT

    @staticmethod
    def delete_test(db: Session, test_id: str) -> None:
        test = HearingTestService.get_test(db, test_id)
        db.query(TrialAudio).filter(TrialAudio.test_id == test_id).delete()
        db.delete(test)
        db.commit()

    @staticmethod
    def cleanup_expired_tests(expiry_minutes: int) -> None:
        """Delete unfinished tests idle for longer than expiry_minutes, and audio older than that."""
        cutoff = datetime.utcnow() - timedelta(minutes=expiry_minutes)
        db = SessionLocal()
        try:
            expired = db.query(HearingTest).filter(
                HearingTest.updated_at < cutoff,
                HearingTest.is_finished == False
            ).all()
            for test in expired:
                db.delete(test)
                logger.info(f"Deleted expired test {test.id}")
            db.query(TrialAudio).filter(TrialAudio.created_at < cutoff).delete()
            db.commit()
        finally:
            db.close()
