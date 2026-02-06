import os
import pandas as pd
from typing import List, Dict, Any, Optional
from app.domain.repositories.asset_data_source import IAssetDataSource

class GetMasterDataUseCase:
    """Use case untuk mengambil seluruh data mentah dari sumber tertentu."""
    def __init__(self, asset_data_source: IAssetDataSource):
        self.asset_data_source = asset_data_source

    def execute(self, sheet_name: Optional[str] = None, source: str = 'master') -> List[Dict[str, Any]]:
        """
        Mengambil data mentah dan mengembalikannya dalam bentuk list of dict (JSON-ready).
        """
        if source == 'siklus':
            target_id = os.getenv("GOOGLE_SHEET_ID_SIKLUS")
            default_sheet = 'CYCLE-1-YEAR-2026' 
        else:
            target_id = os.getenv("GOOGLE_SHEET_ID_MASTER")
            default_sheet = 'MASTER-SHEET'

        target_sheet = sheet_name or default_sheet
        
        df = self.asset_data_source.fetch_data(target_sheet, spreadsheet_id=target_id)
        
        if df.empty:
            return []
            
        return df.to_dict(orient='records')