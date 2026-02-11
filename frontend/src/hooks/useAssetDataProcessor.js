import { useMemo, useState } from 'react';
import { sortAssetData } from '../utils/assetUtils';

export const useAssetDataProcessor = (rawData, initialArea = 'Semua Area') => {
    const [searchTerm, setSearchTerm] = useState('');
    const [filterArea, setFilterArea] = useState(initialArea);
    const [filterKondisi, setFilterKondisi] = useState('Semua');
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'none' });
    const [currentPage, setCurrentPage] = useState(1);

    const processedData = useMemo(() => {
        if (!rawData) return [];
        let filtered = [...rawData];

        if (filterArea !== 'Semua' && filterArea !== 'Semua Area') {
            filtered = filtered.filter(item => item.AREA === filterArea);
        }
        if (filterKondisi !== 'Semua') {
            filtered = filtered.filter(item => item.KONDISI === filterKondisi);
        }
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(item => Object.values(item).some(v => String(v || '').toLowerCase().includes(term)));
        }
        return sortAssetData(filtered, sortConfig);
    }, [rawData, searchTerm, filterArea, filterKondisi, sortConfig]);

    return {
        searchTerm, setSearchTerm,
        filterArea, setFilterArea,
        filterKondisi, setFilterKondisi,
        sortConfig, setSortConfig,
        currentPage, setCurrentPage,
        processedData
    };
};