from sqlalchemy.orm import Session
from typing import List, Optional

from app.domain.entities.history import History as HistoryEntity
from app.domain.repositories.history_repository import IHistoryRepository
from app.infrastructure.database.models import History as HistoryModel

class SqlalchemyHistoryRepository(IHistoryRepository):
    """Implementasi konkret dari IHistoryRepository menggunakan SQLAlchemy."""
    def __init__(self, db: Session):
        self.db = db

    def get_by_timestamp(self, timestamp: str) -> Optional[HistoryEntity]:
        db_model = self.db.query(HistoryModel).filter(HistoryModel.timestamp == timestamp).first()
        return self._to_entity(db_model) if db_model else None

    def get_latest(self) -> Optional[HistoryEntity]:
        db_model = self.db.query(HistoryModel).order_by(HistoryModel.upload_date.desc()).first()
        return self._to_entity(db_model) if db_model else None

    def get_all(self) -> List[HistoryEntity]:
        db_models = self.db.query(HistoryModel).order_by(HistoryModel.upload_date.desc()).all()
        return [self._to_entity(model) for model in db_models]

    def save(self, history_entity: HistoryEntity) -> HistoryEntity:
        entity_data = history_entity.__dict__
        entity_data.pop('id', None)
        
        db_model = HistoryModel(**entity_data)
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return self._to_entity(db_model)

    def delete_by_timestamp(self, timestamp: str) -> bool:
        db_model = self.db.query(HistoryModel).filter(HistoryModel.timestamp == timestamp).first()
        if db_model:
            self.db.delete(db_model)
            self.db.commit()
            return True
        return False

    def _to_entity(self, model: HistoryModel) -> Optional[HistoryEntity]:
        """Mapper dari SQLAlchemy Model ke Dataclass Entity."""
        if not model:
            return None
            
        return HistoryEntity(
            id=model.id,
            filename=model.filename,
            summary=model.summary,
            timestamp=model.timestamp,
            upload_date=model.upload_date,
            cycle_assets=model.cycle_assets,
            user_email=model.user_email,
            sheet_name=model.sheet_name 
        )