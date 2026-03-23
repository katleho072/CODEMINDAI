from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid

from backend.app.models.schemas import (
    CodingRequest, CodingResponse, FileUpload,
    CodebaseContext, ChatMessage
)

from backend.app.services.context import CodebaseContextManager
from backend.app.api.deps import get_current_user, get_context_manager, get_ai_service

from backend.app.services.ai import AIService

router = APIRouter()


@router.post("/chat", response_model=CodingResponse)
async def chat_with_context(
        request: CodingRequest,
        session_id: str = None,
        ai_service: AIService = Depends(get_ai_service),
        context_manager: CodebaseContextManager = Depends(get_context_manager)
):
    """
    Main chat endpoint with codebase context
    """
    # Generate or use session ID
    if not session_id:
        session_id = str(uuid.uuid4())
        context_manager.create_session(session_id)

    # Get relevant context from codebase
    context_snippets = []
    if request.context and request.context.files:
        # Add new files to context
        context_manager.add_files(session_id, request.context.files)

    # Search for relevant code snippets
    if request.context and request.context.files:
        context_snippets = context_manager.get_relevant_context(
            session_id, request.message
        )

    # Generate response
    response = await ai_service.generate_code_response(
        request=request,
        context_snippets=context_snippets
    )

    return response


@router.post("/upload-files")
async def upload_files(
        files: List[FileUpload],
        session_id: str,
        context_manager: CodebaseContextManager = Depends(get_context_manager)
):
    """
    Upload files to establish codebase context
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    results = context_manager.add_files(session_id, files)

    summary = context_manager.get_project_summary(session_id)

    return {
        "session_id": session_id,
        "files_processed": len(results),
        "results": results,
        "project_summary": summary
    }


@router.get("/project-summary/{session_id}")
async def get_project_summary(
        session_id: str,
        context_manager: CodebaseContextManager = Depends(get_context_manager)
):
    """
    Get summary of the codebase in current session
    """
    summary = context_manager.get_project_summary(session_id)

    if not summary:
        raise HTTPException(
            status_code=404,
            detail="Session not found or no files uploaded"
        )

    return summary


@router.post("/explain-code")
async def explain_code(
        code: str,
        language: str = "python",
        ai_service: AIService = Depends(get_ai_service)
):
    """
    Explain a piece of code
    """
    explanation = await ai_service.explain_code(code, language)
    return {"explanation": explanation}