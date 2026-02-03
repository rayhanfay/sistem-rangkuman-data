from datetime import datetime
import pandas as pd

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

    def execute(self, current_user: User) -> History:
        """
        Menjalankan logika penyimpanan, dengan nama file yang diperbarui agar lebih mudah dibaca.
        """
        latest_result = self.preview_state_service.get()
        if not latest_result or not latest_result.get("data_available"):
            raise ValueError("Tidak ada hasil analisis valid di pratinjau untuk disimpan.")

        df = latest_result["dataframe"]
        options = latest_result["options"]
        analysis_time = latest_result["analysis_time"]
        timestamp_str = analysis_time.strftime("%Y%m%d_%H%M%S")

        
        sheet_name_for_file = options.get('sheet_name') or 'MasterDataAsset'
        user_role_str = current_user.role.name.capitalize()

        base_filename = f"Laporan Manual: {sheet_name_for_file} - oleh {user_role_str}"
        
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

        # Kembalikan logika pembersihan data tanggal untuk cycle_assets
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
            user_email=current_user.email,
            sheet_name=sheet_name_for_file
        )
        saved_history = self.history_repo.save(new_history_entity)

        safe_sheet_name = sheet_name_for_file.replace(" ", "_")
        new_json_filename = f"data_{safe_sheet_name}_{timestamp_str}.json"
        
        raw_json = df.to_json(orient='records', date_format='iso')
        
        json_file_entity = File(
            id=None,
            filename=new_json_filename,
            file_type="json",
            json_content=raw_json,
            upload_date=analysis_time
        )
        self.file_repo.save(json_file_entity)
        
        print(f"[DB-SAVE] Berhasil menyimpan analisis ke riwayat: {new_json_filename}")
        
        self.preview_state_service.clear()
        print("[INFO] State pratinjau telah dibersihkan setelah penyimpanan.")
        
        return saved_history