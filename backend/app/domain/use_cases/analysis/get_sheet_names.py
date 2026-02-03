from typing import List
from app.domain.repositories.asset_data_source import IAssetDataSource

class GetSheetNamesUseCase:
    """Use case untuk mendapatkan semua nama sheet dari sumber data."""
    def __init__(self, asset_data_source: IAssetDataSource):
        self.asset_data_source = asset_data_source

    def execute(self) -> List[str]:
        """
        Memanggil repository untuk mengambil daftar nama sheet.
        """
        try:
            return self.asset_data_source.get_sheet_names()
        except Exception as e:
            print(f"ERROR saat mengambil nama sheet: {e}")
            raise RuntimeError(f"Gagal mengambil daftar sheet dari sumber data: {e}")