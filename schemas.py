"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class StartHearingTestRequest(BaseModel):
    """Request to start a new hearing test."""
    phone: str = Field(..., description="User's phone number")
    call_id: str = Field(..., description="Unique call ID from Bolna")


class StartHearingTestResponse(BaseModel):
    """Response when hearing test starts."""
    test_id: str = Field(..., description="Unique test identifier")
    audio_url: str = Field(..., description="URL of the audio to play")
    expected_key: str = Field(..., description="Expected keypad digit (for backend validation only)")
    instruction: str = Field(..., description="Instruction text for the user")
    step: int = Field(..., description="Current step number (1-indexed)")
    total_steps: int = Field(..., description="Total steps in the test")


class SubmitAnswerRequest(BaseModel):
    """Request to submit a keypad answer."""
    test_id: str = Field(..., description="Test identifier")
    pressed_key: str = Field(..., description="The digit pressed (0-9)")
    call_id: str = Field(..., description="Call ID for tracking")


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    correct: bool = Field(..., description="Whether the answer was correct")
    current_score: float = Field(..., description="Current score (0-100)")
    next_audio_url: Optional[str] = Field(None, description="URL of next audio or null if finished")
    next_expected_key: Optional[str] = Field(None, description="Expected key for next step")
    instruction: str = Field(..., description="Instruction for next step")
    step: int = Field(..., description="Current step number")
    is_finished: bool = Field(..., description="Whether the test is complete")
    final_score: Optional[float] = Field(None, description="Final score if finished")
    interpretation: Optional[str] = Field(None, description="Interpretation: 'mild', 'moderate', or 'severe'")
    recommendation: Optional[str] = Field(None, description="Recommendation text if finished")


class GetTestResultRequest(BaseModel):
    """Request to get final test results."""
    test_id: str = Field(..., description="Test identifier")


class GetTestResultResponse(BaseModel):
    """Response with final test results."""
    test_id: str
    phone: str
    final_score: float = Field(..., description="Final score (0-100)")
    interpretation: str = Field(..., description="Interpretation: 'mild', 'moderate', or 'severe'")
    recommendation: str = Field(..., description="Recommendation text")
    total_steps: int
    correct_answers: int
    answers: List[Dict[str, Any]] = Field(..., description="Detailed answer history")
    is_finished: bool
    created_at: str
    updated_at: str


class ErrorResponse(BaseModel):
    """Generic error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional details")
