from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from app.domain.entities.user import UserRole

class AnalysisOptions(BaseModel):
    """
    Opsi yang dikirim dari Frontend/LLM untuk memicu analisis.
    Field 'source' sangat krusial untuk menentukan link Google Sheets mana yang dipakai.
    """
    sheet_name: Optional[str] = 'MASTER-SHEET'
    source: Optional[str] = 'master'  
    data_overview: bool = True
    summarize: bool = True
    insight: bool = True
    check_duplicates: bool = False
    financial_analysis: bool = False

    class Config:
        extra = "allow"

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