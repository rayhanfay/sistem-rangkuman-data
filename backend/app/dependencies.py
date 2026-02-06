import os
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import credentials, auth
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- DATABASE ---
from app.infrastructure.database.database import get_db, SessionLocal

# --- REPOSITORIES (INTERFACES & IMPLEMENTATIONS) ---
from app.domain.repositories.history_repository import IHistoryRepository
from app.infrastructure.repositories.sqlalchemy_history_repository import SqlalchemyHistoryRepository
from app.domain.repositories.file_repository import IFileRepository
from app.infrastructure.repositories.sqlalchemy_file_repository import SqlalchemyFileRepository
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.repositories.sqlalchemy_user_repository import SqlalchemyUserRepository
from app.domain.repositories.asset_data_source import IAssetDataSource
from app.infrastructure.services.google_sheets_asset_data_source import GoogleSheetsAssetDataSource

# --- USE CASES ---
from app.domain.use_cases.analysis.get_dashboard_data import GetDashboardDataUseCase
from app.domain.use_cases.analysis.trigger_analysis import TriggerAnalysisUseCase
from app.domain.use_cases.analysis.save_latest_analysis import SaveLatestAnalysisUseCase
from app.domain.use_cases.analysis.get_stats_data import GetStatsDataUseCase
from app.domain.use_cases.analysis.get_sheet_names import GetSheetNamesUseCase
from app.domain.use_cases.analysis.get_download_file import GetDownloadFileUseCase
from app.domain.use_cases.analysis.get_master_data import GetMasterDataUseCase
from app.domain.use_cases.analysis.query_assets import QueryAssetsUseCase
from app.domain.use_cases.analysis.query_resource import QueryResourceUseCase
from app.domain.use_cases.history.get_all_history import GetAllHistoryUseCase
from app.domain.use_cases.history.delete_history import DeleteHistoryUseCase
from app.domain.use_cases.user.get_all_users import GetAllUsersUseCase
from app.domain.use_cases.user.create_user import CreateUserUseCase
from app.domain.use_cases.user.update_user_role import UpdateUserRoleUseCase
from app.domain.use_cases.user.update_user_email import UpdateUserEmailUseCase
from app.domain.use_cases.user.delete_user import DeleteUserUseCase
from app.domain.use_cases.mcp.get_resources import GetResourcesUseCase
from app.domain.use_cases.mcp.get_prompts import GetPromptsUseCase

# --- SERVICES (INFRASTRUCTURE) ---
from app.infrastructure.services.preview_state_service import PreviewStateService
from app.infrastructure.services.chart_service import ChartService
from app.infrastructure.services.document_analyzer import DocumentAnalyzer
from app.infrastructure.services.auth_service import IAuthService, FirebaseAuthService
from app.infrastructure.services.download_service import DownloadService

# --- INSTANCE SINGLETON / GLOBAL ---
preview_state_service_instance = PreviewStateService()
chart_service_instance = ChartService()
asset_data_source_instance = GoogleSheetsAssetDataSource()
document_analyzer_instance = DocumentAnalyzer()
auth_service_instance = FirebaseAuthService()
download_service_instance = DownloadService()

