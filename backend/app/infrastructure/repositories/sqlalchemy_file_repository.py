from sqlalchemy.orm import Session
from typing import Optional, List

from app.domain.entities.file import File as FileEntity
from app.domain.repositories.file_repository import IFileRepository
from app.infrastructure.database.models import File as FileModel

class SqlalchemyFileRepository(IFileRepository):
    """Implementasi konkret dari IFileRepository menggunakan SQLAlchemy."""
    def __init__(self, db: Session):
        self.db = db

    def find_by_timestamp(self, timestamp: str) -> Optional[FileEntity]:
        """Menemukan file berdasarkan timestamp yang disematkan di nama filenya."""
        # Query ini mencari nama file yang diakhiri dengan '_<timestamp>.json'
        db_model = self.db.query(FileModel).filter(FileModel.filename.like(f"%_{timestamp}.json")).first()
        return self._to_entity(db_model) if db_model else None

    def find_by_filename(self, filename: str) -> Optional[FileEntity]:
        """Menemukan file berdasarkan nama file yang sama persis."""
        db_model = self.db.query(FileModel).filter(FileModel.filename == filename).first()
        return self._to_entity(db_model) if db_model else None

    def get_all(self) -> List[FileEntity]:
        """Mengambil semua record file dari database."""
        db_models = self.db.query(FileModel).order_by(FileModel.upload_date.desc()).all()
        return [self._to_entity(model) for model in db_models]

    def save(self, file_entity: FileEntity) -> FileEntity:
        """Menyimpan entitas File baru ke database."""
        entity_data = file_entity.__dict__
        entity_data.pop('id', None)  
        
        db_model = FileModel(**entity_data)
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return self._to_entity(db_model)

    def delete_by_timestamp(self, timestamp: str) -> bool:
        """Menghapus file berdasarkan timestamp yang disematkan di nama filenya."""
        db_model = self.db.query(FileModel).filter(FileModel.filename.like(f"%_{timestamp}.json")).first()
        if db_model:
            self.db.delete(db_model)
            self.db.commit()
            return True
        return False

    def _to_entity(self, model: FileModel) -> FileEntity:
        """
        Mapper internal untuk mengubah dari SQLAlchemy Model ke Dataclass Entity.
        Ini adalah bagian penting untuk menjaga domain tetap terisolasi.
        """
        if not model:
            return None
        return FileEntity(
            id=model.id,
            filename=model.filename,
            file_type=model.file_type,
            json_content=model.json_content,
            upload_date=model.upload_date
        )