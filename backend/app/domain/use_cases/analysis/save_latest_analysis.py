import traceback
from datetime import datetime
import pytz
from typing import Callable, Dict, List, Any, Optional
import pandas as pd
import logging
import json

from app.domain.entities.user import User
from app.domain.entities.history import History
from app.domain.entities.file import File
from app.domain.repositories.history_repository import IHistoryRepository
from app.domain.repositories.file_repository import IFileRepository
from app.infrastructure.services.preview_state_service import PreviewStateService

class SaveLatestAnalysisUseCase:
    """
    Use case untuk menyimpan hasil analisis dari state pratinjau (preview)
    ke penyimpanan data permanen (database).
    """
    def __init__(
        self,
        history_repo: IHistoryRepository,
        file_repo: IFileRepository,
        preview_state_service: PreviewStateService
    ):
        self.history_repo = history_repo
        self.file_repo = file_repo
        self.preview_state_service = preview_state_service

    def execute(self, current_user: Optional[User] = None) -> History:
        """
        Menjalankan logika penyimpanan, mendukung user manual maupun sistem (Otomasi).
        """
        latest_result = self.preview_state_service.get()
        if not latest_result or not latest_result.get("data_available"):
            raise ValueError("Tidak ada hasil analisis valid di pratinjau untuk disimpan.")

        df = latest_result["dataframe"]
        options = latest_result["options"]
        analysis_time = latest_result["analysis_time"]
        timestamp_str = analysis_time.strftime("%Y%m%d_%H%M%S")

        # --- LOGIKA IDENTITAS (USER VS SYSTEM) ---
        if current_user:
            user_email = current_user.email
            user_role_str = current_user.role.name.capitalize() if current_user.role else "User"
            prefix_name = "Laporan Manual"
        else:
            user_email = "system@phr.internal"
            user_role_str = "System"
            prefix_name = "Otomasi Harian"

        source_type = options.get('source', 'master').upper() # SIKLUS atau MASTER
        sheet_name_for_file = options.get('sheet_name') or 'MASTER-SHEET'
        
        base_filename = f"{prefix_name} [{source_type}]: {sheet_name_for_file}"
        
        tool_map = {
            'data_overview': 'Data Overview',
            'summarize': 'Ringkasan Eksekutif', 
            'insight': 'Insight Kondisi Aset', 
            'check_duplicates': 'Cek Duplikasi', 
            'financial_analysis': 'Rangkuman Nilai Aset'
        }
        used_tools = [tool_map[tool] for tool, enabled in options.items() if enabled and tool in tool_map]

        if used_tools:
            tools_str = ', '.join(used_tools)
            analysis_name = f"{base_filename} | {tools_str}"
        else:
            analysis_name = base_filename

        cycle_assets_table = latest_result.get("cycle_assets_table", [])
        cleaned_cycle_assets = []
        if cycle_assets_table:
            for row in cycle_assets_table:
                cleaned_row = {}
                for key, value in row.items():
                    if isinstance(value, pd.Timestamp):
                        cleaned_row[key] = value.isoformat()
                    else:
                        cleaned_row[key] = value
                cleaned_cycle_assets.append(cleaned_row)

        new_history_entity = History(
            id=None,  
            filename=analysis_name,
            summary=latest_result["summary_text"],
            timestamp=timestamp_str,
            upload_date=analysis_time,
            cycle_assets=cleaned_cycle_assets, 
            user_email=user_email, 
            sheet_name=sheet_name_for_file
        )
        saved_history = self.history_repo.save(new_history_entity)

        safe_sheet_name = sheet_name_for_file.replace(" ", "_")
        new_json_filename = f"data_{source_type.lower()}_{safe_sheet_name}_{timestamp_str}.json"
        
        raw_json = df.to_json(orient='records', date_format='iso')
        
        json_file_entity = File(
            id=None,
            filename=new_json_filename,
            file_type="json",
            json_content=raw_json,
            upload_date=analysis_time
        )
        self.file_repo.save(json_file_entity)
        
        print(f"[DB-SAVE] Berhasil menyimpan analisis {source_type} ke riwayat: {new_json_filename}")
        
        self.preview_state_service.clear()
        print("[INFO] State pratinjau telah dibersihkan setelah penyimpanan.")
        
        return saved_history