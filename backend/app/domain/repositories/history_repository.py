from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.history import History

class IHistoryRepository(ABC):
    """
    Interface abstrak untuk operasi data terkait entitas History.
    """

    @abstractmethod
    def get_by_timestamp(self, timestamp: str) -> Optional[History]:
        """
        Mengambil satu riwayat analisis berdasarkan timestamp uniknya.
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest(self) -> Optional[History]:
        """
        Mengambil riwayat analisis terbaru yang disimpan.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[History]:
        """
        Mengambil semua riwayat analisis, diurutkan dari yang terbaru.
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, history_entity: History) -> History:
        """
        Menyimpan entitas riwayat baru ke dalam penyimpanan data.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by_timestamp(self, timestamp: str) -> bool:
        """
        Menghapus satu riwayat analisis berdasarkan timestamp uniknya.
        Mengembalikan True jika berhasil, False jika tidak ditemukan.
        """
        raise NotImplementedError