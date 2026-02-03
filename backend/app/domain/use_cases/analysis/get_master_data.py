import pandas as pd
from typing import List, Dict, Any
from app.domain.repositories.asset_data_source import IAssetDataSource

class GetMasterDataUseCase:
    """Use case untuk mengambil data mentah dari sumber data aset."""
    def __init__(self, asset_data_source: IAssetDataSource):
        self.asset_data_source = asset_data_source

    def execute(self, sheet_name: str) -> List[Dict[str, Any]]:
        """Mengambil data dari sheet yang ditentukan dan mengubahnya menjadi format JSON."""
        df = self.asset_data_source.fetch_data(sheet_name)
        if df.empty:
            return []
        
        df_cleaned = df.replace({pd.NaT: None, pd.NA: None}).where(pd.notna(df), None)
        return df_cleaned.to_dict(orient='records')