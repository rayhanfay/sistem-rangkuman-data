from typing import List, Dict, Any
from app.domain.repositories.file_repository import IFileRepository

class GetResourcesUseCase:
    """
    Use case untuk mendapatkan daftar semua sumber data (resources)
    yang tersedia untuk analisis kustom.
    """
    def __init__(self, file_repo: IFileRepository):
        self.file_repo = file_repo

    def execute(self) -> List[Dict[str, Any]]:
        """
        Mengambil semua entitas file dari repository dan memformatnya
        ke dalam struktur yang diharapkan oleh frontend.
        """
        try:
            files = self.file_repo.get_all()

            resources = [
                {
                    "name": file.filename,
                    "description": f"Data JSON yang diunggah pada {file.upload_date.strftime('%Y-%m-%d %H:%M')}"
                }
                for file in files
            ]
            return resources
        except Exception as e:
            print(f"ERROR saat mengambil resources: {e}")
            return []
