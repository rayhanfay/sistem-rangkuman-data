from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.file import File

class IFileRepository(ABC):
    """
    Interface abstrak untuk operasi data terkait entitas File.
    """

    @abstractmethod
    def find_by_timestamp(self, timestamp: str) -> Optional[File]:
        """
        Menemukan file data mentah yang terkait dengan sebuah timestamp analisis.
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, file_entity: File) -> File:
        """
        Menyimpan entitas file baru ke dalam penyimpanan data.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by_timestamp(self, timestamp: str) -> bool:
        """
        Menghapus file data mentah yang terkait dengan sebuah timestamp analisis.
        Mengembalikan True jika berhasil, False jika tidak ditemukan.
        """
        raise NotImplementedError