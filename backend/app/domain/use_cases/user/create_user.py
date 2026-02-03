from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.services.auth_service import IAuthService 

class CreateUserUseCase:
    """Use case untuk membuat pengguna baru."""
    def __init__(self, user_repo: IUserRepository, auth_service: IAuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service

    def execute(self, email: str, password: str, role: UserRole) -> User:
        """
        Mengoordinasikan pembuatan pengguna di layanan otentikasi (Firebase)
        dan penyimpanan di database lokal, dengan aturan bisnis baru.
        """
        if self.user_repo.get_by_email(email):
            raise ValueError("Email sudah terdaftar.")

        if role != UserRole.user:
            raise PermissionError("Admin hanya dapat membuat pengguna dengan peran 'user'.")

        try:
            firebase_user_data = self.auth_service.create_user(email, password, UserRole.user)
        except Exception as e:
            raise RuntimeError(f"Gagal membuat pengguna di layanan otentikasi: {e}")

        new_user_entity = User(
            id=None,
            uid=firebase_user_data['uid'],
            email=email,
            role=UserRole.user, 
            created_at=None 
        )

        try:
            saved_user = self.user_repo.save(new_user_entity)
            return saved_user
        except Exception as e:
            self.auth_service.delete_user(firebase_user_data['uid'])
            raise RuntimeError(f"Gagal menyimpan pengguna ke database lokal. Rollback dilakukan. Error: {e}")