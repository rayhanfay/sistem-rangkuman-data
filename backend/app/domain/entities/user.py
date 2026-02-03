from dataclasses import dataclass
from typing import Optional
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    """Mendefinisikan peran baru yang lebih sederhana: admin dan user."""
    admin = "admin"
    user = "user"

@dataclass
class User:
    """
    Mewakili entitas pengguna dalam sistem.
    Ini adalah objek domain murni tanpa detail database.
    """
    id: Optional[int]
    uid: str
    email: str
    role: UserRole
    created_at: datetime