import pandas as pd
from typing import Dict, Any

class ChartService:
    """Service yang bertanggung jawab untuk membuat data visualisasi (chart)."""
    
    COL_KONDISI = 'KONDISI'
    COL_HASIL_INV = 'HASIL INVENTORY'
    COL_NILAI_ASET = 'NILAI ASET'
    COL_LOKASI = 'LOKASI SPESIFIK PER-INVENTORY'
    COL_TANGGAL_INV = 'TANGGAL INVENTORY'

    def create_chart_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Mengonversi DataFrame menjadi struktur data yang siap digunakan oleh library chart di frontend.
        """
        chart_data = {}
        if df.empty:
            return chart_data
        
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        # Chart Kondisi
        if self.COL_KONDISI in df.columns:
            kondisi_counts = df[self.COL_KONDISI].value_counts().reset_index()
            kondisi_counts.columns = ['x', 'y']
            chart_data['kondisi'] = kondisi_counts.to_dict(orient='records')

        # Chart Hasil Inventory
        if self.COL_HASIL_INV in df.columns:
            hasil_inv_counts = df[self.COL_HASIL_INV].value_counts().reset_index()
            hasil_inv_counts.columns = ['x', 'y']
            chart_data['hasilInventory'] = hasil_inv_counts.to_dict(orient='records')

        # Chart Nilai Aset
        if self.COL_NILAI_ASET in df.columns and self.COL_LOKASI in df.columns:
            asset_df = df.copy()
            asset_df[self.COL_NILAI_ASET] = pd.to_numeric(
                asset_df[self.COL_NILAI_ASET].astype(str).str.replace(r'[^\d]', '', regex=True), 
                errors='coerce'
            ).fillna(0)
            asset_value = asset_df.groupby(self.COL_LOKASI)[self.COL_NILAI_ASET].sum().reset_index()
            asset_value.columns = ['x', 'y']
            chart_data['assetValue'] = asset_value.nlargest(10, 'y').to_dict(orient='records')

        # Chart Tren Inventory
        if self.COL_TANGGAL_INV in df.columns:
            date_df = df.copy()
            date_df['parsed_date'] = pd.to_datetime(date_df[self.COL_TANGGAL_INV], errors='coerce')
            date_df.dropna(subset=['parsed_date'], inplace=True)
            if not date_df.empty:
                date_df['bulan_inv'] = date_df['parsed_date'].dt.strftime('%Y-%m')
                monthly_counts = date_df.groupby('bulan_inv').size().reset_index(name='y')
                monthly_counts.rename(columns={'bulan_inv': 'x'}, inplace=True)
                chart_data['trenInventory'] = monthly_counts.sort_values('x').to_dict(orient='records')
        
        return chart_data