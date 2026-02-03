from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from app.domain.entities.user import UserRole

class AnalysisOptions(BaseModel):
    """Opsi yang dapat dipilih pengguna untuk memicu analisis."""
    data_overview: bool = False
    summarize: bool = False
    insight: bool = False
    check_duplicates: bool = False
    financial_analysis: bool = False
    sheet_name: Optional[str] = None

class UserResponse(BaseModel):
    """Skema respons untuk data pengguna, menyembunyikan data sensitif."""
    id: int
    uid: str
    email: EmailStr
    role: UserRole
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """Skema untuk membuat pengguna baru."""
    email: EmailStr
    password: str
    role: UserRole

class UserUpdateRole(BaseModel):
    """Skema untuk memperbarui peran pengguna."""
    role: UserRole

class LlmRouterRequest(BaseModel):
    """Skema untuk request ke LLM router proxy."""
    user_prompt: str
    tools: List[Dict[str, Any]]
    conversation_history: Optional[List[Dict[str, str]]] = None

class LlmSummarizeRequest(BaseModel):
    """Skema untuk request peringkasan hasil tool oleh LLM."""
    user_prompt: str
    tool_result: str
    conversation_history: Optional[List[Dict[str, str]]] = None