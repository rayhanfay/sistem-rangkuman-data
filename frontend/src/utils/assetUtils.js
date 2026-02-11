export const formatIDRCurrency = (value) => {
    return new Intl.NumberFormat('id-ID').format(value);
};

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
        return new Date(year, month, day, hour, minute, second).toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' });
    }
    const dateObject = new Date(dateSource);
    return !isNaN(dateObject.getTime()) ? dateObject.toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' }) : 'Tanggal tidak valid';
};

export const sortAssetData = (data, sortConfig) => {
    if (!sortConfig.key || sortConfig.direction === 'none') return data;
    return [...data].sort((a, b) => {
        const key = sortConfig.key;
        let aV = a[key];
        let bV = b[key];
        if (String(key).toUpperCase().includes('NILAI ASET')) {
            const clean = (val) => parseInt(String(val || '0').replace(/[^0-9]/g, ''), 10) || 0;
            aV = clean(aV); bV = clean(bV);
        } else if (String(key).toUpperCase().includes('TANGGAL')) {
            aV = new Date(aV).getTime() || 0; bV = new Date(bV).getTime() || 0;
        } else {
            aV = String(aV || '').toLowerCase(); bV = String(bV || '').toLowerCase();
            return sortConfig.direction === 'ascending' ? aV.localeCompare(bV) : bV.localeCompare(aV);
        }
        return sortConfig.direction === 'ascending' ? aV - bV : bV - aV;
    });
};