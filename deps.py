from fastapi import Depends, HTTPException, status
from typing import Annotated

from backend.app.services.context import CodebaseContextManager
from backend.app.services.ai import AIService
from backend.app.core.config import settings

async def get_context_manager() -> CodebaseContextManager:
    # This would come from app state in real app
    from backend.app.main import app
    return app.state.context_manager

async def get_ai_service() -> AIService:
    # This would come from app state in real app
    from backend.app.main import app
    return app.state.ai_service

async def get_current_user():
    # TODO: Implement authentication
    return {"id": "user_1", "email": "demo@example.com"}