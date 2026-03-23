from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class CodeLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    KOTLIN = "kotlin"

class FileUpload(BaseModel):
    filename: str
    content: str
    language: Optional[CodeLanguage] = None
    path: Optional[str] = None  # Relative path in project

class CodebaseContext(BaseModel):
    files: List[FileUpload] = Field(default_factory=list)
    current_file: Optional[str] = None
    cursor_position: Optional[int] = None

class ChatMessage(BaseModel):
    role: ChatRole
    content: str
    metadata: Optional[Dict[str, Any]] = None

class CodingRequest(BaseModel):
    message: str
    context: Optional[CodebaseContext] = None
    language: CodeLanguage = CodeLanguage.PYTHON
    execute_code: bool = False  # Whether to run suggested code

class CodingResponse(BaseModel):
    message: str
    code_suggestions: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None
    executed_output: Optional[str] = None
    context_used: List[str] = Field(default_factory=list)  # Which files were referenced