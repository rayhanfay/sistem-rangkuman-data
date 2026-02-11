export const formatIDRCurrency = (value) => {
    return new Intl.NumberFormat('id-ID').format(value);
};

/**
 * Parsing tanggal dari format string Google Sheets atau ISO
 */
export const parseAndFormatDate = (dateSource) => {
    if (!dateSource) return 'Tanggal tidak tersedia';
    
    if (typeof dateSource === 'string' && dateSource.includes('_')) {
        const [datePart, timePart] = dateSource.split('_');
        const year = datePart.substring(0, 4);
        const month = parseInt(datePart.substring(4, 6), 10) - 1;
        const day = datePart.substring(6, 8);
        const hour = timePart.substring(0, 2);
        const minute = timePart.substring(2, 4);
        const second = timePart.substring(4, 6);
        
        const dateObject = new Date(year, month, day, hour, minute, second);
        return dateObject.toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' });
    }
    
    const dateObject = new Date(dateSource);
    return !isNaN(dateObject.getTime()) 
        ? dateObject.toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' })
        : 'Tanggal tidak valid';
};

/**
 * Fungsi sortir universal untuk Nilai Aset, Tanggal, dan String
 */
export const sortAssetData = (data, sortConfig) => {
    if (!sortConfig.key || sortConfig.direction === 'none') return data;

    return [...data].sort((a, b) => {
        const key = sortConfig.key;
        let aValue = a[key];
        let bValue = b[key];

        if (String(key).toUpperCase().includes('NILAI ASET')) {
            const clean = (val) => parseInt(String(val || '0').replace(/[^0-9]/g, ''), 10) || 0;
            aValue = clean(aValue);
            bValue = clean(bValue);
        } else if (String(key).toUpperCase().includes('TANGGAL')) {
            aValue = new Date(aValue).getTime() || 0;
            bValue = new Date(bValue).getTime() || 0;
        } else {
            aValue = String(aValue || '').toLowerCase();
            bValue = String(bValue || '').toLowerCase();
            return sortConfig.direction === 'ascending' 
                ? aValue.localeCompare(bValue) 
                : bValue.localeCompare(aValue);
        }

        if (aValue < bValue) return sortConfig.direction === 'ascending' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'ascending' ? 1 : -1;
        return 0;
    });
};