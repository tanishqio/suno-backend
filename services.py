"""
Business logic for hearing test management.
"""
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import logging

from sqlalchemy.orm import Session
from models import HearingTest
from config import (
    AUDIO_CLIPS, AUDIO_BASE_URL, TOTAL_STEPS, 
    SCORE_INTERPRETATION, RECOMMENDATIONS, INSTRUCTION_TEXT
)

logger = logging.getLogger(__name__)


class HearingTestService:
    """Service for managing hearing tests."""
    
    @staticmethod
    def create_test(db: Session, phone: str, call_id: str) -> Tuple[HearingTest, dict]:
        """
        Create a new hearing test and return the first audio clip info.
        
        Returns:
            Tuple of (HearingTest object, first_clip_info dict)
        """
        test_id = str(uuid.uuid4())
        
        # Create new test record
        test = HearingTest(
            id=test_id,
            phone=phone,
            call_id=call_id,
            total_steps=TOTAL_STEPS,
            current_step=0,
            used_audio_indices=[],
            answers=[]
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        
        logger.info(f"Created hearing test {test_id} for phone {phone}, call {call_id}")
        
        # Get first audio clip
        first_clip = HearingTestService._get_next_audio_clip(db, test)
        
        return test, first_clip
    
    @staticmethod
    def _get_next_audio_clip(db: Session, test: HearingTest) -> dict:
        """
        Get the next audio clip for the test, avoiding already-used clips.
        
        Returns:
            Dictionary with audio_url, expected_key, step, total_steps
        """
        used_indices = test.used_audio_indices or []
        available_indices = [i for i in range(1, 10) if i not in used_indices]
        
        if not available_indices:
            # Reset if all clips used (shouldn't happen with proper test length)
            available_indices = list(range(1, 10))
            used_indices = []
        
        # Pick random available clip
        chosen_index = random.choice(available_indices)
        used_indices.append(chosen_index)
        
        # Update test
        test.used_audio_indices = used_indices
        test.current_step += 1
        db.commit()
        
        # Get clip info
        clip_info = AUDIO_CLIPS[chosen_index]
        audio_url = f"{AUDIO_BASE_URL}{clip_info['filename']}"
        
        return {
            "audio_url": audio_url,
            "expected_key": clip_info["expected_key"],
            "step": test.current_step,
            "total_steps": test.total_steps,
            "instruction": INSTRUCTION_TEXT
        }
    
    @staticmethod
    def submit_answer(db: Session, test_id: str, pressed_key: str, call_id: str) -> dict:
        """
        Process a keypad answer submission.
        
        Returns:
            Dictionary with test result and next step info
        """
        # Get test
        test = db.query(HearingTest).filter(HearingTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        # Validate call_id matches
        if test.call_id != call_id:
            raise ValueError(f"Call ID mismatch for test {test_id}")
        
        # Check if already finished
        if test.is_finished:
            raise ValueError(f"Test {test_id} is already finished")
        
        # Get expected key from current state
        # We need to retrieve what we showed in the previous step
        if not test.answers:
            raise ValueError("No answers recorded yet - test state corrupted")
        
        last_answer = test.answers[-1]
        expected_key = last_answer.get("current_expected_key")
        
        if not expected_key:
            raise ValueError("Cannot determine expected key for current step")
        
        # Check if correct
        is_correct = pressed_key == expected_key
        
        # Record answer
        answer_record = {
            "step": test.current_step,
            "expected": expected_key,
            "pressed": pressed_key,
            "correct": is_correct,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        test.answers.append(answer_record)
        
        if is_correct:
            test.correct_answers += 1
        
        db.commit()
        
        logger.info(f"Answer submitted for test {test_id}, step {test.current_step}: "
                   f"expected={expected_key}, pressed={pressed_key}, correct={is_correct}")
        
        # Calculate current score
        current_score = (test.correct_answers / test.current_step) * 100 if test.current_step > 0 else 0
        
        # Check if test is finished
        is_finished = test.current_step >= test.total_steps
        
        result = {
            "correct": is_correct,
            "current_score": current_score,
            "step": test.current_step,
            "is_finished": is_finished,
            "final_score": None,
            "interpretation": None,
            "recommendation": None,
            "next_audio_url": None,
            "next_expected_key": None,
            "instruction": INSTRUCTION_TEXT
        }
        
        if is_finished:
            # Calculate final score and interpretation
            final_score = (test.correct_answers / test.total_steps) * 100
            test.final_score = final_score
            
            interpretation = HearingTestService._get_interpretation(final_score)
            test.interpretation = interpretation
            
            recommendation = RECOMMENDATIONS.get(interpretation, "")
            test.recommendation = recommendation
            
            test.is_finished = True
            db.commit()
            
            result.update({
                "final_score": final_score,
                "interpretation": interpretation,
                "recommendation": recommendation,
                "next_audio_url": None,
                "next_expected_key": None,
                "instruction": "Test completed. Thank you for participating."
            })
            
            logger.info(f"Test {test_id} finished. Score: {final_score}, Interpretation: {interpretation}")
        else:
            # Get next clip
            next_clip = HearingTestService._get_next_audio_clip(db, test)
            
            # Store expected key in answers for next submit call
            if not test.answers:
                test.answers = []
            
            test.answers.append({
                "current_expected_key": next_clip["expected_key"],
                "current_step": test.current_step,
                "timestamp": datetime.utcnow().isoformat()
            })
            db.commit()
            
            result.update({
                "next_audio_url": next_clip["audio_url"],
                "next_expected_key": next_clip["expected_key"],
                "instruction": next_clip["instruction"],
                "step": next_clip["step"]
            })
        
        return result
    
    @staticmethod
    def start_next_step(db: Session, test_id: str) -> dict:
        """
        Get the next audio clip for a test that has been created but not yet answered.
        This is called after POST /start-hearing-test to get the response.
        
        Returns:
            Dictionary with audio_url, expected_key, step, total_steps, instruction
        """
        test = db.query(HearingTest).filter(HearingTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        # Get first audio clip (or next one)
        clip_info = HearingTestService._get_next_audio_clip(db, test)
        
        # Store the expected key so we can verify it on submit
        test.answers.append({
            "current_expected_key": clip_info["expected_key"],
            "current_step": test.current_step,
            "timestamp": datetime.utcnow().isoformat()
        })
        db.commit()
        
        return clip_info
    
    @staticmethod
    def get_test_result(db: Session, test_id: str) -> dict:
        """
        Get the final result of a hearing test.
        """
        test = db.query(HearingTest).filter(HearingTest.id == test_id).first()
        if not test:
            raise ValueError(f"Test {test_id} not found")
        
        if not test.is_finished:
            raise ValueError(f"Test {test_id} is not yet finished")
        
        return {
            "test_id": test.id,
            "phone": test.phone,
            "final_score": test.final_score,
            "interpretation": test.interpretation,
            "recommendation": test.recommendation,
            "total_steps": test.total_steps,
            "correct_answers": test.correct_answers,
            "answers": test.answers,
            "is_finished": test.is_finished,
            "created_at": test.created_at.isoformat(),
            "updated_at": test.updated_at.isoformat()
        }
    
    @staticmethod
    def _get_interpretation(score: float) -> str:
        """Determine interpretation based on score."""
        for interpretation, (min_score, max_score) in SCORE_INTERPRETATION.items():
            if min_score <= score <= max_score:
                return interpretation
        return "severe"
    
    @staticmethod
    def cleanup_expired_tests(db: Session, expiry_minutes: int = 10) -> int:
        """
        Delete tests that have expired (not updated for X minutes).
        
        Returns:
            Number of tests deleted
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=expiry_minutes)
        expired_tests = db.query(HearingTest).filter(
            HearingTest.updated_at < cutoff_time,
            HearingTest.is_finished == False
        ).all()
        
        count = len(expired_tests)
        for test in expired_tests:
            db.delete(test)
            logger.info(f"Deleted expired test {test.id}")
        
        db.commit()
        return count
