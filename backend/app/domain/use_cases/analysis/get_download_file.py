from typing import Tuple, Optional
from io import BytesIO
from sqlalchemy.orm import Session
import pandas as pd

from app.domain.repositories.asset_data_source import IAssetDataSource
from app.infrastructure.services.download_service import DownloadService

class GetDownloadFileUseCase:
    """Use case untuk mempersiapkan dan membuat file unduhan (CSV/XLSX)."""
    def __init__(
        self,
        db: Session, 
        asset_data_source: IAssetDataSource,
        download_service: DownloadService
    ):
        self.db = db
        self.asset_data_source = asset_data_source
        self.download_service = download_service

    def execute(
        self,
        file_format: str,
        source: str,
        timestamp: Optional[str],
        area: Optional[str],
        sheet_name: Optional[str]
    ) -> Tuple[BytesIO, str, str]:
        """
        Menjalankan logika untuk membuat file unduhan.
        Mengembalikan buffer file, nama file, dan tipe media.
        """
        if source == 'temporary':
            df = self.asset_data_source.fetch_data(sheet_name)
            if df.empty:
                raise ValueError(f"Tidak ada data sementara untuk diunduh dari sheet '{sheet_name or 'Default'}'.")
            
            filename_part = sheet_name if sheet_name and sheet_name.strip() else 'MasterDataAsset'

        elif source == 'history':
            if not timestamp:
                raise ValueError("Timestamp diperlukan untuk mengunduh data riwayat.")
            
            df, filename_part = self.download_service.get_historical_data(self.db, timestamp)
            if df.empty:
                raise FileNotFoundError(f"Data riwayat untuk timestamp '{timestamp}' tidak ditemukan atau kosong.")
        
        else:
            raise ValueError("Sumber data tidak valid. Gunakan 'temporary' atau 'history'.")

        if 'AREA' in df.columns:
            df.columns = [str(col).strip().upper() for col in df.columns]
            if area and area != "Semua Area":
                df = df[df['AREA'] == area].copy()
        
        if df.empty:
            raise ValueError(f"Tidak ada data yang cocok dengan area '{area}'.")

        return self.download_service.create_file_buffer(df, file_format, filename_part)