import json
import logging
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import StreamingResponse

# Dependencies yang relevan
from app.dependencies import (
    get_download_file_use_case,
    get_document_analyzer,
    get_resource_list_use_case
)
from app.domain.use_cases.analysis.get_download_file import GetDownloadFileUseCase
from app.infrastructure.services.document_analyzer import DocumentAnalyzer

# Schemas dan Auth yang dipakai
from app.presentation.schemas import LlmRouterRequest, LlmSummarizeRequest
from app.presentation.auth import auth_required
from app.domain.entities.user import User as UserEntity

# --- Inisialisasi Router ---
router = APIRouter(prefix="/api/web", tags=["Web API (Utilitas)"])

# === Endpoint Kritis yang WAJIB Dipertahankan ===

@router.get("/download")
def download_data(
    file_format: str = Query(...), 
    source: str = Query(...), 
    timestamp: Optional[str] = Query(None),
    area: Optional[str] = Query(None), 
    sheet_name: Optional[str] = Query(None),
    user: UserEntity = Depends(auth_required),
    use_case: GetDownloadFileUseCase = Depends(get_download_file_use_case)
):
    """Endpoint esensial untuk mengunduh file data (CSV/XLSX) melalui HTTP."""
    try:
        file_buffer, filename, media_type = use_case.execute(
            file_format=file_format, source=source, timestamp=timestamp, area=area, sheet_name=sheet_name
        )
        return StreamingResponse(
            file_buffer, 
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"[DOWNLOAD ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Gagal membuat file unduhan: {e}")


# === Endpoint Proxy Aman untuk Fitur Percakapan AI ===

@router.post("/llm-router")
async def llm_router(
    request: LlmRouterRequest,
    user: UserEntity = Depends(auth_required),
    doc_analyzer: DocumentAnalyzer = Depends(get_document_analyzer),
    resource_use_case = Depends(get_resource_list_use_case)
):
    """
    Endpoint aman untuk meminta LLM memilih tool yang sesuai.
    PERBAIKAN: Menambahkan resources list ke context LLM agar bisa membaca data dari sheet lain.
    PROTEKSI: Mencegah eksekusi trigger_analysis melalui Custom Analysis.
    """
    try:
        # 1. Dapatkan daftar resources (file hasil analisis tersimpan) yang tersedia
        resources_list = []
        try:
            resources_result = resource_use_case.execute()
            resources_list = resources_result if isinstance(resources_result, list) else []
        except Exception as e:
            logging.warning(f"[LLM-ROUTER] Failed to fetch resources: {e}")
            # Lanjutkan tanpa resources jika gagal agar chat tidak crash
        
        # 2. Minta LLM memutuskan tool mana yang harus dipanggil
        tool_choice_str = await doc_analyzer.decide_tool_to_use(
            user_prompt=request.user_prompt, 
            tools=request.tools, 
            conversation_history=request.conversation_history,
            resources=resources_list
        )

        # 3. PERBAIKAN & PROTEKSI: Cek apakah LLM mencoba menjalankan trigger_analysis
        try:
            tool_data = json.loads(tool_choice_str)
            if tool_data.get("tool_name") == "trigger_analysis":
                logging.warning(f"[SECURITY] User {user.email} mencoba memicu trigger_analysis melalui chat. Permintaan diblokir.")
                
                # Override pilihan tool menjadi 'tidak_ada_tool' dengan pesan edukatif
                blocked_choice = {
                    "tool_name": "tidak_ada_tool",
                    "arguments": {},
                    "message": "Maaf, fitur 'Analisis Dashboard' hanya dapat dijalankan melalui tombol utama di Dashboard untuk menjaga performa sistem. Anda tetap bisa menanyakan statistik data melalui chat ini."
                }
                return {"tool_choice": json.dumps(blocked_choice)}
                
        except json.JSONDecodeError:
            logging.error(f"[LLM-ROUTER] LLM returned invalid JSON: {tool_choice_str}")
            raise HTTPException(status_code=500, detail="LLM memberikan respon format yang salah.")   
        return {"tool_choice": tool_choice_str}
        
    except ValueError as e:
        # Error dari quota exhausted atau validasi
        logging.error(f"[LLM-ROUTER ValueError] {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        # Error tak terduga - log detail lengkap
        logging.error("="*80)
        logging.error("[LLM-ROUTER CRITICAL ERROR]")
        logging.error(f"User Prompt: {request.user_prompt[:200]}...")
        logging.error(f"Error Type: {type(e).__name__}")
        logging.error(f"Error Message: {str(e)}")
        logging.error(f"Traceback:\n{traceback.format_exc()}")
        logging.error("="*80)
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error saat routing tool: {type(e).__name__} - {str(e)}"
        )


@router.post("/llm-summarize")
async def llm_summarize(
    request: LlmSummarizeRequest,
    user: UserEntity = Depends(auth_required),
    doc_analyzer: DocumentAnalyzer = Depends(get_document_analyzer)
):
    """
    Endpoint aman untuk meminta LLM meringkas hasil dari tool.
    PERBAIKAN: Menambahkan logging yang lebih detail untuk debugging.
    """
    try:
        summary = await doc_analyzer.summarize_tool_result(
            user_prompt=request.user_prompt, 
            tool_result=request.tool_result,
            conversation_history=request.conversation_history
        )
        return {"summary": summary}
        
    except ValueError as e:
        # Error dari quota exhausted
        logging.error(f"[LLM-SUMMARIZE ValueError] {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        # Error tak terduga - log detail lengkap
        logging.error("="*80)
        logging.error("[LLM-SUMMARIZE CRITICAL ERROR]")
        logging.error(f"User Prompt: {request.user_prompt[:200]}...")
        logging.error(f"Tool Result Length: {len(str(request.tool_result))}")
        logging.error(f"Error Type: {type(e).__name__}")
        logging.error(f"Error Message: {str(e)}")
        logging.error(f"Traceback:\n{traceback.format_exc()}")
        logging.error("="*80)
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error saat summarize: {type(e).__name__} - {str(e)}"
        )