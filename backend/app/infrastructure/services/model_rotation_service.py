import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from google.api_core.exceptions import ResourceExhausted

class ModelRotationService:
    """
    Service untuk rotasi otomatis model dan API key dengan persistensi lokal.
    Rotasi: Setiap 4 request ganti model, setiap 1 loop (8 request) ganti API key.
    """
    
    # Konfigurasi Path untuk Azure Persistence
    # Di Azure, set ENV 'ROTATION_DATA_PATH' ke '/app/persisted'
    BASE_DIR = Path(os.getenv("ROTATION_DATA_PATH", "."))
    PERSISTENCE_FILE = BASE_DIR / "model_rotation_state.json"
    
    # Definisi model dan API keys dari environment
    MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite"
    ]
    
    API_KEYS = [
        os.getenv("GEMINI_API_KEY"),
        os.getenv("GEMINI_API_KEY_2"),
        os.getenv("GEMINI_API_KEY_3"),
        os.getenv("GEMINI_API_KEY_4")
    ]
    
    def __init__(self):
        # Pastikan directory mount tersedia
        if not self.BASE_DIR.exists():
            try:
                self.BASE_DIR.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logging.error(f"Gagal membuat direktori persistensi: {e}")

        # Muat daftar API Keys dari .env
        self.state = self._load_state()
        self._validate_config()
        
    def _validate_config(self):
        """Validasi bahwa semua API keys tersedia."""
        valid_keys = [key for key in self.API_KEYS if key]
        if len(valid_keys) < 2:
            logging.warning(
                f"Hanya {len(valid_keys)} API key yang tersedia. "
                "Sebaiknya tambahkan lebih banyak key untuk rotasi optimal."
            )
        self.API_KEYS = valid_keys
        
    def _load_state(self) -> Dict:
        """Load state dari file persisten."""
        if self.PERSISTENCE_FILE.exists():
            try:
                with open(self.PERSISTENCE_FILE, 'r') as f:
                    state = json.load(f)
                    logging.info(f"State loaded: {state}")
                    return state
            except Exception as e:
                logging.error(f"Error loading state: {e}")
        
        # Default state
        return {
            "request_count": 0,
            "model_index": 0,
            "api_key_index": 0,
            "last_rotation": datetime.now().isoformat(),
            "total_requests": 0
        }
    
    def _save_state(self):
        """Simpan state ke file persisten."""
        try:
            with open(self.PERSISTENCE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving state: {e}")
    
    def get_current_config(self) -> Tuple[str, int]:
        """
        Dapatkan model dan API key index saat ini.
        PERBAIKAN: Return (model_name, api_key_index) bukan (model_name, api_key)
        Returns: (model_name, api_key_index)
        """
        model = self.MODELS[self.state["model_index"]]
        api_key_index = self.state["api_key_index"]
        
        logging.info(
            f"Current config - Model: {model}, "
            f"API Key Index: {api_key_index}, "
            f"Request: {self.state['request_count']}/4"
        )
        
        return model, api_key_index
    
    def get_current_api_key(self) -> str:
        """
        METHOD BARU: Dapatkan API key string yang aktif saat ini.
        Returns: api_key (string)
        """
        return self.API_KEYS[self.state["api_key_index"]]
    
    def increment_and_rotate(self):
        """
        Increment counter dan lakukan rotasi jika diperlukan.
        Logika:
        - Setiap 4 request: ganti model
        - Setiap 8 request (1 loop): ganti API key
        """
        self.state["request_count"] += 1
        self.state["total_requests"] += 1
        
        # Setiap 4 request, ganti model
        if self.state["request_count"] % 4 == 0:
            self._rotate_model()
            
            # Setiap 8 request (2 model x 4 request), ganti API key
            if self.state["request_count"] % 8 == 0:
                self._rotate_api_key()
                self.state["request_count"] = 0  # Reset counter
        
        # Log progress
        logging.info(f"Request Count: {self.state['request_count']}/8 | Total Requests: {self.state['total_requests']}")
        
        self._save_state()
    
    def _rotate_model(self):
        """Rotasi ke model berikutnya."""
        old_model = self.MODELS[self.state["model_index"]]
        self.state["model_index"] = (self.state["model_index"] + 1) % len(self.MODELS)
        new_model = self.MODELS[self.state["model_index"]]
        
        logging.info("="*80)
        logging.info(f"MODEL ROTATION: {old_model} → {new_model}")
        logging.info("="*80)
    
    def _rotate_api_key(self):
        """Rotasi ke API key berikutnya."""
        old_index = self.state["api_key_index"]
        self.state["api_key_index"] = (self.state["api_key_index"] + 1) % len(self.API_KEYS)
        new_index = self.state["api_key_index"]
        
        logging.info("="*80)
        logging.info(f"API KEY ROTATION: Key#{old_index + 1} → Key#{new_index + 1}")
        logging.info(f"Rotation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("="*80)
        
        self.state["last_rotation"] = datetime.now().isoformat()
    
    def force_rotate_on_error(self, error: Exception):
        """
        Paksa rotasi saat terjadi ResourceExhausted error (429).
        Strategi: Coba model lain dulu, jika masih error, ganti API key.
        """
        if isinstance(error, ResourceExhausted):
            logging.warning("="*80)
            logging.warning("FORCING ROTATION DUE TO RESOURCE EXHAUSTED ERROR")
            logging.warning("="*80)
            
            # Coba ganti model dulu
            current_model_index = self.state["model_index"]
            self._rotate_model()
            
            # Jika sudah loop kembali ke model awal, berarti semua model di key ini exhausted
            if self.state["model_index"] == current_model_index:
                logging.warning("All models exhausted for current API key")
                logging.warning("Forcing API key rotation...")
                self._rotate_api_key()
                self.state["request_count"] = 0
            
            self._save_state()
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Dapatkan statistik penggunaan."""
        return {
            "total_requests": self.state["total_requests"],
            "current_model": self.MODELS[self.state["model_index"]],
            "current_api_key_index": self.state["api_key_index"],
            "requests_until_model_rotation": 4 - (self.state["request_count"] % 4),
            "requests_until_key_rotation": 8 - self.state["request_count"],
            "last_rotation": self.state["last_rotation"]
        }
    
    def reset_state(self):
        """Reset state ke default (untuk testing/maintenance)."""
        self.state = {
            "request_count": 0,
            "model_index": 0,
            "api_key_index": 0,
            "last_rotation": datetime.now().isoformat(),
            "total_requests": 0
        }
        self._save_state()
        logging.info("State has been reset to default")