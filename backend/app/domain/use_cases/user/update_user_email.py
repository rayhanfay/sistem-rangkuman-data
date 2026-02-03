from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.services.auth_service import IAuthService

class UpdateUserEmailUseCase:
    """Use case untuk memperbarui email seorang pengguna."""
    def __init__(self, user_repo: IUserRepository, auth_service: IAuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service

    def execute(self, user_id: int, new_email: str) -> User:
        existing_user = self.user_repo.get_by_email(new_email)
        if existing_user and existing_user.id != user_id:
            raise ValueError(f"Email '{new_email}' sudah terdaftar.")

        user_to_update = self.user_repo.get_by_id(user_id)
        if not user_to_update:
            raise FileNotFoundError("Pengguna tidak ditemukan.")

        try:
            self.auth_service.update_user_email(user_to_update.uid, new_email)
        except Exception as e:
            raise RuntimeError(f"Gagal memperbarui email di layanan otentikasi: {e}")

        user_to_update.email = new_email
        updated_user_in_db = self.user_repo.save(user_to_update) 

        return updated_user_in_db