import json
import pandas as pd
import re
from io import BytesIO
from datetime import datetime
from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.infrastructure.database.models import History, File

class DownloadService:
    """
    Service yang bertanggung jawab untuk membuat file unduhan (CSV atau XLSX)
    dari data yang diberikan.
    """

    def get_historical_data(self, db: Session, timestamp: str) -> Tuple[pd.DataFrame, str]:
        """
        Mengambil data historis dari database berdasarkan timestamp.
        Mengembalikan DataFrame dan bagian nama file.
        """
        target_history = db.query(History).filter(History.timestamp == timestamp).first()
        if not target_history:
            return pd.DataFrame(), ""

        json_file = db.query(File).filter(File.filename.like(f"%_{timestamp}.json")).first()
        if not json_file or not json_file.json_content:
            return pd.DataFrame(), ""

        match = re.search(r'\((.*?)\)', target_history.filename)
        filename_part = match.group(1).replace(" ", "_") if match else f"history_{timestamp}"
        
        raw_data = json.loads(json_file.json_content)
        df = pd.DataFrame(raw_data)
        
        return df, filename_part

    def create_file_buffer(
        self, df: pd.DataFrame, file_format: str, filename_part: str
    ) -> Tuple[BytesIO, str, str]:
        """
        Membuat file di dalam memori (BytesIO buffer) dari sebuah DataFrame.
        
        Returns:
            Tuple[BytesIO, str, str]: Buffer file, nama file lengkap, dan tipe media.
        """
        buffer = BytesIO()
        
        safe_filename_part = re.sub(r'[\\/*?:"<>|]', "", filename_part)
        timestamp_str = datetime.now().strftime('%Y%m%d')
        filename = f"data_aset_{safe_filename_part}_{timestamp_str}"

        media_type = ''
        if file_format == 'xlsx':
            df.to_excel(buffer, index=False, engine='openpyxl')
            filename += ".xlsx"
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif file_format == 'csv':
            df.to_csv(buffer, index=False, encoding='utf-8')
            filename += ".csv"
            media_type = 'text/csv'
        else:
            raise ValueError("Format file tidak valid. Gunakan 'csv' atau 'xlsx'.")
            
        buffer.seek(0)
        return buffer, filename, media_type