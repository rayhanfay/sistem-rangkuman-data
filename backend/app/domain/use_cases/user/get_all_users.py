from typing import List
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository

class GetAllUsersUseCase:
    """Use case untuk mendapatkan semua pengguna."""
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(self) -> List[User]:
        """Mengembalikan daftar semua entitas pengguna."""
        return self.user_repo.get_all()