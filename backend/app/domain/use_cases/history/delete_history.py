from typing import Dict
from app.domain.repositories.history_repository import IHistoryRepository
from app.domain.repositories.file_repository import IFileRepository

class DeleteHistoryUseCase:
    """Use case untuk menghapus satu riwayat analisis beserta file datanya."""
    def __init__(self, history_repo: IHistoryRepository, file_repo: IFileRepository):
        self.history_repo = history_repo
        self.file_repo = file_repo

    def execute(self, timestamp: str) -> Dict[str, str]:
        """
        Menjalankan logika penghapusan.
        Akan mencoba menghapus dari kedua repository.
        """
        history_deleted = self.history_repo.delete_by_timestamp(timestamp)
        if not history_deleted:
            raise FileNotFoundError("Entri riwayat tidak ditemukan.")
            
        self.file_repo.delete_by_timestamp(timestamp) 
        
        return {"message": "Riwayat dan data terkait berhasil dihapus."}