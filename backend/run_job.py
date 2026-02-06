import os
import sys
import logging
from datetime import datetime
import pytz

# Menambahkan path agar bisa membaca modul 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.database.database import SessionLocal, engine, Base
from app.dependencies import AppContainer
from app.presentation.schemas import AnalysisOptions

# Konfigurasi Logging agar mudah dibaca di Azure Log Stream
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [AZURE-JOB] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_current_cycle_sheet():
    """
    Menghitung nama sheet berdasarkan bulan dan tahun saat ini.
    Timeline PHR:
    - Jan - April: Cycle 1
    - Mei - Agustus: Cycle 2
    - September - Desember: Cycle 3
    """
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    month = now.month
    year = now.year
    
    if 1 <= month <= 4:
        cycle = 1
    elif 5 <= month <= 8:
        cycle = 2
    else:
        cycle = 3
        
    # Format: CYCLE-1-YEAR-2026
    return f"CYCLE-{cycle}-YEAR-{year}"

def run_daily_automation():
    logger.info("=== MEMULAI EKSEKUSI TUGAS OTOMATIS HARIAN ===")
    db = SessionLocal()
    container = AppContainer()
    
    try:
        # 1. Pastikan tabel database sinkron
        Base.metadata.create_all(bind=engine)
        logger.info("Koneksi database stabil dan skema diverifikasi.")

        # 2. Tentukan sheet berdasarkan waktu saat ini
        target_sheet = get_current_cycle_sheet()
        logger.info(f"Target Otomasi Hari Ini: {target_sheet} (Sumber: SIKLUS)")

        # 3. Definisikan Opsi Analisis (PENTING: source="siklus")
        options = AnalysisOptions(
            source="siklus", 
            data_overview=True,
            summarize=True,
            insight=True,
            check_duplicates=True,
            financial_analysis=True,
            sheet_name=target_sheet 
        )

        # 4. Ambil Use Case dari Container
        trigger_use_case = container.get_use_case("trigger_analysis", db)
        
        logger.info(f"Menjalankan analisis data {target_sheet} (LLM Call)...")

        # Callback sederhana untuk logging progress di Azure
        def log_progress(progress):
            logger.info(f"Progress: {progress.get('message')}")

        # Jalankan Proses Analisis
        trigger_use_case.execute(options=options, progress_callback=log_progress)

        # 5. Simpan hasil analisis ke tabel history secara otomatis
        logger.info("Menyimpan hasil analisis harian ke tabel history...")
        save_use_case = container.get_use_case("save_latest_analysis", db)
        
        result = save_use_case.execute(current_user=None)
        
        logger.info(f"=== PROSES BERHASIL DISELESAIKAN PADA {datetime.now(pytz.timezone('Asia/Jakarta'))} ===")
        logger.info(f"ID Riwayat: {result.timestamp}")

    except Exception as e:
        logger.error(f"FATAL ERROR saat menjalankan Job: {str(e)}", exc_info=True)
        # Keluar dengan status 1 agar Azure menandai Job ini sebagai 'Failed'
        sys.exit(1)
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    run_daily_automation()