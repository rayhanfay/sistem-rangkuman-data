import pandas as pd
from typing import Dict, Any, Optional
from io import StringIO

from app.domain.repositories.history_repository import IHistoryRepository
from app.domain.repositories.file_repository import IFileRepository
from app.infrastructure.services.preview_state_service import PreviewStateService
from app.infrastructure.services.chart_service import ChartService

class GetStatsDataUseCase:
    """Use case untuk mengambil data statistik detail untuk halaman Statistik."""
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

    def execute(self, timestamp: Optional[str] = None, area: Optional[str] = None) -> Dict[str, Any]:
        """
        Menjalankan logika untuk mendapatkan data statistik.
        Jika timestamp tidak diberikan, ambil data terbaru yang tersedia.
        Jika diberikan, ambil dari riwayat yang spesifik.
        """
        if timestamp and timestamp != "temporary":
            return self._get_specific_history(timestamp, area)
        else:
            return self._get_latest_available_data(area)

    def _get_latest_available_data(self, area: str | None) -> Dict[str, Any]:
        """Mengambil data terbaru, memprioritaskan state preview."""
        latest_result = self.preview_state_service.get()
        if latest_result and latest_result.get("data_available"):
            return self._format_preview_data(latest_result, area)

        latest_history = self.history_repo.get_latest()
        if not latest_history:
            raise FileNotFoundError("Tidak ada data analisis yang tersedia, baik sementara maupun tersimpan.")
        
        return self._get_specific_history(latest_history.timestamp, area)

    def _get_specific_history(self, timestamp: str, area: str | None) -> Dict[str, Any]:
        """Mengambil dan memformat data dari riwayat berdasarkan timestamp."""
        target_history = self.history_repo.get_by_timestamp(timestamp)
        if not target_history:
            raise FileNotFoundError(f"Riwayat analisis dengan timestamp '{timestamp}' tidak ditemukan.")

        json_file_entry = self.file_repo.find_by_timestamp(target_history.timestamp)
        if not json_file_entry or not json_file_entry.json_content:
            raise FileNotFoundError("File data mentah untuk riwayat ini tidak ditemukan.")

        try:
            full_df = pd.read_json(StringIO(json_file_entry.json_content))
        except (ValueError, TypeError):
            raise ValueError("File data untuk riwayat ini korup atau tidak valid.")

        if full_df.empty:
            return {"data_available": False, "error_message": "Data analisis kosong."}

        df = self._filter_by_area(full_df, area)
        available_areas = ["Semua Area"]
        if 'AREA' in full_df.columns:
            available_areas.extend(sorted(full_df['AREA'].dropna().unique().tolist()))

        return {
            "data_available": True,
            "summary_text": target_history.summary,
            "table_data": df.to_dict(orient='records'),
            "chart_data": self.chart_service.create_chart_data(df),
            "timestamp": target_history.timestamp,
            "sheet_name": target_history.sheet_name,
            "available_areas": available_areas,
            "cycle_assets_table": target_history.cycle_assets,
            "is_temporary": False
        }

    def _format_preview_data(self, preview_data: Dict, area: str | None) -> Dict[str, Any]:
        """Memformat data dari state preview."""
        full_df = preview_data["dataframe"]
        df = self._filter_by_area(full_df, area)
        
        available_areas = ["Semua Area"]
        if 'AREA' in full_df.columns:
            available_areas.extend(sorted(full_df['AREA'].dropna().unique().tolist()))

        return {
            "data_available": True,
            "summary_text": preview_data["summary_text"],
            "table_data": df.to_dict(orient='records'),
            "chart_data": self.chart_service.create_chart_data(df),
            "timestamp": "Analisis Saat Ini (Belum Disimpan)",
            "sheet_name": preview_data["options"].get('sheet_name') or 'MASTER-SHEET', 
            "available_areas": available_areas,
            "cycle_assets_table": preview_data["cycle_assets_table"],
            "is_temporary": True
        }