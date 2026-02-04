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

def run_daily_automation():
    logger.info("=== MEMULAI EKSEKUSI TUGAS OTOMATIS HARIAN ===")
    
    # 1. Inisialisasi Database Session & Container
    db = SessionLocal()
    container = AppContainer()
    
    try:
        # 2. Pastikan tabel database sudah up-to-date
        Base.metadata.create_all(bind=engine)
        logger.info("Koneksi database stabil dan skema diverifikasi.")

        # 3. Definisikan Opsi Analisis (Misal: Refresh Dashboard Total)
        options = AnalysisOptions(
            data_overview=True,
            summarize=True,
            insight=True,
            check_duplicates=True,
            financial_analysis=True,
            sheet_name="MasterDataAsset" # Sesuaikan dengan sheet utama Anda
        )

        # 4. Ambil Use Case dari Container
        trigger_use_case = container.get_use_case("trigger_analysis", db)
        
        logger.info("Menjalankan analisis data otomatis (LLM Call)...")

        # Callback sederhana untuk logging progress di Azure
        def log_progress(progress):
            logger.info(f"Progress: {progress.get('message')}")

        # Jalankan Use Case
        trigger_use_case.execute(options=options, progress_callback=log_progress)

        # 5. (Opsional) Simpan hasil analisis ke Riwayat jika diperlukan secara otomatis
        logger.info("Menyimpan hasil analisis harian ke tabel history...")
        save_use_case = container.get_use_case("save_latest_analysis", db)
        result = save_use_case.execute(current_user=None)
        
        logger.info(f"=== PROSES BERHASIL DISELESAIKAN PADA {datetime.now(pytz.timezone('Asia/Jakarta'))} ===")

    except Exception as e:
        logger.error(f"FATAL ERROR saat menjalankan Job: {str(e)}", exc_info=True)
        # Keluar dengan status 1 agar Azure menandai Job ini sebagai 'Failed'
        sys.exit(1)
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    run_daily_automation()