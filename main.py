"""
FastAPI backend for voice AI hearing screening agent using Bolna.
"""
import logging
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from models import get_db, HearingTest
from schemas import (
    StartHearingTestRequest, StartHearingTestResponse,
    SubmitAnswerRequest, SubmitAnswerResponse,
    GetTestResultRequest, GetTestResultResponse,
    ErrorResponse
)
from services import HearingTestService
from config import TEST_EXPIRY_MINUTES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hearing Screening Agent API",
    description="Backend for voice AI hearing screening using Bolna",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Hearing Screening Agent API"
    }


@app.post("/start-hearing-test", response_model=StartHearingTestResponse, tags=["Hearing Test"])
async def start_hearing_test(
    request: StartHearingTestRequest,
    db: Annotated[Session, Depends(get_db)],
    background_tasks: BackgroundTasks
):
    """
    Start a new hearing test session.
    
    This endpoint:
    1. Creates a new test record
    2. Selects the first audio clip
    3. Returns the audio URL for Bolna to play
    
    The user then presses a keypad digit, which Bolna sends to /submit-answer.
    """
    try:
        logger.info(f"Starting hearing test for phone: {request.phone}, call_id: {request.call_id}")
        
        # Create test
        test, first_clip = HearingTestService.create_test(
            db, 
            phone=request.phone, 
            call_id=request.call_id
        )
        
        # Store expected key for first step
        first_clip_data = HearingTestService.start_next_step(db, test.id)
        
        # Schedule cleanup of expired tests
        background_tasks.add_task(
            HearingTestService.cleanup_expired_tests, 
            db, 
            TEST_EXPIRY_MINUTES
        )
        
        return StartHearingTestResponse(
            test_id=test.id,
            audio_url=first_clip_data["audio_url"],
            expected_key=first_clip_data["expected_key"],
            instruction=first_clip_data["instruction"],
            step=first_clip_data["step"],
            total_steps=first_clip_data["total_steps"]
        )
    
    except Exception as e:
        logger.error(f"Error starting hearing test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-answer", response_model=SubmitAnswerResponse, tags=["Hearing Test"])
async def submit_answer(
    request: SubmitAnswerRequest,
    db: Annotated[Session, Depends(get_db)],
    background_tasks: BackgroundTasks
):
    """
    Submit a keypad answer from the user.
    
    Flow:
    1. User hears audio from /start-hearing-test or /submit-answer
    2. User presses a digit on their keypad (0-9)
    3. Bolna sends that digit to this endpoint via DTMF
    4. Backend validates, updates score, decides next audio
    5. Returns next audio URL (or null if finished)
    
    Bolna repeats steps 1-5 until is_finished=true.
    """
    try:
        logger.info(f"Processing answer for test: {request.test_id}, "
                   f"pressed_key: {request.pressed_key}, call_id: {request.call_id}")
        
        result = HearingTestService.submit_answer(
            db, 
            test_id=request.test_id, 
            pressed_key=request.pressed_key,
            call_id=request.call_id
        )
        
        # Schedule cleanup
        background_tasks.add_task(
            HearingTestService.cleanup_expired_tests, 
            db, 
            TEST_EXPIRY_MINUTES
        )
        
        return SubmitAnswerResponse(
            correct=result["correct"],
            current_score=result["current_score"],
            next_audio_url=result["next_audio_url"],
            next_expected_key=result["next_expected_key"],
            instruction=result["instruction"],
            step=result["step"],
            is_finished=result["is_finished"],
            final_score=result["final_score"],
            interpretation=result["interpretation"],
            recommendation=result["recommendation"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get-test-result", response_model=GetTestResultResponse, tags=["Hearing Test"])
async def get_test_result(
    request: GetTestResultRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Retrieve the final result of a completed hearing test.
    
    Returns:
    - Final score (0-100)
    - Interpretation (mild, moderate, severe)
    - Recommendation text
    - Detailed answer history
    """
    try:
        logger.info(f"Retrieving test result for test_id: {request.test_id}")
        
        result = HearingTestService.get_test_result(db, request.test_id)
        
        return GetTestResultResponse(
            test_id=result["test_id"],
            phone=result["phone"],
            final_score=result["final_score"],
            interpretation=result["interpretation"],
            recommendation=result["recommendation"],
            total_steps=result["total_steps"],
            correct_answers=result["correct_answers"],
            answers=result["answers"],
            is_finished=result["is_finished"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-status/{test_id}", tags=["Hearing Test"])
async def get_test_status(
    test_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get current status of an ongoing or completed test.
    
    Returns:
    - Current step
    - Current score
    - Is finished
    - All answers so far
    """
    try:
        test = db.query(HearingTest).filter(HearingTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        current_score = (test.correct_answers / test.current_step) * 100 if test.current_step > 0 else 0
        
        return {
            "test_id": test.id,
            "phone": test.phone,
            "current_step": test.current_step,
            "total_steps": test.total_steps,
            "current_score": current_score,
            "correct_answers": test.correct_answers,
            "is_finished": test.is_finished,
            "final_score": test.final_score,
            "interpretation": test.interpretation,
            "answers": test.answers,
            "created_at": test.created_at.isoformat(),
            "updated_at": test.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/test/{test_id}", tags=["Hearing Test"])
async def delete_test(
    test_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Delete a test record.
    """
    try:
        test = db.query(HearingTest).filter(HearingTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        db.delete(test)
        db.commit()
        
        logger.info(f"Deleted test {test_id}")
        
        return {
            "status": "success",
            "message": f"Test {test_id} deleted",
            "test_id": test_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Hearing Screening Agent API starting up...")
    logger.info(f"Database initialized with test expiry time: {TEST_EXPIRY_MINUTES} minutes")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Hearing Screening Agent API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
