"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class StartHearingTestRequest(BaseModel):
    """Request to start a new hearing test."""
    phone: str = Field(..., description="User's phone number")
    call_id: str = Field(..., description="Unique call ID from Bolna")
    language: Optional[Literal["hindi", "english"]] = Field(
        None, description="Voice language for the whole test; random if omitted"
    )


class StartHearingTestResponse(BaseModel):
    """Response when hearing test starts."""
    test_id: str = Field(..., description="Unique test identifier")
    trial: int = Field(..., description="Current trial number (1-indexed)")
    total_trials: int = Field(..., description="Maximum trials in the test")
    audio_url: str = Field(..., description="Absolute URL of the merged triplet audio to play")
    expected_digits: str = Field(..., description="The three digits the user should press, e.g. '695'")
    instruction: str = Field(..., description="Instruction text for the user")
    language: str = Field(..., description="Voice language used for this test")


class SubmitAnswerRequest(BaseModel):
    """Request to submit the digits the user pressed."""
    test_id: str = Field(..., description="Test identifier")
    call_id: str = Field(..., description="Call ID for tracking")
    pressed_digits: str = Field(..., description="Digits pressed via DTMF, e.g. '695' or '6 9 5'")


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    test_id: str
    answered_trial: int = Field(..., description="Trial number that was just answered")
    correct: bool = Field(..., description="Whether all three digits matched in order")
    correct_trials: int
    trials_completed: int
    total_trials: int
    is_finished: bool
    instruction: str
    next_trial: Optional[int] = Field(None, description="Next trial number, null if finished")
    next_audio_url: Optional[str] = Field(None, description="Absolute URL of the next audio, null if finished")
    next_expected_digits: Optional[str] = Field(None, description="Digits expected for the next trial")
    final_score: Optional[float] = Field(None, description="Percentage of trials correct, if finished")
    interpretation: Optional[str] = Field(None, description="'good', 'mild_difficulty' or 'needs_doctor'")
    recommendation: Optional[str] = Field(None, description="Recommendation text, if finished")


class GetTestResultRequest(BaseModel):
    """Request to get final test results."""
    test_id: str = Field(..., description="Test identifier")


class GetTestResultResponse(BaseModel):
    """Response with final test results."""
    test_id: str
    phone: str
    language: str
    final_score: float = Field(..., description="Percentage of trials correct (0-100)")
    interpretation: str = Field(..., description="'good', 'mild_difficulty' or 'needs_doctor'")
    recommendation: str
    total_trials: int
    correct_trials: int
    trials: List[Dict[str, Any]] = Field(..., description="Per-trial history")
    is_finished: bool
    created_at: str
    updated_at: str
