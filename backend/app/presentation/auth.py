from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from typing import List

from app.domain.entities.user import User as UserEntity, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.dependencies import get_user_repository 

security_scheme = HTTPBearer()

def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security_scheme),
    user_repo: IUserRepository = Depends(get_user_repository)
) -> UserEntity:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token otentikasi tidak ada")
    
    return get_current_user_from_token(token.credentials, user_repo)

def get_current_user_from_token(
    token_str: str, 
    user_repo: IUserRepository
) -> UserEntity:
    try:
        decoded_token = auth.verify_id_token(token_str)
        uid = decoded_token['uid']
        email = decoded_token.get('email')

        if not email:
            raise ValueError("Email tidak ditemukan di dalam token Firebase.")

        db_user = user_repo.get_by_uid(uid)
        
        if db_user:
            return db_user
        
        db_user_by_email = user_repo.get_by_email(email)
        if db_user_by_email:
            print(f"SYNC INFO: UID untuk {email} tidak sinkron. Memperbarui UID di DB.")
            db_user_by_email.uid = uid
            return user_repo.save(db_user_by_email) 

        print(f"SYNC INFO: Pengguna baru {email} terdeteksi dari Firebase. Membuat entri di DB.")
        new_user = UserEntity(
            id=None, uid=uid, email=email, 
            role=UserRole(decoded_token.get('role', 'user')),
            created_at=None
        )
        return user_repo.save(new_user)

    except auth.InvalidIdTokenError:
        raise ValueError("Token otentikasi tidak valid atau sudah kedaluwarsa.")
    except Exception as e:
        raise ValueError(f"Terjadi error otentikasi: {e}")

def role_required(allowed_roles: List[str]):
    def role_checker(current_user: UserEntity = Depends(auth_required)):
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki izin untuk mengakses sumber daya ini."
            )
        return current_user
    return role_checker

auth_required = get_current_user