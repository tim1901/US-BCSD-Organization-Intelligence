from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.brain.service import BrainService
from app.models.dto import BrainAskRequest, BrainAskResponse

router = APIRouter(prefix="/api/brain", tags=["brain"])


@router.post("/ask", response_model=BrainAskResponse)
def ask(request: BrainAskRequest):
    try:
        organization_id = BrainService.organization_id_for_us_bcsd()
        result = BrainService(organization_id).ask(
            question=request.question,
            project_id=request.project_id,
            conversation_id=request.conversation_id,
            channel_id=request.channel_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return BrainAskResponse(
        question=result.question,
        answer=result.answer,
        plan=result.plan,
        retrieved_memory=result.retrieved_memory,
        citations=result.citations,
    )
