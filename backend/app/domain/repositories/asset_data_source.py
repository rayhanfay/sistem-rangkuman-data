from abc import ABC, abstractmethod
from typing import List
import pandas as pd

class IAssetDataSource(ABC):
    """
    Interface abstrak untuk sumber data aset.
    Ini mengabstraksi dari mana data aset berasal,
    bisa dari Google Sheets, file CSV, atau API lain.
    """

    @abstractmethod
    def fetch_data(self, sheet_name: str | None) -> pd.DataFrame:
        """
        Mengambil data aset sebagai Pandas DataFrame dari sumber yang ditentukan.
        """
        raise NotImplementedError

    @abstractmethod
    def get_sheet_names(self) -> List[str]:
        """
        Mengambil daftar nama sheet yang tersedia dari sumber data.
        """
        raise NotImplementedError