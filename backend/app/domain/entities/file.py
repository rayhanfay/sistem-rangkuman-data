from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class File:
    """
    Mewakili entitas file data mentah yang disimpan.
    Ini adalah objek domain murni tanpa detail database.
    """
    id: Optional[int]
    filename: str
    file_type: str
    json_content: Optional[str]
    upload_date: datetime