# --- CONTAINER UNTUK MANUAL DEPENDENCY INJECTION (UNTUK MCP SERVER) ---
class AppContainer:
    """
    Container untuk membuat dan menyediakan instance dari use case secara manual,
    terutama untuk digunakan oleh WebSocket handler (McpServer).
    """
    def __init__(self):
        self.preview_state = preview_state_service_instance
        self.chart_service = chart_service_instance
        self.asset_data_source = asset_data_source_instance
        self.document_analyzer = document_analyzer_instance
        self.auth_service = auth_service_instance
        self.download_service = download_service_instance

    def get_use_case(self, use_case_name: str, db_session: Session):
        """
        Pabrik (factory) untuk membuat instance use case dengan sesi DB yang diberikan.
        """
        history_repo = SqlalchemyHistoryRepository(db_session)
        file_repo = SqlalchemyFileRepository(db_session)
        user_repo = SqlalchemyUserRepository(db_session)

        use_case_map = {
            "get_dashboard_data": GetDashboardDataUseCase(history_repo, file_repo, self.preview_state, self.chart_service),
            "trigger_analysis": TriggerAnalysisUseCase(self.asset_data_source, self.document_analyzer, self.preview_state, self.chart_service),
            "save_latest_analysis": SaveLatestAnalysisUseCase(history_repo, file_repo, self.preview_state),
            "get_all_history": GetAllHistoryUseCase(history_repo, file_repo),
            "delete_history": DeleteHistoryUseCase(history_repo, file_repo),
            "get_stats_data": GetStatsDataUseCase(history_repo, file_repo, self.preview_state, self.chart_service),
            "get_sheet_names": GetSheetNamesUseCase(self.asset_data_source),
            "get_master_data": GetMasterDataUseCase(self.asset_data_source),
            "query_assets": QueryAssetsUseCase(self.asset_data_source),
            "query_resource": QueryResourceUseCase(file_repo),
            "get_resources": GetResourcesUseCase(file_repo),
            "get_prompts": GetPromptsUseCase(),
            "get_all_users": GetAllUsersUseCase(user_repo),
            "create_user": CreateUserUseCase(user_repo, self.auth_service),
            "update_user_role": UpdateUserRoleUseCase(user_repo, self.auth_service),
            "update_user_email": UpdateUserEmailUseCase(user_repo, self.auth_service),
            "delete_user": DeleteUserUseCase(user_repo, self.auth_service),
        }
        
        instance = use_case_map.get(use_case_name)
        if not instance:
            raise NameError(f"Use case '{use_case_name}' tidak ditemukan di AppContainer.")
        return instance


#  INISIALISASI CONTAINER - HARUS SETELAH CLASS DIDEFINISIKAN
container = AppContainer()


# --- PROVIDERS UNTUK DEPENDENCY INJECTION OTOMATIS (UNTUK REST API) ---

def get_preview_state_service() -> PreviewStateService:
    return preview_state_service_instance

def get_chart_service() -> ChartService:
    return chart_service_instance

def get_asset_data_source() -> IAssetDataSource:
    return asset_data_source_instance

def get_document_analyzer() -> DocumentAnalyzer:
    return document_analyzer_instance

def get_auth_service() -> IAuthService:
    return auth_service_instance

def get_download_service() -> DownloadService:
    return download_service_instance

def get_history_repository(db: Session = Depends(get_db)) -> IHistoryRepository:
    return SqlalchemyHistoryRepository(db)
    
def get_file_repository(db: Session = Depends(get_db)) -> IFileRepository:
    return SqlalchemyFileRepository(db)

def get_user_repository(db: Session = Depends(get_db)) -> IUserRepository:
    return SqlalchemyUserRepository(db)

# --- PROVIDER UNTUK SETIAP USE CASE ---

def get_dashboard_data_use_case(
    history_repo: IHistoryRepository = Depends(get_history_repository),
    file_repo: IFileRepository = Depends(get_file_repository),
    preview_state_service: PreviewStateService = Depends(get_preview_state_service),
    chart_service: ChartService = Depends(get_chart_service)
) -> GetDashboardDataUseCase:
    return GetDashboardDataUseCase(history_repo, file_repo, preview_state_service, chart_service)

def trigger_analysis_use_case(
    asset_data_source: IAssetDataSource = Depends(get_asset_data_source),
    document_analyzer: DocumentAnalyzer = Depends(get_document_analyzer),
    preview_state_service: PreviewStateService = Depends(get_preview_state_service),
    chart_service: ChartService = Depends(get_chart_service)
) -> TriggerAnalysisUseCase:
    return TriggerAnalysisUseCase(asset_data_source, document_analyzer, preview_state_service, chart_service)

def save_latest_analysis_use_case(
    history_repo: IHistoryRepository = Depends(get_history_repository),
    file_repo: IFileRepository = Depends(get_file_repository),
    preview_state_service: PreviewStateService = Depends(get_preview_state_service)
) -> SaveLatestAnalysisUseCase:
    return SaveLatestAnalysisUseCase(history_repo, file_repo, preview_state_service)

