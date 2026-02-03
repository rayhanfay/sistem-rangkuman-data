from typing import Optional
from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.services.auth_service import IAuthService 

class UpdateUserRoleUseCase:
    """Use case untuk memperbarui peran (role) seorang pengguna."""
    def __init__(self, user_repo: IUserRepository, auth_service: IAuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service

    def execute(self, user_id: int, new_role: UserRole) -> User:
        """
        Mengoordinasikan pembaruan peran di layanan otentikasi eksternal
        dan di database lokal, dengan aturan keamanan baru.
        """
        if new_role == UserRole.admin:
            raise PermissionError("Tidak diizinkan untuk mempromosikan pengguna menjadi admin melalui antarmuka ini.")

        user_to_update = self.user_repo.get_by_id(user_id)
        if not user_to_update:
            raise FileNotFoundError("Pengguna tidak ditemukan.")
            
        if user_to_update.role == UserRole.admin:
             raise PermissionError("Peran seorang admin tidak dapat diubah.")

        try:
            self.auth_service.update_user_role(user_to_update.uid, new_role)
        except Exception as e:
            raise RuntimeError(f"Gagal memperbarui peran di layanan otentikasi: {e}")

        updated_user = self.user_repo.update_role(user_id, new_role)
        if not updated_user:
            raise RuntimeError("Gagal memperbarui pengguna di database lokal setelah berhasil di otentikasi.")
            
        return updated_user