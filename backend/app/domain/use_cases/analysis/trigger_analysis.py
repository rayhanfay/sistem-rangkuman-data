import traceback
from datetime import datetime
import pytz
from typing import Callable, Dict, List, Any
import pandas as pd
import logging
import json

from app.domain.repositories.asset_data_source import IAssetDataSource
from app.infrastructure.services.document_analyzer import DocumentAnalyzer
from app.infrastructure.services.preview_state_service import PreviewStateService
from app.infrastructure.services.chart_service import ChartService
from app.presentation.schemas import AnalysisOptions

class TriggerAnalysisUseCase:
    """Use case untuk memicu proses analisis data aset."""
    def __init__(
        self,
        asset_data_source: IAssetDataSource,
        document_analyzer: DocumentAnalyzer,
        preview_state_service: PreviewStateService,
        chart_service: ChartService
    ):
        self.asset_data_source = asset_data_source
        self.document_analyzer = document_analyzer
        self.preview_state_service = preview_state_service
        self.chart_service = chart_service
        self.wib_timezone = pytz.timezone('Asia/Jakarta')
        self.REQUIRED_CYCLE_COLS = ['NO', 'NO ASSET', 'NAMA ASET', 'KONDISI', 'KETERANGAN', 'LOKASI SPESIFIK PER-INVENTORY', 'TANGGAL UPDATE', 'AREA']

    def _get_cycle_assets_table(self, assets_df: pd.DataFrame) -> List[Dict[str, Any]]:
        try:
            existing_cols = [col for col in self.REQUIRED_CYCLE_COLS if col in assets_df.columns]
            if not all(k in existing_cols for k in ['KONDISI', 'KETERANGAN']): 
                return []
            
            problem_keywords = ['Rusak', 'Penghapusan', 'Ditemukan']
            kondisi_filter = assets_df['KONDISI'].str.contains('|'.join(problem_keywords), case=False, na=False)
            keterangan_filter = ~assets_df['KETERANGAN'].isin(['-', '', None])
            exclusion_keywords = ['Digunakan', 'Cadangan', 'Baik']
            exclusion_filter = ~assets_df['KONDISI'].isin(exclusion_keywords)
            
            recommended_df = assets_df[(kondisi_filter | keterangan_filter) & exclusion_filter].copy()
            return recommended_df[existing_cols].to_dict(orient='records')
        except Exception as e:
            logging.error(f"[ERROR] Gagal saat memfilter tabel siklus aset: {e}")
            return []

    def _create_data_overview(self, df: pd.DataFrame, options: AnalysisOptions, sheet_name: str) -> str:
        if df.empty: 
            return ""
        
        total_rows = len(df)
        num_areas = df['AREA'].nunique() if 'AREA' in df.columns else 'N/A'
        date_col = 'TANGGAL UPDATE'
        
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            min_date_val, max_date_val = df[date_col].min(), df[date_col].max()
            min_date = min_date_val.strftime('%d %B %Y') if pd.notna(min_date_val) else 'N/A'
            max_date = max_date_val.strftime('%d %B %Y') if pd.notna(max_date_val) else 'N/A'
            date_range = f"{min_date} hingga {max_date}"
        else: 
            date_range = "Informasi tanggal tidak tersedia"
        
        overview_parts = [
            "DATA OVERVIEW",
            f"\n- Sumber Data: Sheet '{sheet_name}'",
            f"- Jumlah Total Aset: {total_rows} unit",
            f"- Jumlah Area Unik: {num_areas}",
            f"- Rentang Waktu Data (berdasarkan Tgl. Update): {date_range}"
        ]
        return "\n".join(overview_parts)

    def _calculate_financial_summary(self, df: pd.DataFrame) -> List[Dict]:
        if 'AREA' not in df.columns or 'NILAI ASET' not in df.columns or 'NAMA ASET' not in df.columns: 
            return []
        
        df_copy = df.copy()
        df_copy['NILAI ASET'] = pd.to_numeric(df_copy['NILAI ASET'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
        summary = []
        
        for area, group in df_copy.groupby('AREA'):
            if group.empty or pd.isna(area): 
                continue
            
            total_value = group['NILAI ASET'].sum()
            max_row = group.loc[group['NILAI ASET'].idxmax()]
            asset_termahal = {"nama": max_row.get('NAMA ASET', 'N/A'), "nilai": max_row['NILAI ASET']}
            
            non_zero_assets = group[group['NILAI ASET'] > 0]
            if not non_zero_assets.empty:
                min_row = non_zero_assets.loc[non_zero_assets['NILAI ASET'].idxmin()]
                asset_termurah = {"nama": min_row.get('NAMA ASET', 'N/A'), "nilai": min_row['NILAI ASET']}
            else: 
                asset_termurah = {"nama": "N/A", "nilai": 0}
            
            summary.append({
                "area": area, 
                "total_value": total_value, 
                "asset_termahal": asset_termahal, 
                "asset_termurah": asset_termurah
            })
        
        return summary
    
    def _format_financial_summary_to_text(self, summary_data: List[Dict]) -> str:
        if not summary_data: 
            return ""
        
        text_parts = ["ANALISA KEUANGAN ASET"]
        for item in summary_data:
            area_text = (
                f"\nArea {item['area']}:\n"
                f"- Total Nilai Aset: Rp {item['total_value']:,.0f}\n"
                f"- Aset Termahal: {item['asset_termahal']['nama']} (Rp {item['asset_termahal']['nilai']:,.0f})\n"
                f"- Aset Termurah: {item['asset_termurah']['nama']} (Rp {item['asset_termurah']['nilai']:,.0f})"
            )
            text_parts.append(area_text)
        
        return "\n".join(text_parts)

    def _calculate_asset_condition_summary(self, df: pd.DataFrame) -> str:
        if 'AREA' not in df.columns or 'KONDISI' not in df.columns: 
            return ""
        
        text_parts = ["INSIGHT UTAMA"]
        df_copy = df.copy()
        df_copy['KONDISI'] = df_copy['KONDISI'].astype(str)
        
        summary = df_copy.groupby('AREA').agg(
            total_assets=('AREA', 'size'),
            baik=('KONDISI', lambda x: x.str.contains('Baik', case=False, na=False).sum()),
            digunakan=('KONDISI', lambda x: x.str.contains('Digunakan', case=False, na=False).sum()),
            cadangan=('KONDISI', lambda x: x.str.contains('Cadangan', case=False, na=False).sum()),
            rusak_ringan=('KONDISI', lambda x: x.str.contains('Rusak Ringan', case=False, na=False).sum()),
            rusak_berat=('KONDISI', lambda x: x.str.contains('Rusak Berat', case=False, na=False).sum()),
            tidak_ditemukan=('KONDISI', lambda x: x.str.contains('Tidak Ditemukan', case=False, na=False).sum()),
            penghapusan=('KONDISI', lambda x: x.str.contains('Penghapusan', case=False, na=False).sum())
        ).reset_index()
        
        for _, row in summary.iterrows():
            area_text = (
                f"\nArea {row['AREA']}:\n"
                f"- Total Aset: {row['total_assets']}\n"
                f"- Kondisi Baik: {int(row['baik'])}\n"
                f"- Digunakan: {int(row['digunakan'])}\n"
                f"- Cadangan: {int(row['cadangan'])}\n"
                f"- Rusak Ringan: {int(row['rusak_ringan'])}\n"
                f"- Rusak Berat: {int(row['rusak_berat'])}\n"
                f"- Tidak Ditemukan: {int(row['tidak_ditemukan'])}\n"
                f"- Penghapusan: {int(row['penghapusan'])}"
            )
            text_parts.append(area_text)
        
        return "\n".join(text_parts)

    def execute(self, options: AnalysisOptions, progress_callback: Callable[[Dict], None]):
        """Menjalankan seluruh alur analisis dan melaporkan progres melalui callback."""
        try:
            def send_progress(status: str, message: str):
                progress_callback({"status": status, "message": message})

            available_sheets = self.asset_data_source.get_sheet_names()
            requested_sheet = options.sheet_name
            
            if requested_sheet and requested_sheet in available_sheets:
                sheet_to_analyze = requested_sheet
            else:
                sheet_to_analyze = 'MasterDataAsset'
                if requested_sheet:
                    logging.warning(f"Sheet '{requested_sheet}' tidak ditemukan, menggunakan default 'MasterDataAsset'.")

            send_progress("starting", f"Analisis untuk sheet '{sheet_to_analyze}' telah dimulai...")
            
            df = self.asset_data_source.fetch_data(sheet_to_analyze)
            if df.empty:
                raise ValueError(f"Tidak ada data di sheet '{sheet_to_analyze}'.")

            df.columns = [str(col).strip().upper() for col in df.columns]
            
            send_progress("progress", "Memproses data dan menjalankan analisis...")
            
            report_parts = []
            
            if options.data_overview:
                report_parts.append(self._create_data_overview(df, options, sheet_to_analyze))

            cycle_assets_table = self._get_cycle_assets_table(df)
            document_text = df.to_string()
            
            # ========================================
            # PERBAIKAN UTAMA: Evaluasi Summary
            # ========================================
            if options.summarize:
                send_progress("progress", "Menghubungi AI untuk membuat Ringkasan Eksekutif...")
                
                print("\n" + "="*80)
                print(">>> DASHBOARD ANALYSIS - LLM CALL #1: GENERATING SUMMARY")
                print("="*80)
                
                # LLM Call #1: Generate Summary
                summary_text = self.document_analyzer.generate_summary(document_text)
                
                print(f">>> Summary created: {len(summary_text)} characters")
                report_parts.append(summary_text)

                # --- EVALUASI DASHBOARD DINONAKTIFKAN UNTUK PRODUKSI ---
                # print("-"*80)
                # print(">>> DASHBOARD ANALYSIS - LLM CALL #2: EVALUATING SUMMARY")
                # print("-"*80)

                # LLM Call #2: Evaluate Summary
                # evaluation_result = self.document_analyzer.evaluate_summary_factualness(
                #     source_document=document_text,
                #     summary_to_evaluate=summary_text,
                #     user_prompt="Ringkasan eksekutif dari keseluruhan data untuk dashboard."
                # )
                
                # print("\n" + "="*80)
                # print(">>> DASHBOARD EVALUATION RESULT:")
                # print("="*80)
                # is_correct = evaluation_result.get('factual_accuracy', {}).get('is_correct')
                # print(f"Factual Accuracy: {'CORRECT ✓' if is_correct else 'INCORRECT ✗'}")
                # print(f"Completeness: {evaluation_result.get('completeness_score', 'N/A')}/5")
                # print(f"Relevance: {evaluation_result.get('relevance_score', 'N/A')}/5")
                # print(f"Final Score: {evaluation_result.get('final_score', 'N/A')}")
                # print(f"Reasoning: {evaluation_result.get('reasoning', 'N/A')}")
                # notes = evaluation_result.get('factual_accuracy', {}).get('notes', [])
                # if notes:
                #     print(f"Notes: {', '.join(notes)}")
                # print("="*80 + "\n")

            if 'AREA' in df.columns:
                if options.insight:
                    insight_text = self._calculate_asset_condition_summary(df)
                    if insight_text: 
                        report_parts.append(insight_text)
                
                if options.financial_analysis:
                    financial_summary_data = self._calculate_financial_summary(df)
                    financial_summary_text = self._format_financial_summary_to_text(financial_summary_data)
                    if financial_summary_text: 
                        report_parts.append(financial_summary_text)
            else:
                if options.insight or options.financial_analysis:
                    send_progress("progress", "Peringatan: Kolom 'AREA' tidak ditemukan, beberapa analisis dilewati.")

            if options.check_duplicates:
                report_parts.append(self.document_analyzer.generate_duplicate_report(df))
            
            final_html = self.document_analyzer.format_summary_to_html("\n\n".join(filter(None, report_parts)).strip())
            
            final_options = options.dict()
            final_options['sheet_name'] = sheet_to_analyze

            analysis_result = {
                "data_available": True, 
                "dataframe": df, 
                "summary_text": final_html,
                "chart_data": self.chart_service.create_chart_data(df),
                "cycle_assets_table": cycle_assets_table,
                "options": final_options,
                "analysis_time": datetime.now(self.wib_timezone),
            }
            
            self.preview_state_service.set(analysis_result)
            send_progress("completed", "Analisis berhasil diselesaikan.")
            return

        except Exception as e:
            error_message = f"Terjadi kesalahan fatal saat analisis: {e}"
            progress_callback({"status": "error", "message": error_message})
            traceback.print_exc()
            self.preview_state_service.set({"data_available": False, "message": error_message})
            raise e