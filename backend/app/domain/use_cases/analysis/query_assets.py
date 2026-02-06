import json
import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domain.repositories.asset_data_source import IAssetDataSource

class QueryAssetsUseCase:
    """
    Use case terpadu untuk mencari, memfilter, dan melakukan kalkulasi pada data aset.
    Mendukung normalisasi input, handling nomor aset bandel, filter tanggal, 
    dan berbagai task agregasi untuk LLM.
    Mendukung sumber data dinamis (Master vs Siklus).
    """
    def __init__(self, asset_data_source: IAssetDataSource):
        self.asset_data_source = asset_data_source

    def execute(self,
                task: str = 'filter',
                source: str = 'master',
                sheet_name: Optional[str] = None, 
                no_asset: Optional[str] = None,
                nama_aset: Optional[str] = None,
                area: Optional[str] = None,
                kondisi: Optional[str] = None,
                kondisi_not: Optional[str] = None,
                pic_team_fav: Optional[str] = None,
                model_type: Optional[str] = None,
                serial_number: Optional[str] = None,
                kategori: Optional[str] = None,
                manufaktur: Optional[str] = None,
                kode_lokasi_sap: Optional[str] = None,
                hasil_inventory: Optional[str] = None,
                nilai_aset_min: Optional[int] = None,
                nilai_aset_max: Optional[int] = None,
                start_date: Optional[str] = None,
                end_date: Optional[str] = None,
                calculation: Optional[str] = None, 
                group_by_field: Optional[str] = None,
                count_field: Optional[str] = None,
                limit: Optional[int] = None,
                sort_by: Optional[str] = None,
                sort_direction: Optional[str] = 'ascending'
                ) -> Any:
        
        # 1. Penentuan ID Spreadsheet dan Nama Sheet Dinamis
        if source == 'siklus':
            target_id = os.getenv("GOOGLE_SHEET_ID_SIKLUS")
            default_sheet = 'CYCLE-1-YEAR-2026'
        else:
            target_id = os.getenv("GOOGLE_SHEET_ID_MASTER")
            default_sheet = 'MASTER-SHEET'

        target_sheet = sheet_name or default_sheet
        
        # 2. Fetch Data
        df = self.asset_data_source.fetch_data(target_sheet, spreadsheet_id=target_id)
        if df.empty: 
            return [{
                "status": "DATA_TIDAK_DITEMUKAN",
                "requested_sheet": target_sheet,
                "source_used": source.upper(),
                "message": f"Sheet '{target_sheet}' tidak ditemukan atau kosong di link {source.upper()}."
            }]

        # 3. Normalisasi Nama Kolom DataFrame menjadi UPPERCASE
        df.columns = [str(col).strip().upper() for col in df.columns]

        # --- PERBAIKAN: Normalisasi Nama Kolom NILAI ASET ---
        # Menyatukan variasi nama kolom menjadi satu standar 'NILAI ASET'
        for col in df.columns:
            if 'NILAI ASET' in col:
                df.rename(columns={col: 'NILAI ASET'}, inplace=True)
                break

        # 4. Normalisasi Parameter Input & Mapping Alias
        if group_by_field: group_by_field = str(group_by_field).strip().upper()
        if count_field: count_field = str(count_field).strip().upper()
        if sort_by: sort_by = str(sort_by).strip().upper()

        column_aliases = {
            'MANUFAKTUR': 'MANUFACTURE', 'BRAND': 'MANUFACTURE', 'PABRIKAN': 'MANUFACTURE',
            'PIC': 'PIC TEAM FAV', 'PIC TEAM': 'PIC TEAM FAV', 'LOKASI': 'AREA',
            'MODEL': 'MODEL/TYPE', 'TIPE': 'MODEL/TYPE', 'NO SERI': 'SERIAL NUMBER',
            'NILAI': 'NILAI ASET', 'TANGGAL': 'TANGGAL INVENTORY',
            'STATUS INVENTORY': 'HASIL INVENTORY', 
            'STATUS': 'HASIL INVENTORY',  
            'INVENTARIS': 'HASIL INVENTORY'        
        }

        # Terapkan alias
        group_by_field = column_aliases.get(group_by_field, group_by_field)
        count_field = column_aliases.get(count_field, count_field)
        sort_by = column_aliases.get(sort_by, sort_by)

        # 5. Pre-processing NILAI ASET (Internal numeric column)
        # Regex [^\d] membuang titik (.) agar '2.980.700' menjadi 2980700 (Numeric)
        if 'NILAI ASET' in df.columns:
            df['_NILAI_NUMERIC'] = pd.to_numeric(
                df['NILAI ASET'].astype(str).str.replace(r'[^\d]', '', regex=True), 
                errors='coerce'
            ).fillna(0)
        
        # 6. Pre-processing Tanggal
        # Prioritas TANGGAL INVENTORY, fallback ke TANGGAL UPDATE
        date_cols = ['TANGGAL INVENTORY', 'TANGGAL UPDATE']
        for col in date_cols:
            if col in df.columns:
                # Menggunakan dayfirst=True agar format 03-Apr-2022 terbaca benar
                df[f'_{col}_DT'] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                
        # === TAMBAHAN: Pastikan Sorting Tanggal Bekerja Sebelum Filter ===
        if not sort_by and (start_date or end_date):
            sort_by = 'TANGGAL INVENTORY' if '_TANGGAL INVENTORY_DT' in df.columns else 'TANGGAL UPDATE'
            sort_direction = 'ascending'

        # 7. Filtering Logic
        # --- Filter String Standar ---
        def get_clean_filter(df_col):
            return df_col.astype(str).str.strip().str.lower()
        
        if area: 
            df = df[get_clean_filter(df['AREA']).str.contains(area.lower().strip(), na=False)]
        
        if hasil_inventory and 'HASIL INVENTORY' in df.columns:
            target_hi = hasil_inventory.lower().strip()
            df = df[get_clean_filter(df['HASIL INVENTORY']).str.contains(target_hi, na=False)]
            
        if nama_aset: df = df[df['NAMA ASET'].str.contains(nama_aset, case=False, na=False)]
        if model_type and 'MODEL/TYPE' in df.columns: 
            df = df[df['MODEL/TYPE'].str.contains(model_type, case=False, na=False)]
        if serial_number and 'SERIAL NUMBER' in df.columns: 
            df = df[df['SERIAL NUMBER'].str.contains(serial_number, case=False, na=False)]
        if manufaktur and 'MANUFACTURE' in df.columns: 
            df = df[df['MANUFACTURE'].str.contains(manufaktur, case=False, na=False)]
            
        if kode_lokasi_sap:
            lokasi_list = [l.strip().lower() for l in kode_lokasi_sap.split(',')]
            df = df[get_clean_filter(df.get('KODE LOKASI SAP', pd.Series())).isin(lokasi_list)]
            
        if hasil_inventory:
            hi_lower = hasil_inventory.lower().strip()
            kondisi_keywords = ["tidak ditemukan", "rusak", "rusak berat", "rusak ringan", "penghapusan", "baik"]
            if any(key in hi_lower for key in kondisi_keywords):
                if not kondisi: 
                    kondisi = hasil_inventory
                    hasil_inventory = None 
                    
        if kondisi:
            k_lower = kondisi.lower().strip()
            if k_lower in ["match", "not match"]:
                if not hasil_inventory:
                    hasil_inventory = kondisi
                    kondisi = None
                    
        if pic_team_fav and 'PIC TEAM FAV' in df.columns: 
            df = df[df['PIC TEAM FAV'].str.contains(pic_team_fav, case=False, na=False)]

        # --- Filter No Asset (Logika Robust) ---
        if no_asset and 'NO ASSET' in df.columns: 
            df['_TEMP_NO'] = df['NO ASSET'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            target_no = str(no_asset).replace('.0', '').strip()
            df = df[df['_TEMP_NO'] == target_no]

        # --- Filter Kondisi (Smart Parsing) ---
        if kondisi and 'KONDISI' in df.columns:
            kondisi_lower = kondisi.lower().strip()
            if kondisi_lower == "rusak":
                df = df[df['KONDISI'].str.contains('Rusak', case=False, na=False)]
            else:
                included = [c.strip().lower() for c in kondisi.split(',')]
                df = df[df['KONDISI'].str.lower().isin(included)]

        if kondisi_not and 'KONDISI' in df.columns:
            excluded = [c.strip().lower() for c in kondisi_not.split(',')]
            df = df[~df['KONDISI'].str.lower().isin(excluded)]

        # --- Filter Nilai Aset (Menggunakan kolom numeric internal yang sudah dibersihkan dari titik) ---
        if nilai_aset_min is not None and '_NILAI_NUMERIC' in df.columns: 
            df = df[df['_NILAI_NUMERIC'] >= nilai_aset_min]
        if nilai_aset_max is not None and '_NILAI_NUMERIC' in df.columns: 
            df = df[df['_NILAI_NUMERIC'] <= nilai_aset_max]

        # --- Filter Tanggal ---
        target_date_col = '_TANGGAL INVENTORY_DT' if '_TANGGAL INVENTORY_DT' in df.columns else '_TANGGAL UPDATE_DT'
        if start_date and target_date_col in df.columns:
            df = df[df[target_date_col] >= pd.to_datetime(start_date)]
        if end_date and target_date_col in df.columns:
            df = df[df[target_date_col] <= pd.to_datetime(end_date)]

        # 8. Task Execution (Agregasi)
        if task == 'get_distribution_analysis' and group_by_field in df.columns:
            counts = df[group_by_field].value_counts()
            percentages = df[group_by_field].value_counts(normalize=True) * 100
            return [{"grup": v, "jumlah": c, "persentase": f"{percentages[v]:.2f}%"} for v, c in counts.items()]

        if task == 'get_top_values' and group_by_field in df.columns:
            top_values = df[group_by_field].value_counts().head(limit or 5)
            return top_values.reset_index().rename(columns={group_by_field: 'grup', 'count': 'jumlah'}).to_dict(orient='records')
        
        if task == 'get_top_per_group':
            if not group_by_field or not count_field:
                return [{"error": "Task 'get_top_per_group' membutuhkan group_by_field dan count_field."}]
            
            if group_by_field not in df.columns or count_field not in df.columns:
                return [{"error": f"Kolom {group_by_field} atau {count_field} tidak ditemukan."}]
            
            top_per_group = df.groupby(group_by_field)[count_field].value_counts().groupby(level=0).head(1)
            return top_per_group.reset_index(name='count').to_dict(orient='records')

        if task == 'breakdown':
            if not group_by_field or not count_field:
                return [{"error": "Task 'breakdown' membutuhkan group_by_field dan count_field."}]
            res = df.groupby(group_by_field)[count_field].value_counts().unstack(fill_value=0)
            return json.loads(res.to_json(orient='index'))

        # 9. Sorting (Mendukung sort berdasarkan Tanggal atau Nilai)
        if sort_by:
            actual_sort_col = sort_by
            if sort_by == 'NILAI ASET': 
                actual_sort_col = '_NILAI_NUMERIC'
            elif sort_by == 'TANGGAL INVENTORY': 
                actual_sort_col = '_TANGGAL INVENTORY_DT'
            
            if actual_sort_col in df.columns:
                is_asc = str(sort_direction).lower() == 'ascending'
                df = df.dropna(subset=[actual_sort_col])
                df = df.sort_values(by=actual_sort_col, ascending=is_asc)
        
        elif start_date or end_date:
            if target_date_col in df.columns:
                df = df.dropna(subset=[target_date_col])
                df = df.sort_values(by=target_date_col, ascending=True)

        if limit:
            df = df.head(limit)

        # 10. Calculation Logic
        if calculation:
            applied_filters = []
            if area: applied_filters.append(f"Area: {area}")
            if kode_lokasi_sap: applied_filters.append(f"Lokasi: {kode_lokasi_sap}")
            if kondisi: applied_filters.append(f"Kondisi: {kondisi}")
            
            context_label = " | ".join(applied_filters)

            if calculation == 'count': 
                return {
                    "calculation_result": {
                        "label": context_label,
                        "count": len(df),
                        "details": "Data dihitung berdasarkan filter yang diminta."
                    }
                }
            if calculation == 'sum_value' and '_NILAI_NUMERIC' in df.columns:
                return {
                    "calculation_result": {
                        "label": context_label,
                        "total_value": f"Rp {df['_NILAI_NUMERIC'].sum():,.0f}"
                    }
                }

        # 11. Clean Up & Return
        if df.empty: 
            return [{"status": "Tidak ada data yang cocok dengan kriteria."}]

        cols_to_drop = [c for c in df.columns if c.startswith('_')]
        df_final = df.drop(columns=cols_to_drop)
        
        return df_final.replace({pd.NaT: None, pd.NA: None}).where(pd.notna(df_final), None).to_dict(orient='records')