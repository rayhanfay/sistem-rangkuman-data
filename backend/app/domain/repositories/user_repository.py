from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.user import User, UserRole

class IUserRepository(ABC):
    """
    Interface abstrak untuk operasi data terkait entitas User.
    """

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Mengambil pengguna berdasarkan ID database internal.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_uid(self, uid: str) -> Optional[User]:
        """
        Mengambil pengguna berdasarkan UID Firebase.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Mengambil pengguna berdasarkan alamat email.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[User]:
        """
        Mengambil semua pengguna dari database.
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, user_entity: User) -> User:
        """
        Menyimpan entitas pengguna baru ke dalam database.
        """
        raise NotImplementedError

    @abstractmethod
    def update_role(self, user_id: int, new_role: UserRole) -> Optional[User]:
        """
        Memperbarui peran seorang pengguna berdasarkan ID internal.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """
        Menghapus seorang pengguna berdasarkan ID internal.
        Mengembalikan True jika berhasil, False jika tidak ditemukan.
        """
        raise NotImplementedError