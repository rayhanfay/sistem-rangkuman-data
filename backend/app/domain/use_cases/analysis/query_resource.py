import pandas as pd
from typing import List, Dict, Any, Optional
from io import StringIO

from app.domain.repositories.file_repository import IFileRepository

class QueryResourceUseCase:
    """
    Use case untuk melakukan query (pencarian/filter) di dalam konten file 
    resource (hasil analisis .json) yang sudah tersimpan.
    """
    def __init__(self, file_repo: IFileRepository):
        self.file_repo = file_repo

    def execute(self, resource_name: str, kondisi: Optional[str] = None, area: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Mencari file resource berdasarkan nama, memuatnya, dan memfilternya.
        """
        file_entity = self.file_repo.find_by_filename(resource_name)
        if not file_entity or not file_entity.json_content:
            return [{"status": f"Resource dengan nama '{resource_name}' tidak ditemukan."}]

        try:
            df = pd.read_json(StringIO(file_entity.json_content))
        except Exception:
            return [{"status": f"Gagal memproses konten dari resource '{resource_name}'."}]
        
        if df.empty:
            return []

        if area and 'AREA' in df.columns:
            df = df[df['AREA'].str.contains(area, case=False, na=False)]
        if kondisi and 'KONDISI' in df.columns:
            df = df[df['KONDISI'].str.contains(kondisi, case=False, na=False)]

        if df.empty:
            return [{"status": "Tidak ada data yang cocok dengan kriteria di dalam resource ini."}]
            
        df_cleaned = df.replace({pd.NaT: None, pd.NA: None}).where(pd.notna(df), None)
        return df_cleaned.to_dict(orient='records')