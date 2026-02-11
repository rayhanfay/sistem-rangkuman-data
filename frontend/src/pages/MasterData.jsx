import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useToast } from '../contexts/ToastContext';
import { useMcp } from '../contexts/McpProvider';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import LoadingOverlay from '../components/common/LoadingOverlay';
import { Database, AlertCircle, RefreshCw } from 'lucide-react';

// Import Utilities (Mencegah Duplikasi Code & ReDoS)
import { sortAssetData } from '../utils/assetUtils';

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

    /**
     * Mengambil data mentah dari link MASTER
     */
    const fetchData = useCallback(async () => {
        if (mcpStatus !== 'connected') return;

        setLoading(true);
        setError('');
        try {
            const result = await mcpService.call('tools/call', {
                name: 'get_master_data',
                arguments: { sheet_name: 'MASTER-SHEET', source: 'master' }
            });
            // Reliability fix: Optional chaining
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

    // Memoize filter options
    const { areaOptions, kondisiOptions } = useMemo(() => {
        if (!masterData?.length) return { areaOptions: ['Semua'], kondisiOptions: ['Semua'] };
        
        const uniqueAreas = new Set(masterData.map(item => item.AREA).filter(Boolean));
        const uniqueKondisi = new Set(masterData.map(item => item.KONDISI).filter(Boolean));
        
        const localeSort = (a, b) => a.localeCompare(b);
        return {
            areaOptions: ['Semua', ...Array.from(uniqueAreas).sort(localeSort)],
            kondisiOptions: ['Semua', ...Array.from(uniqueKondisi).sort(localeSort)]
        };
    }, [masterData]);

    /**
     * Memproses data (Filter & Sort menggunakan Shared Utility)
     */
    const processedData = useMemo(() => {
        if (!masterData?.length) return [];
        let filtered = [...masterData];

        // 1. Filtering Logic
        if (filterArea !== 'Semua') {
            filtered = filtered.filter(item => item.AREA === filterArea);
        }
        if (filterKondisi !== 'Semua') {
            filtered = filtered.filter(item => item.KONDISI === filterKondisi);
        }
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(item => 
                Object.values(item).some(value => String(value || '').toLowerCase().includes(term))
            );
        }

        // 2. Sorting Logic (Panggil Shared Utility untuk fix bug angka jutaan)
        return sortAssetData(filtered, sortConfig);
    }, [masterData, searchTerm, filterArea, filterKondisi, sortConfig]);

    const totalPages = Math.ceil(processedData.length / rowsPerPage);
    const currentTableData = processedData.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);
    const tableHeaders = masterData?.length > 0 ? Object.keys(masterData[0]) : [];

    const handlePageChange = (page) => {
        if (page >= 1 && page <= totalPages) setCurrentPage(page);
    };

    if (loading) return <LoadingOverlay />;

    if (error) {
        return (
            <Card className="p-8 text-center border-red-200 bg-red-50">
                <AlertCircle className="mx-auto h-12 w-12 text-brand-red" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">Gagal Memuat Data</h3>
                <p className="mt-1 text-sm text-gray-500">{error}</p>
                <Button onClick={fetchData} className="mt-4" variant="outline">
                    <RefreshCw className="mr-2 h-4 w-4" /> Coba Lagi
                </Button>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800">Master Data Aset</h1>
                    <p className="text-text-secondary mt-1">
                        Tampilan data mentah langsung dari sumber MASTER (Pusat).
                    </p>
                </div>
                <Button onClick={fetchData} variant="outline">
                    <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> 
                    Refresh Data
                </Button>
            </div>

            <Card shadow="subtle">
                <Card.Content className="p-4">
                    {/* Filter & Search Bar */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 p-4 bg-gray-50 rounded-lg border">
                        <div className="md:col-span-3">
                            <label htmlFor="master-search" className="text-sm font-medium text-gray-700">Cari Cepat</label>
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
                            <label htmlFor="master-area" className="text-sm font-medium text-gray-700">Filter Area</label>
                            <select 
                                id="master-area"
                                value={filterArea} 
                                onChange={e => { setFilterArea(e.target.value); setCurrentPage(1); }} 
                                className="mt-1 w-full p-2 border rounded-md bg-white focus:ring-2 focus:ring-brand-blue"
                            >
                                {areaOptions.map(area => <option key={area} value={area}>{area}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label htmlFor="master-kondisi" className="text-sm font-medium text-gray-700">Filter Kondisi</label>
                            <select 
                                id="master-kondisi"
                                value={filterKondisi} 
                                onChange={e => { setFilterKondisi(e.target.value); setCurrentPage(1); }} 
                                className="mt-1 w-full p-2 border rounded-md bg-white focus:ring-2 focus:ring-brand-blue"
                            >
                                {kondisiOptions.map(kondisi => <option key={kondisi} value={kondisi}>{kondisi}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label htmlFor="master-sort" className="text-sm font-medium text-gray-700">Urutkan</label>
                            <select
                                id="master-sort"
                                className="mt-1 w-full p-2 border rounded-md bg-white focus:ring-2 focus:ring-brand-blue"
                                onChange={(e) => {
                                    const [keyRaw, direction] = e.target.value.split('-');
                                    // Flex-matching key untuk handle kolom dinamis seperti "NILAI ASET (Rp)"
                                    const actualKey = tableHeaders.find(h => h.includes(keyRaw)) || keyRaw;
                                    setSortConfig({ key: actualKey, direction });
                                    setCurrentPage(1);
                                }}
                            >
                                <option value="none-none">Default</option>
                                <option value="NILAI ASET-descending">Nilai Aset (Tertinggi)</option>
                                <option value="NILAI ASET-ascending">Nilai Aset (Terendah)</option>
                                <option value="TANGGAL INVENTORY-descending">Tgl. Inventory (Terbaru)</option>
                                <option value="TANGGAL INVENTORY-ascending">Tgl. Inventory (Terlama)</option>
                            </select>
                        </div>
                    </div>

                    {/* Table Section */}
                    <div className="overflow-x-auto">
                        {currentTableData.length > 0 ? (
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
                                        <tr key={row['NO ASSET'] || `master-row-${idx}`} className="hover:bg-gray-50 transition-colors">
                                            {tableHeaders.map(header => (
                                                <td key={`${header}-${idx}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                                    {String(row[header] ?? '-')}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div className="text-center p-12 text-gray-400">
                                <AlertCircle className="mx-auto h-12 w-12 mb-4 opacity-20" />
                                <p className="text-lg font-medium">Data tidak ditemukan.</p>
                            </div>
                        )}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <span className="text-sm text-gray-600">
                                Menampilkan {currentTableData.length} dari {processedData.length} baris
                            </span>
                            <div className="flex items-center space-x-2">
                                <Button size="sm" variant='outline' onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>Sebelumnya</Button>
                                <div className="px-4 py-1 text-sm font-medium bg-gray-100 rounded-md">{currentPage} / {totalPages}</div>
                                <Button size="sm" variant='outline' onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>Berikutnya</Button>
                            </div>
                        </div>
                    )}
                </Card.Content>
            </Card>
        </div>
    );
};

export default MasterData;