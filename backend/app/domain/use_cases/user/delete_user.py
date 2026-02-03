from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.services.auth_service import IAuthService 

class DeleteUserUseCase:
    """Use case untuk menghapus seorang pengguna."""
    def __init__(self, user_repo: IUserRepository, auth_service: IAuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service

    def execute(self, user_id: int) -> dict:
        """
        Mengoordinasikan penghapusan pengguna dari layanan otentikasi
        dan dari database lokal.
        """
        user_to_delete = self.user_repo.get_by_id(user_id)
        if not user_to_delete:
            raise FileNotFoundError("Pengguna tidak ditemukan.")

        if user_to_delete.role == "super_admin":
            raise PermissionError("Tidak diizinkan menghapus akun super_admin.")
        
        try:
            self.auth_service.delete_user(user_to_delete.uid)
            print(f"[INFO] Pengguna '{user_to_delete.email}' berhasil dihapus dari layanan otentikasi.")
        except Exception as e:
            print(f"[WARN] Gagal menghapus pengguna dari layanan otentikasi: {e}. Melanjutkan penghapusan lokal.")

        deleted = self.user_repo.delete(user_id)
        if not deleted:
            raise RuntimeError("Gagal menghapus pengguna dari database lokal.")
        
        return {"message": "Pengguna berhasil dihapus."}