def get_all_history_use_case(
    history_repo: IHistoryRepository = Depends(get_history_repository),
    file_repo: IFileRepository = Depends(get_file_repository)
) -> GetAllHistoryUseCase:
    return GetAllHistoryUseCase(history_repo, file_repo)

def delete_history_use_case(
    history_repo: IHistoryRepository = Depends(get_history_repository),
    file_repo: IFileRepository = Depends(get_file_repository)
) -> DeleteHistoryUseCase:
    return DeleteHistoryUseCase(history_repo, file_repo)

def get_stats_data_use_case(
    history_repo: IHistoryRepository = Depends(get_history_repository),
    file_repo: IFileRepository = Depends(get_file_repository),
    preview_state_service: PreviewStateService = Depends(get_preview_state_service),
    chart_service: ChartService = Depends(get_chart_service)
) -> GetStatsDataUseCase:
    return GetStatsDataUseCase(history_repo, file_repo, preview_state_service, chart_service)

def get_sheet_names_use_case(
    asset_data_source: IAssetDataSource = Depends(get_asset_data_source)
) -> GetSheetNamesUseCase:
    return GetSheetNamesUseCase(asset_data_source)

def get_download_file_use_case(
    db: Session = Depends(get_db),
    asset_data_source: IAssetDataSource = Depends(get_asset_data_source),
    download_service: DownloadService = Depends(get_download_service)
) -> GetDownloadFileUseCase:
    return GetDownloadFileUseCase(db, asset_data_source, download_service)

def get_master_data_use_case(
    asset_data_source: IAssetDataSource = Depends(get_asset_data_source)
) -> GetMasterDataUseCase:
    return GetMasterDataUseCase(asset_data_source)

def query_assets_use_case(
    asset_data_source: IAssetDataSource = Depends(get_asset_data_source)
) -> QueryAssetsUseCase:
    return QueryAssetsUseCase(asset_data_source)

def query_resource_use_case(
    file_repo: IFileRepository = Depends(get_file_repository)
) -> QueryResourceUseCase:
    return QueryResourceUseCase(file_repo)

def get_all_users_use_case(
    user_repo: IUserRepository = Depends(get_user_repository)
) -> GetAllUsersUseCase:
    return GetAllUsersUseCase(user_repo)

def create_user_use_case(
    user_repo: IUserRepository = Depends(get_user_repository),
    auth_service: IAuthService = Depends(get_auth_service)
) -> CreateUserUseCase:
    return CreateUserUseCase(user_repo, auth_service)

def update_user_role_use_case(
    user_repo: IUserRepository = Depends(get_user_repository),
    auth_service: IAuthService = Depends(get_auth_service)
) -> UpdateUserRoleUseCase:
    return UpdateUserRoleUseCase(user_repo, auth_service)

def update_user_email_use_case(
    user_repo: IUserRepository = Depends(get_user_repository),
    auth_service: IAuthService = Depends(get_auth_service)
) -> UpdateUserEmailUseCase:
    return UpdateUserEmailUseCase(user_repo, auth_service)

def delete_user_use_case(
    user_repo: IUserRepository = Depends(get_user_repository),
    auth_service: IAuthService = Depends(get_auth_service)
) -> DeleteUserUseCase:
    return DeleteUserUseCase(user_repo, auth_service)

def get_resources_use_case(
    file_repo: IFileRepository = Depends(get_file_repository)
) -> GetResourcesUseCase:
    return GetResourcesUseCase(file_repo)

def get_prompts_use_case() -> GetPromptsUseCase:
    return GetPromptsUseCase()

def get_resource_list_use_case(
    file_repo: IFileRepository = Depends(get_file_repository)
) -> GetResourcesUseCase:
    """
    Provider untuk GetResourcesUseCase yang digunakan oleh llm-router endpoint
    untuk mendapatkan daftar resources yang tersedia.
    """
    return GetResourcesUseCase(file_repo)