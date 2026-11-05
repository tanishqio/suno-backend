"""
FastAPI backend for the Suno Care Digits-in-Noise hearing screening test, driven by Bolna.
"""
import logging
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from models import get_db, HearingTest
from schemas import (
    StartHearingTestRequest, StartHearingTestResponse,
    SubmitAnswerRequest, SubmitAnswerResponse,
    GetTestResultRequest, GetTestResultResponse
)
from services import HearingTestService
from config import TEST_EXPIRY_MINUTES, PUBLIC_BASE_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Suno Care Digits-in-Noise API",
    description="Backend for the Digits-in-Noise hearing screening test over Bolna voice calls",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def audio_url(request: Request, test: HearingTest, trial: int) -> str:
    """Absolute URL Bolna fetches the merged trial audio from."""
    base_url = (PUBLIC_BASE_URL or str(request.base_url)).rstrip("/")
    return f"{base_url}/audio/{test.id}/{trial}.mp3"


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "Suno Care Digits-in-Noise API"}


@app.post("/start-hearing-test", response_model=StartHearingTestResponse, tags=["Hearing Test"])
def start_hearing_test(
    body: StartHearingTestRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    background_tasks: BackgroundTasks
):
    """
    Start a new test: creates the session, picks 3 random digits with one random
    noisy variant each, and returns the merged audio URL and the expected digits.
    """
    logger.info(f"Starting hearing test for phone: {body.phone}, call_id: {body.call_id}")
    test = HearingTestService.create_test(db, body.phone, body.call_id, body.language)
    background_tasks.add_task(HearingTestService.cleanup_expired_tests, TEST_EXPIRY_MINUTES)

    current = test.trials[-1]
    return StartHearingTestResponse(
        test_id=test.id,
        trial=current["trial"],
        total_trials=test.total_trials,
        audio_url=audio_url(request, test, current["trial"]),
        expected_digits=current["digits"],
        instruction=HearingTestService.instruction(test),
        language=test.language
    )


@app.post("/submit-answer", response_model=SubmitAnswerResponse, tags=["Hearing Test"])
def submit_answer(
    body: SubmitAnswerRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    background_tasks: BackgroundTasks
):
    """
    Score the digits the user pressed against the server-side answer for the current
    trial, then return the next trial or the final result.
    """
    logger.info(f"Processing answer for test: {body.test_id}, pressed: {body.pressed_digits}")
    try:
        test = HearingTestService.submit_answer(db, body.test_id, body.call_id, body.pressed_digits)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    background_tasks.add_task(HearingTestService.cleanup_expired_tests, TEST_EXPIRY_MINUTES)

    answered = test.trials[-1] if test.is_finished else test.trials[-2]
    upcoming = None if test.is_finished else test.trials[-1]
    return SubmitAnswerResponse(
        test_id=test.id,
        answered_trial=answered["trial"],
        correct=answered["correct"],
        correct_trials=test.correct_trials,
        trials_completed=answered["trial"],
        total_trials=test.total_trials,
        is_finished=test.is_finished,
        instruction=HearingTestService.instruction(test),
        next_trial=upcoming and upcoming["trial"],
        next_audio_url=upcoming and audio_url(request, test, upcoming["trial"]),
        next_expected_digits=upcoming and upcoming["digits"],
        final_score=test.final_score,
        interpretation=test.interpretation,
        recommendation=test.recommendation
    )


@app.api_route("/audio/{test_id}/{trial}.mp3", methods=["GET", "HEAD"], tags=["Audio"])
def get_trial_audio(test_id: str, trial: int, db: Annotated[Session, Depends(get_db)]):
    """Merged triplet audio for one trial of a test."""
    try:
        mp3 = HearingTestService.get_trial_audio(db, test_id, trial)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(content=mp3, media_type="audio/mpeg", headers={"Cache-Control": "private, max-age=600"})


@app.post("/get-test-result", response_model=GetTestResultResponse, tags=["Hearing Test"])
def get_test_result(body: GetTestResultRequest, db: Annotated[Session, Depends(get_db)]):
    """Final result of a completed test with per-trial history."""
    try:
        test = HearingTestService.get_test(db, body.test_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not test.is_finished:
        raise HTTPException(status_code=400, detail=f"Test {body.test_id} is not yet finished")

    return GetTestResultResponse(
        test_id=test.id,
        phone=test.phone,
        language=test.language,
        final_score=test.final_score,
        interpretation=test.interpretation,
        recommendation=test.recommendation,
        total_trials=len(test.trials),
        correct_trials=test.correct_trials,
        trials=test.trials,
        is_finished=test.is_finished,
        created_at=test.created_at.isoformat(),
        updated_at=test.updated_at.isoformat()
    )


@app.get("/test-status/{test_id}", tags=["Hearing Test"])
def get_test_status(test_id: str, db: Annotated[Session, Depends(get_db)]):
    """Current state of an ongoing or completed test."""
    try:
        test = HearingTestService.get_test(db, test_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    answered = [trial for trial in test.trials if trial["correct"] is not None]
    return {
        "test_id": test.id,
        "phone": test.phone,
        "language": test.language,
        "current_trial": test.trials[-1]["trial"],
        "total_trials": test.total_trials,
        "trials_completed": len(answered),
        "correct_trials": test.correct_trials,
        "current_score": round(test.correct_trials / len(answered) * 100, 1) if answered else 0,
        "is_finished": test.is_finished,
        "final_score": test.final_score,
        "interpretation": test.interpretation,
        "trials": test.trials,
        "created_at": test.created_at.isoformat(),
        "updated_at": test.updated_at.isoformat()
    }


@app.delete("/test/{test_id}", tags=["Hearing Test"])
def delete_test(test_id: str, db: Annotated[Session, Depends(get_db)]):
    """Delete a test and its audio."""
    try:
        HearingTestService.delete_test(db, test_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    logger.info(f"Deleted test {test_id}")
    return {"status": "success", "message": f"Test {test_id} deleted", "test_id": test_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
