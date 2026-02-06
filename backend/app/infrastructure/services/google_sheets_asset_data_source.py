import os
import pandas as pd
import time
import json
import logging
from typing import List, Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.api_core.exceptions import GoogleAPIError

from app.config import settings
from app.domain.repositories.asset_data_source import IAssetDataSource

class GoogleSheetsAssetDataSource(IAssetDataSource):
    """
    Implementasi IAssetDataSource yang mendukung multi-spreadsheet (Master & Siklus)
    dan penanganan nama sheet dinamis dengan proteksi Length Mismatch.
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    COL_NO_ASET = 'NO ASSET'
    COL_KONDISI = 'KONDISI'

    def __init__(self):
        self.sheet = self._initialize_service()
        # Mengambil ID dari Environment Variables
        self.master_spreadsheet_id = os.getenv("GOOGLE_SHEET_ID_MASTER") or settings.GOOGLE_SHEET_ID
        self.siklus_spreadsheet_id = os.getenv("GOOGLE_SHEET_ID_SIKLUS")

    def _initialize_service(self):
        """Menginisialisasi koneksi ke Google Sheets API."""
        try:
            creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
            
            if creds_json:
                creds_info = json.loads(creds_json)
                creds = service_account.Credentials.from_service_account_info(
                    creds_info, scopes=self.SCOPES
                )
                logging.info("[INFO] Google Sheets service initialized via Env Var.")
            elif os.path.exists(self.SERVICE_ACCOUNT_FILE):
                creds = service_account.Credentials.from_service_account_file(
                    self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES
                )
                logging.info("[INFO] Google Sheets service initialized via local file.")
            else:
                raise FileNotFoundError("Credentials Google tidak ditemukan.")
            
            service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
            return service.spreadsheets()
        except Exception as e:
            logging.error(f"[FATAL] Gagal inisialisasi Google Sheets: {e}")
            raise

    def get_sheet_names(self, spreadsheet_id: Optional[str] = None) -> List[str]:
        """Mengambil semua nama sheet dari ID spreadsheet tertentu."""
        if not self.sheet:
            raise ConnectionError("Service Google Sheets tidak aktif.")
        
        target_id = spreadsheet_id or self.master_spreadsheet_id
        
        retries = 3
        for attempt in range(retries):
            try:
                sheet_metadata = self.sheet.get(spreadsheetId=target_id).execute()
                sheets = sheet_metadata.get('sheets', [])
                return [sheet.get('properties', {}).get('title', '') for sheet in sheets]
            except GoogleAPIError as e:
                logging.error(f"[API-ERROR] Percobaan {attempt + 1} gagal: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    raise ConnectionError(f"Gagal mengambil nama sheet dari ID {target_id}")
        return []

    def fetch_data(self, sheet_name: Optional[str], spreadsheet_id: Optional[str] = None) -> pd.DataFrame:
        """
        Mengambil data dengan proteksi otomatis terhadap perbedaan jumlah kolom (Length Mismatch).
        """
        if not self.sheet:
            raise ConnectionError("Service Google Sheets tidak aktif.")
        
        target_sheet = sheet_name or 'MASTER-SHEET'
        target_id = spreadsheet_id or self.master_spreadsheet_id
        
        # Ambil range yang luas (A sampai Z atau lebih jika perlu)
        range_name = f"'{target_sheet}'!A:Z"
        logging.info(f"[FETCH] Membaca Spreadsheet: {target_id} | Sheet: {target_sheet}")
        
        try:
            result = self.sheet.values().get(
                spreadsheetId=target_id, range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logging.warning(f"Sheet '{target_sheet}' kosong.")
                return pd.DataFrame()

            # 1. Cari baris Header
            header, header_row_index = self._find_header_row(values)
            if header_row_index == -1:
                logging.warning(f"Header kunci tidak ditemukan di sheet '{target_sheet}'.")
                return pd.DataFrame()

            # 2. Proses Nama Kolom agar Unik
            unique_header = self._make_unique_columns([' '.join(str(col).strip().split()) for col in header])
            num_expected_cols = len(unique_header)

            # 3. Proses Baris Data (setelah index header)
            data_rows = values[header_row_index + 1:]
            
            # 4. PERBAIKAN KRITIS: Normalisasi panjang baris
            # Google API memotong sel kosong di akhir baris. Kita harus menambahkannya kembali.
            normalized_data = []
            for row in data_rows:
                # Lewati baris yang benar-benar kosong
                if not any(str(cell).strip() for cell in row):
                    continue
                
                # Jika baris lebih pendek dari header, tambahkan None (sel kosong)
                if len(row) < num_expected_cols:
                    row.extend([None] * (num_expected_cols - len(row)))
                
                # Jika baris lebih panjang dari header, potong agar pas
                normalized_data.append(row[:num_expected_cols])
            
            if not normalized_data:
                logging.warning(f"Tidak ada data valid ditemukan di bawah header sheet '{target_sheet}'.")
                return pd.DataFrame()

            # 5. Buat DataFrame
            df = pd.DataFrame(normalized_data, columns=unique_header)
            
            logging.info(f"[SUCCESS] Berhasil memuat {len(df)} baris dari {target_sheet} (Kolom: {num_expected_cols}).")
            return df
            
        except Exception as e:
            logging.error(f"[ERROR] fetch_data failed: {str(e)}")
            # Berikan error yang lebih informatif untuk debugging
            raise RuntimeError(f"Gagal memproses sheet '{target_sheet}': {str(e)}")

    def _find_header_row(self, values: List[List[str]]) -> Tuple[List[str], int]:
        """Mencari baris header berdasarkan kolom kunci (NO ASSET & KONDISI)."""
        key_header_columns = {self.COL_NO_ASET, self.COL_KONDISI}
        for i, row in enumerate(values):
            row_content = {str(cell).strip().upper() for cell in row if str(cell).strip()}
            if key_header_columns.issubset(row_content):
                return row, i
        return [], -1

    def _make_unique_columns(self, columns: List[str]) -> List[str]:
        """Mencegah duplikasi nama kolom agar tidak error di Pandas."""
        seen = {}
        new_columns = []
        for col in columns:
            if not col: # Jika nama kolom kosong, beri nama default
                col = "UNTITLED_COLUMN"
                
            original_col = col
            count = seen.get(original_col, 0)
            if count > 0:
                col = f"{original_col}_{count}"
            seen[original_col] = count + 1
            new_columns.append(col)
        return new_columns