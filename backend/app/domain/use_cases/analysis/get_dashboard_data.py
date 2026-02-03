import pandas as pd
from typing import Dict, Any, Optional
from io import StringIO

from app.domain.repositories.history_repository import IHistoryRepository
from app.domain.repositories.file_repository import IFileRepository
from app.infrastructure.services.preview_state_service import PreviewStateService 
from app.infrastructure.services.chart_service import ChartService

class GetDashboardDataUseCase:
    """Use case untuk mengambil data yang akan ditampilkan di dashboard utama."""
    def __init__(
        self,
        history_repo: IHistoryRepository,
        file_repo: IFileRepository,
        preview_state_service: PreviewStateService,
        chart_service: ChartService
    ):
        self.history_repo = history_repo
        self.file_repo = file_repo
        self.preview_state_service = preview_state_service
        self.chart_service = chart_service

    def _filter_by_area(self, df: pd.DataFrame, area: str | None) -> pd.DataFrame:
        """Helper untuk memfilter DataFrame berdasarkan area."""
        if df.empty or not area or area == "Semua Area":
            return df
            
        df.columns = [str(col).strip().upper() for col in df.columns]
        if 'AREA' in df.columns:
            return df[df['AREA'] == area].copy()
        return df

    def execute(self, area: Optional[str] = None) -> Dict[str, Any]:
        """
        Menjalankan logika untuk mendapatkan data dashboard.
        Prioritas:
        1. Data dari sesi analisis sementara (preview).
        2. Jika tidak ada, data dari riwayat terakhir yang tersimpan.
        """
        latest_result = self.preview_state_service.get()
        
        if latest_result and latest_result.get("data_available"):
            full_df = latest_result["dataframe"]
            df = self._filter_by_area(full_df, area)
            chart_data = self.chart_service.create_chart_data(df)
            
            available_areas = ["Semua Area"]
            if 'AREA' in full_df.columns:
                available_areas.extend(sorted(full_df['AREA'].dropna().unique().tolist()))

            return {
                "data_available": True,
                "summary_text": latest_result["summary_text"],
                "chart_data": chart_data,
                "last_updated": latest_result["analysis_time"],
                "available_areas": available_areas,
                "is_temporary": True,
                "cycle_assets_table": latest_result["cycle_assets_table"],
                "timestamp": "temporary"
            }

        latest_history = self.history_repo.get_latest()
        if not latest_history:
            return {"data_available": False, "message": "Belum ada analisis yang disimpan ke riwayat."}

        latest_file = self.file_repo.find_by_timestamp(latest_history.timestamp)
        if not latest_file or not latest_file.json_content:
            return {"data_available": False, "message": "File data untuk riwayat terakhir tidak ditemukan."}

        try:
            full_df = pd.read_json(StringIO(latest_file.json_content))
        except (ValueError, TypeError):
            return {"data_available": False, "message": "File data untuk riwayat terakhir korup atau tidak valid."}

        df = self._filter_by_area(full_df, area)
        chart_data = self.chart_service.create_chart_data(df)

        available_areas = ["Semua Area"]
        if 'AREA' in full_df.columns:
            available_areas.extend(sorted(full_df['AREA'].dropna().unique().tolist()))
        
        return {
            "data_available": True,
            "summary_text": latest_history.summary,
            "chart_data": chart_data,
            "last_updated": latest_history.upload_date,
            "available_areas": available_areas,
            "is_temporary": False,
            "cycle_assets_table": latest_history.cycle_assets,
            "timestamp": latest_history.timestamp
        }