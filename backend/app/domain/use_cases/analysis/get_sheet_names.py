import os
from typing import List, Optional
from app.domain.repositories.asset_data_source import IAssetDataSource

class GetSheetNamesUseCase:
    """Use case untuk mendapatkan daftar nama sheet dari sumber tertentu."""
    def __init__(self, asset_data_source: IAssetDataSource):
        self.asset_data_source = asset_data_source

    def execute(self, source: str = 'master') -> List[str]:
        """
        Menjalankan logika pengambilan nama sheet.
        source: 'master' atau 'siklus'
        """
        if source == 'siklus':
            target_id = os.getenv("GOOGLE_SHEET_ID_SIKLUS")
        else:
            target_id = os.getenv("GOOGLE_SHEET_ID_MASTER")

        return self.asset_data_source.get_sheet_names(spreadsheet_id=target_id)