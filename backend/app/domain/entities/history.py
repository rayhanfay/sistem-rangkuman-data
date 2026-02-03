from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

@dataclass
class History:
    """Mewakili satu catatan riwayat analisis yang telah disimpan."""
    id: Optional[int]
    filename: str
    summary: str
    timestamp: str
    upload_date: datetime
    cycle_assets: Optional[List[Dict[str, Any]]] = field(default_factory=list) 
    user_email: Optional[str] = None
    sheet_name: Optional[str] = None