import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useToast } from '../contexts/ToastContext';
import { useMcp } from '../contexts/McpProvider';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import LoadingOverlay from '../components/common/LoadingOverlay';
import { Database, AlertCircle, RefreshCw } from 'lucide-react';

const MasterData = () => {
    const [masterData, setMasterData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [searchTerm, setSearchTerm] = useState('');
    const [filterArea, setFilterArea] = useState('Semua');
    const [filterKondisi, setFilterKondisi] = useState('Semua');
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'none' });
    const [currentPage, setCurrentPage] = useState(1);
    const rowsPerPage = 50;
    
    const { showToast } = useToast();
    const { service: mcpService, status: mcpStatus } = useMcp();

    const fetchData = useCallback(async () => {
        if (mcpStatus !== 'connected') return;

        setLoading(true);
        setError('');
        try {
            const result = await mcpService.call('tools/call', {
                name: 'get_master_data',
                arguments: { sheet_name: 'MASTER-SHEET', source: 'master' }
            });
            setMasterData(result?.content || []);
        } catch (err) {
            const msg = err?.message || 'Gagal memuat master data.';
            setError(msg);
            showToast(msg, 'error');
        } finally {
            setLoading(false);
        }
    }, [mcpService, mcpStatus, showToast]);

    useEffect(() => {
        if (mcpStatus === 'connected') {
            fetchData();
        }
    }, [fetchData, mcpStatus]);

    const { areaOptions, kondisiOptions } = useMemo(() => {
        if (!masterData?.length) return { areaOptions: ['Semua'], kondisiOptions: ['Semua'] };
        
        const uniqueAreas = new Set(masterData.map(item => item.AREA).filter(Boolean));
        const uniqueKondisi = new Set(masterData.map(item => item.KONDISI).filter(Boolean));
        
        return {
            areaOptions: ['Semua', ...Array.from(uniqueAreas).sort((a, b) => a.localeCompare(b))],
            kondisiOptions: ['Semua', ...Array.from(uniqueKondisi).sort((a, b) => a.localeCompare(b))]
        };
    }, [masterData]);

    const processedData = useMemo(() => {
        if (!masterData?.length) return [];
        let data = [...masterData];

        // 1. Filtering
        if (filterArea !== 'Semua') {
            data = data.filter(item => item.AREA === filterArea);
        }
        if (filterKondisi !== 'Semua') {
            data = data.filter(item => item.KONDISI === filterKondisi);
        }
        if (searchTerm) {
            const lowercasedTerm = searchTerm.toLowerCase();
            data = data.filter(item => 
                Object.values(item).some(value => String(value || '').toLowerCase().includes(lowercasedTerm))
            );
        }

        // 2. Sorting (FIXED LOGIC)
        if (sortConfig.key && sortConfig.direction !== 'none') {
            data.sort((a, b) => {
                const key = sortConfig.key;
                let aValue = a[key];
                let bValue = b[key];

                // PERBAIKAN BUG: Deteksi kolom Nilai Aset secara fleksibel
                if (key.includes('NILAI ASET')) {
                    // Membersihkan titik, koma, Rp, dan spasi agar jadi angka murni
                    const clean = (val) => parseInt(String(val || '0').replace(/[^0-9]/g, ''), 10) || 0;
                    aValue = clean(aValue);
                    bValue = clean(bValue);
                } 
                else if (key.includes('TANGGAL')) {
                    aValue = new Date(aValue).getTime() || 0;
                    bValue = new Date(bValue).getTime() || 0;
                } 
                else {
                    // Pengurutan teks biasa untuk kolom lainnya
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
        }
        return data;
    }, [masterData, searchTerm, filterArea, filterKondisi, sortConfig]);

    const totalPages = Math.ceil(processedData.length / rowsPerPage);
    const currentTableData = processedData.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);
    const tableHeaders = masterData?.length > 0 ? Object.keys(masterData[0]) : [];

    const handlePageChange = (page) => {
        if (page >= 1 && page <= totalPages) setCurrentPage(page);
    };

    if (loading) return <LoadingOverlay />;

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold">Master Data Aset</h1>
                    <p className="text-text-secondary mt-1">
                        Tampilan data mentah dari sumber MASTER (Pusat).
                    </p>
                </div>
                <Button onClick={fetchData} variant="outline">
                    <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> 
                    Refresh Data
                </Button>
            </div>

            <Card shadow="subtle">
                <Card.Content className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 p-4 bg-gray-50 rounded-lg border">
                        <div className="md:col-span-3">
                            <label htmlFor="master-search" className="text-sm font-medium">Cari Cepat</label>
                            <Input 
                                id="master-search"
                                type="text" 
                                placeholder="Cari di semua kolom..." 
                                value={searchTerm} 
                                onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }} 
                                className="mt-1" 
                            />
                        </div>
                        <div className="w-full">
                            <label htmlFor="master-filter-area" className="text-sm font-medium">Filter Area</label>
                            <select 
                                id="master-filter-area"
                                value={filterArea} 
                                onChange={e => { setFilterArea(e.target.value); setCurrentPage(1); }} 
                                className="mt-1 w-full p-2 border rounded-md bg-white focus:ring-2 focus:ring-brand-blue"
                            >
                                {areaOptions.map(area => <option key={area} value={area}>{area}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label htmlFor="master-filter-kondisi" className="text-sm font-medium">Filter Kondisi</label>
                            <select 
                                id="master-filter-kondisi"
                                value={filterKondisi} 
                                onChange={e => { setFilterKondisi(e.target.value); setCurrentPage(1); }} 
                                className="mt-1 w-full p-2 border rounded-md bg-white focus:ring-2 focus:ring-brand-blue"
                            >
                                {kondisiOptions.map(kondisi => <option key={kondisi} value={kondisi}>{kondisi}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label htmlFor="master-sort-select" className="text-sm font-medium">Urutkan Berdasarkan</label>
                            <select
                                id="master-sort-select"
                                onChange={(e) => {
                                    // Gunakan key fleksibel untuk NILAI ASET
                                    const direction = e.target.value.split('-')[1];
                                    const keyRaw = e.target.value.split('-')[0];
                                    // Cari key asli di data (karena bisa NILAI ASET atau NILAI ASET (Rp))
                                    const actualKey = tableHeaders.find(h => h.includes(keyRaw)) || keyRaw;
                                    setSortConfig({ key: actualKey, direction });
                                    setCurrentPage(1);
                                }}
                                className="mt-1 w-full p-2 border rounded-md bg-white focus:ring-2 focus:ring-brand-blue"
                            >
                                <option value="none-none">Default</option>
                                <option value="NILAI ASET-descending">Nilai Aset (Tertinggi)</option>
                                <option value="NILAI ASET-ascending">Nilai Aset (Terendah)</option>
                                <option value="TANGGAL INVENTORY-descending">Tgl. Inventory (Terbaru)</option>
                                <option value="TANGGAL INVENTORY-ascending">Tgl. Inventory (Terlama)</option>
                            </select>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 border">
                            <thead className="bg-gray-50">
                                <tr>
                                    {tableHeaders.map(key => (
                                        <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            {key}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {currentTableData.map((row, idx) => (
                                    <tr key={row['NO ASSET'] || idx} className="hover:bg-gray-50">
                                        {tableHeaders.map(header => (
                                            <td key={`${header}-${idx}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                                {String(row[header] ?? '')}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
                        <span className="text-sm text-gray-600">
                            Halaman {currentPage} dari {totalPages}
                        </span>
                        <div className="flex items-center space-x-2">
                            <Button size="sm" variant='outline' onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>Sebelumnya</Button>
                            <Button size="sm" variant='outline' onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>Berikutnya</Button>
                        </div>
                    </div>
                </Card.Content>
            </Card>
        </div>
    );
};

export default MasterData;