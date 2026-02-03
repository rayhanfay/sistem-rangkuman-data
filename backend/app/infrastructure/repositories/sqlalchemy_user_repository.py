from sqlalchemy.orm import Session
from typing import List, Optional

from app.domain.entities.user import User as UserEntity, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.models import User as UserModel

class SqlalchemyUserRepository(IUserRepository):
    """Implementasi konkret dari IUserRepository menggunakan SQLAlchemy."""
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        db_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(db_model) if db_model else None

    def get_by_uid(self, uid: str) -> Optional[UserEntity]:
        db_model = self.db.query(UserModel).filter(UserModel.uid == uid).first()
        return self._to_entity(db_model) if db_model else None

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        db_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(db_model) if db_model else None

    def get_all(self) -> List[UserEntity]:
        db_models = self.db.query(UserModel).all()
        return [self._to_entity(model) for model in db_models]

    def save(self, user_entity: UserEntity) -> UserEntity:
        """
        Menyimpan entitas pengguna.
        Melakukan UPDATE jika entitas sudah memiliki ID (sudah ada di DB).
        Melakukan INSERT jika entitas belum memiliki ID (pengguna baru).
        """
        if user_entity.id:
            db_model = self.db.query(UserModel).filter(UserModel.id == user_entity.id).first()
            if db_model:
                db_model.uid = user_entity.uid
                db_model.email = user_entity.email
                db_model.role = user_entity.role.value
            else:
                db_model = UserModel(
                    uid=user_entity.uid,
                    email=user_entity.email,
                    role=user_entity.role.value
                )
                self.db.add(db_model)
        else:
            db_model = UserModel(
                uid=user_entity.uid,
                email=user_entity.email,
                role=user_entity.role.value
            )
            self.db.add(db_model)
        
        self.db.commit()
        self.db.refresh(db_model)
        return self._to_entity(db_model)

    def update_role(self, user_id: int, new_role: UserRole) -> Optional[UserEntity]:
        db_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if db_model:
            db_model.role = new_role.value
            self.db.commit()
            self.db.refresh(db_model)
            return self._to_entity(db_model)
        return None

    def delete(self, user_id: int) -> bool:
        db_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if db_model:
            self.db.delete(db_model)
            self.db.commit()
            return True
        return False

    def _to_entity(self, model: UserModel) -> UserEntity:
        """Mapper dari SQLAlchemy Model ke Dataclass Entity."""
        if not model:
            return None
        return UserEntity(
            id=model.id,
            uid=model.uid,
            email=model.email,
            role=UserRole(model.role), 
            created_at=model.created_at
        )