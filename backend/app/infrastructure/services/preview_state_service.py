from typing import Dict, Any

class PreviewStateService:
    """
    Service untuk mengelola state sementara (in-memory) dari hasil analisis terakhir.
    Ini bertindak sebagai singleton sederhana untuk menyimpan data preview.
    Dalam aplikasi multi-worker, ini harus diganti dengan cache terdistribusi seperti Redis.
    """
    _instance = None
    _state: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PreviewStateService, cls).__new__(cls)
            cls._state = {}
        return cls._instance

    def set(self, analysis_result: Dict[str, Any]):
        """Menyimpan atau memperbarui state preview."""
        self.__class__._state = analysis_result

    def get(self) -> Dict[str, Any]:
        """Mengambil state preview saat ini."""
        return self.__class__._state

    def clear(self):
        """Membersihkan state preview."""
        self.__class__._state = {}