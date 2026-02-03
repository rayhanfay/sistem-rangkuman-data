import os
from abc import ABC, abstractmethod
from typing import Dict, Any
import json
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.auth import UserNotFoundError

from app.domain.entities.user import UserRole

# --- INTERFACE (KONTRAK) ---
class IAuthService(ABC):
    """Interface abstrak untuk layanan otentikasi eksternal."""

    @abstractmethod
    def create_user(self, email: str, password: str, role: UserRole) -> Dict[str, Any]:
        """Membuat pengguna baru di layanan otentikasi."""
        raise NotImplementedError

    @abstractmethod
    def update_user_role(self, uid: str, new_role: UserRole):
        """Memperbarui peran pengguna di layanan otentikasi."""
        raise NotImplementedError

    @abstractmethod
    def update_user_email(self, uid: str, new_email: str):
        """Memperbarui email pengguna di layanan otentikasi."""
        raise NotImplementedError

    @abstractmethod
    def delete_user(self, uid: str):
        """Menghapus pengguna dari layanan otentikasi."""
        raise NotImplementedError

# --- IMPLEMENTASI KONKRET UNTUK FIREBASE ---
class FirebaseAuthService(IAuthService):
    def __init__(self):
        try:
            # Ambil string JSON dari environment variable
            firebase_json = os.getenv("FIREBASE_CONFIG_JSON")
            
            if not firebase_admin._apps:
                if firebase_json:
                    # Jika ada di Env Var (untuk Produksi/Azure)
                    firebase_info = json.loads(firebase_json)
                    cred = credentials.Certificate(firebase_info)
                    print("[INFO] Firebase initialized via Environment Variable.")
                else:
                    # Fallback ke file lokal (untuk Development)
                    base_dir = os.path.dirname(__file__)
                    cred_path = os.path.join(base_dir, '..', '..', '..', 'firebase-adminsdk.json')
                    if not os.path.exists(cred_path):
                        raise FileNotFoundError(f"File Firebase tidak ditemukan di: {cred_path}")
                    cred = credentials.Certificate(cred_path)
                    print("[INFO] Firebase initialized via local file.")
                
                firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"[FATAL] Gagal menginisialisasi Firebase Admin SDK: {e}")
            raise

    def create_user(self, email: str, password: str, role: UserRole) -> Dict[str, Any]:
        """Membuat pengguna baru di Firebase dan menetapkan peran sebagai custom claim."""
        firebase_user = auth.create_user(email=email, password=password)
        auth.set_custom_user_claims(firebase_user.uid, {'role': role.value})
        return {'uid': firebase_user.uid}

    def update_user_role(self, uid: str, new_role: UserRole):
        """Memperbarui custom claim 'role' untuk pengguna yang ada."""
        auth.set_custom_user_claims(uid, {'role': new_role.value})

    def update_user_email(self, uid: str, new_email: str):
        """Memperbarui alamat email untuk pengguna yang ada."""
        auth.update_user(uid, email=new_email)

    def delete_user(self, uid: str):
        """Menghapus pengguna dari Firebase berdasarkan UID-nya."""
        try:
            auth.delete_user(uid)
        except UserNotFoundError:
            print(f"[WARN] Pengguna dengan UID {uid} tidak ditemukan di Firebase, mungkin sudah dihapus.")
            pass