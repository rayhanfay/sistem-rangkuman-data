import os
import pandas as pd
import time
from typing import List
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.api_core.exceptions import GoogleAPIError

from app.config import settings
from app.domain.repositories.asset_data_source import IAssetDataSource

class GoogleSheetsAssetDataSource(IAssetDataSource):
    """
    Implementasi konkret dari IAssetDataSource yang mengambil data dari Google Sheets.
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    COL_NO_ASET = 'NO ASSET'
    COL_KONDISI = 'KONDISI'

    def __init__(self):
        self.sheet = self._initialize_service()

    def _initialize_service(self):
        """Menginisialisasi koneksi ke Google Sheets API via Env Var."""
        try:
            # Ambil string JSON dari environment variable
            creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
            
            if creds_json:
                # Jika ada di Env Var (untuk Produksi/Azure)
                creds_info = json.loads(creds_json)
                creds = service_account.Credentials.from_service_account_info(
                    creds_info, scopes=self.SCOPES
                )
                print("[INFO] Google Sheets initialized via Environment Variable.")
            elif os.path.exists(self.SERVICE_ACCOUNT_FILE):
                # Fallback ke file lokal (untuk Development)
                creds = service_account.Credentials.from_service_account_file(
                    self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES
                )
                print("[INFO] Google Sheets initialized via local file.")
            else:
                raise FileNotFoundError("Google Credentials tidak ditemukan di Env Var maupun file lokal.")
            
            service = build('sheets', 'v4', credentials=creds)
            return service.spreadsheets()
        except Exception as e:
            print(f"[FATAL] Gagal menginisialisasi Google Sheets service: {e}")
            raise

    def get_sheet_names(self) -> List[str]:
        """Mengambil semua nama sheet dari spreadsheet yang dikonfigurasi."""
        if not self.sheet:
            raise ConnectionError("Google Sheets service tidak terinisialisasi.")
        
        retries = 3
        delay = 2
        for attempt in range(retries):
            try:
                sheet_metadata = self.sheet.get(spreadsheetId=settings.GOOGLE_SHEET_ID).execute()
                sheets = sheet_metadata.get('sheets', [])
                return [sheet.get('properties', {}).get('title', '') for sheet in sheets]
            except GoogleAPIError as e:
                print(f"[API-ERROR] Google API Error pada percobaan {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise ConnectionError(f"Gagal mengambil daftar sheet setelah {retries} percobaan.")
        return []

    def fetch_data(self, sheet_name: str | None) -> pd.DataFrame:
        """Mengambil data dari sheet tertentu dan mengubahnya menjadi DataFrame."""
        if not self.sheet:
            raise ConnectionError("Google Sheets service tidak terinisialisasi.")
        
        target_sheet = sheet_name or 'MasterDataAsset'
        range_name = f"'{target_sheet}'!A:Z"
        print(f"[INFO] Mengambil data dari Google Sheet: {range_name}...")
        
        try:
            result = self.sheet.values().get(
                spreadsheetId=settings.GOOGLE_SHEET_ID, range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                print(f"[WARN] Sheet '{target_sheet}' kosong.")
                return pd.DataFrame()

            header, header_row_index = self._find_header_row(values)
            if header_row_index == -1:
                print(f"[WARN] Header dengan kolom kunci tidak ditemukan di sheet '{target_sheet}'.")
                return pd.DataFrame()

            data_rows = values[header_row_index + 1:]
            clean_data = [row for row in data_rows if any(str(cell).strip() for cell in row)]
            if not clean_data:
                return pd.DataFrame()

            unique_header = self._make_unique_columns([' '.join(str(col).strip().split()) for col in header])
            df = pd.DataFrame(clean_data)
            
            num_header_cols = len(unique_header)
            df = df.iloc[:, :num_header_cols]
            
            df.columns = unique_header
            print(f"[INFO] DataFrame dibuat dengan {len(df)} baris dari sheet '{target_sheet}'.")
            return df
        except GoogleAPIError as e:
            raise ConnectionError(f"Gagal mengakses Google Sheet '{target_sheet}': {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Terjadi error tak terduga saat mengambil data: {e}")

    def _find_header_row(self, values: List[List[str]]):
        """Mencari baris yang berisi kolom kunci sebagai header."""
        key_header_columns = {self.COL_NO_ASET, self.COL_KONDISI}
        for i, row in enumerate(values):
            row_content = {str(cell).strip().upper() for cell in row if str(cell).strip()}
            if key_header_columns.issubset(row_content):
                return row, i
        return [], -1

    def _make_unique_columns(self, columns: List[str]) -> List[str]:
        """Memastikan setiap nama kolom unik untuk menghindari error di Pandas."""
        seen = {}
        new_columns = []
        for col in columns:
            original_col = col
            count = seen.get(original_col, 0)
            if count > 0:
                col = f"{original_col}_{count}"
            seen[original_col] = count + 1
            new_columns.append(col)
        return new_columns