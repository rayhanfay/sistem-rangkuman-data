from typing import List, Dict, Any
import json

from app.domain.repositories.history_repository import IHistoryRepository
from app.domain.repositories.file_repository import IFileRepository

class GetAllHistoryUseCase:
    """Use case untuk mendapatkan semua riwayat analisis."""
    def __init__(self, history_repo: IHistoryRepository, file_repo: IFileRepository):
        self.history_repo = history_repo
        self.file_repo = file_repo

    def execute(self) -> List[Dict[str, Any]]:
        """
        Mengambil semua riwayat dan menggabungkannya dengan data file JSON terkait
        serta informasi email pengguna yang melakukan analisis.
        """
        histories = self.history_repo.get_all()
        results = []

        for history in histories:
            json_file = self.file_repo.find_by_timestamp(history.timestamp)
            json_data = None
            if json_file and json_file.json_content:
                try:
                    json_data = json.loads(json_file.json_content)
                except json.JSONDecodeError:
                    json_data = None  

            summary_html = history.summary
            
            results.append({
                "filename": history.filename,
                "upload_date": history.upload_date,
                "summary": summary_html[:100] + ("..." if len(summary_html) > 100 else ""),
                "timestamp": history.timestamp,
                "user_email": history.user_email, 
                "json_data": json_data, 
                "html_data": summary_html
            })
            
        return results