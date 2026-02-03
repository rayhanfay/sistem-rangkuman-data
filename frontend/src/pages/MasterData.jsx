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
                arguments: { sheet_name: 'MasterDataAsset' }
            });
            setMasterData(result.content);
        } catch (err) {
            setError(err.message || 'Gagal memuat master data.');
            showToast(err.message || 'Gagal memuat master data.', 'error');
        } finally {
            setLoading(false);
        }
    }, [mcpService, mcpStatus, showToast]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const { areaOptions, kondisiOptions } = useMemo(() => {
        if (!masterData) return { areaOptions: ['Semua'], kondisiOptions: ['Semua'] };
        const uniqueAreas = new Set(masterData.map(item => item.AREA).filter(Boolean));
        const uniqueKondisi = new Set(masterData.map(item => item.KONDISI).filter(Boolean));
        return {
            areaOptions: ['Semua', ...Array.from(uniqueAreas).sort()],
            kondisiOptions: ['Semua', ...Array.from(uniqueKondisi).sort()]
        };
    }, [masterData]);

    const processedData = useMemo(() => {
        if (!masterData) return [];
        let data = [...masterData];

        if (filterArea !== 'Semua') {
            data = data.filter(item => item.AREA === filterArea);
        }
        if (filterKondisi !== 'Semua') {
            data = data.filter(item => item.KONDISI === filterKondisi);
        }
        if (searchTerm) {
            const lowercasedTerm = searchTerm.toLowerCase();
            data = data.filter(item => 
                Object.values(item).some(value => String(value).toLowerCase().includes(lowercasedTerm))
            );
        }
        if (sortConfig.key && sortConfig.direction !== 'none') {
            data.sort((a, b) => {
                let aValue = a[sortConfig.key];
                let bValue = b[sortConfig.key];
                if (sortConfig.key === 'NILAI ASET') {
                    aValue = parseInt(String(aValue).replace(/[^0-9]/g, ''), 10) || 0;
                    bValue = parseInt(String(bValue).replace(/[^0-9]/g, ''), 10) || 0;
                } else if (sortConfig.key === 'TANGGAL INVENTORY' || sortConfig.key === 'TANGGAL UPDATE') {
                    aValue = new Date(aValue).getTime() || 0;
                    bValue = new Date(bValue).getTime() || 0;
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
    const tableHeaders = masterData.length > 0 ? Object.keys(masterData[0]) : [];
    const handlePageChange = (page) => {
        if (page >= 1 && page <= totalPages) setCurrentPage(page);
    };

    if (loading) return <LoadingOverlay />;

    if (error) {
        return (
            <Card className="p-8 text-center"><AlertCircle className="mx-auto h-12 w-12 text-red-400" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">Gagal Memuat Data</h3>
                <p className="mt-1 text-sm text-gray-500">{error}</p>
                <Button onClick={fetchData} className="mt-4"><RefreshCw className="mr-2 h-4 w-4" /> Coba Lagi</Button>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold">Master Data Aset</h1>
                    <p className="text-text-secondary mt-1">
                        Tampilan data mentah langsung dari Google Spreadsheet sheet 'MasterDataAsset'.
                    </p>
                </div>
                <Button onClick={fetchData} variant="outline"><RefreshCw className="mr-2 h-4 w-4" /> Refresh Data</Button>
            </div>
            <Card>
                <Card.Content className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 p-4 bg-gray-50 rounded-lg border">
                        <div className="md:col-span-3">
                            <label className="text-sm font-medium">Cari Cepat</label>
                            <Input type="text" placeholder="Cari di semua kolom..." value={searchTerm} onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }} className="mt-1" />
                        </div>
                        <div className="w-full">
                            <label className="text-sm font-medium">Filter Area</label>
                            <select value={filterArea} onChange={e => { setFilterArea(e.target.value); setCurrentPage(1); }} className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300">
                                {areaOptions.map(area => <option key={area} value={area}>{area}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label className="text-sm font-medium">Filter Kondisi</label>
                            <select value={filterKondisi} onChange={e => { setFilterKondisi(e.target.value); setCurrentPage(1); }} className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300">
                                {kondisiOptions.map(kondisi => <option key={kondisi} value={kondisi}>{kondisi}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label className="text-sm font-medium">Urutkan Berdasarkan</label>
                            <select
                                onChange={(e) => {
                                    const [key, direction] = e.target.value.split('-');
                                    setSortConfig({ key, direction });
                                    setCurrentPage(1);
                                }}
                                className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300"
                            >
                                <option value="none-none">Default</option>
                                <option value="NILAI ASET-descending">Nilai Aset (Tertinggi)</option>
                                <option value="NILAI ASET-ascending">Nilai Aset (Terendah)</option>
                                <option value="TANGGAL INVENTORY-descending">Tgl. Inventory (Terbaru)</option>
                                <option value="TANGGAL INVENTORY-ascending">Tgl. Inventory (Terlama)</option>
                                <option value="TANGGAL UPDATE-descending">Tgl. Update (Terbaru)</option>
                                <option value="TANGGAL UPDATE-ascending">Tgl. Update (Terlama)</option>
                            </select>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        {currentTableData.length > 0 ? (
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>{tableHeaders.map(key => <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{key}</th>)}</tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {currentTableData.map((row, index) => (
                                        <tr key={index}>{tableHeaders.map(header => (
                                            <td key={header} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{String(row[header] === null || row[header] === undefined ? '' : row[header])}</td>
                                        ))}</tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (<div className="text-center p-8 text-gray-500"><p>Tidak ada data yang cocok dengan kriteria Anda.</p></div>)}
                    </div>
                    {totalPages > 1 && (
                        <div className="mt-4 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <span className="text-sm">Menampilkan {currentTableData.length} dari {processedData.length} baris (Halaman {currentPage} dari {totalPages})</span>
                            {/* === PERBAIKAN TATA LETAK DI SINI === */}
                            <div className="flex items-center space-x-2">
                                <Button size="sm" variant='outline' onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>Sebelumnya</Button>
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