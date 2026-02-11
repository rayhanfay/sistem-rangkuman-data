import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { useMcp } from '../contexts/McpProvider';
import { useAuth } from '../hooks/useAuth';
import { getAuth, getIdToken } from "firebase/auth";
import apiService from '../services/api';

// UI Components
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import LoadingOverlay from '../components/common/LoadingOverlay';

// Icons
import { 
    RefreshCcw, 
    AlertCircle, 
    RefreshCw, 
    Clock, 
    Save, 
    Download, 
    ChevronDown 
} from 'lucide-react';

// Utilities & Hooks (Solusi untuk Sonar Duplicated Code & ReDoS)
import { parseAndFormatDate } from '../utils/assetUtils';
import { useAssetDataProcessor } from '../hooks/useAssetDataProcessor';

const Cycle = () => {
    // --- State Lokal & Hooks ---
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [isDownloadOpen, setIsDownloadOpen] = useState(false);
    
    const rowsPerPage = 50;
    const navigate = useNavigate();
    const location = useLocation();
    const { showToast } = useToast();
    const { service: mcpService, status: mcpStatus } = useMcp();
    const { user } = useAuth();

    // --- Integrasi useAssetDataProcessor ---
    // Logika Search, Filter Area, Filter Kondisi, dan Sort dipindahkan ke sini
    const { 
        searchTerm, 
        setSearchTerm, 
        filterArea, 
        setFilterArea, 
        filterKondisi, 
        setFilterKondisi,
        sortConfig, 
        setSortConfig, 
        currentPage, 
        setCurrentPage, 
        processedData 
    } = useAssetDataProcessor(data?.cycle_assets_table, 'Semua Area');

    /**
     * Mengambil data siklus berdasarkan URL parameter atau Dashboard default
     */
    const fetchCycleData = useCallback(async () => {
        if (mcpStatus !== 'connected') return;

        const timestamp = new URLSearchParams(location.search).get('timestamp');
        setLoading(true);
        setError('');

        try {
            const toolToCall = timestamp ? 'get_stats_data' : 'get_dashboard_data';
            const argumentsToCall = timestamp ? { timestamp } : {};
            
            const result = await mcpService.call('tools/call', {
                name: toolToCall,
                arguments: argumentsToCall
            });
            
            const content = result?.content;
            if (!content || !content.data_available) {
                throw new Error(content?.message || "Data untuk siklus aset tidak ditemukan.");
            }
            setData(content);
        } catch (err) {
            setData(null);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [mcpService, mcpStatus, location.search]);

    useEffect(() => {
        if (mcpStatus === 'connected') {
            fetchCycleData();
        }
    }, [fetchCycleData, mcpStatus]);

    /**
     * Menyimpan hasil analisis dashboard ke dalam riwayat database
     */
    const handleSaveAnalysis = async () => {
        if (mcpStatus !== 'connected' || !user) {
            showToast('Koneksi atau sesi pengguna tidak valid.', 'warning');
            return;
        }
        setIsSaving(true);
        try {
            const auth = getAuth();
            const token = await getIdToken(auth.currentUser);
            const result = await mcpService.call('tools/call', { 
                name: 'save_analysis',
                arguments: { auth_token: token }
            });
            showToast('Analisis berhasil disimpan!', 'success');
            navigate(`/stats?timestamp=${result?.content?.timestamp}`);
        } catch (err) {
            showToast(err.message || 'Gagal menyimpan analisis.', 'error');
        } finally {
            setIsSaving(false);
        }
    };

    /**
     * Menangani pengunduhan file data (CSV/XLSX)
     */
    const handleDownload = (format) => {
        if (!data?.data_available) {
            showToast("Tidak ada data untuk diunduh.", 'warning');
            return;
        }
        const params = {
            file_format: format,
            source: data.is_temporary ? 'temporary' : 'history',
            timestamp: data.is_temporary ? null : data.timestamp,
            area: filterArea,
            sheet_name: data.is_temporary ? (data.sheet_name || 'MASTER-SHEET') : null,
        };
        apiService.downloadAnalyzedData(params)
            .catch(err => showToast(`Gagal mengunduh file: ${err.message}`, 'error'));
        setIsDownloadOpen(false);
    };

    // Memoize pilihan filter unik dari data aset
    const { areaOptions, kondisiOptions } = useMemo(() => {
        if (!data?.cycle_assets_table) return { areaOptions: ['Semua Area'], kondisiOptions: ['Semua'] };
        const uniqueAreas = new Set(data.cycle_assets_table.map(item => item.AREA).filter(Boolean));
        const uniqueKondisi = new Set(data.cycle_assets_table.map(item => item.KONDISI).filter(Boolean));
        
        const localeSort = (a, b) => a.localeCompare(b);
        return {
            areaOptions: ['Semua Area', ...Array.from(uniqueAreas).sort(localeSort)],
            kondisiOptions: ['Semua', ...Array.from(uniqueKondisi).sort(localeSort)]
        };
    }, [data]);

    // Metadata untuk Tabel & Pagination
    const tableHeaders = data?.cycle_assets_table?.[0] ? Object.keys(data.cycle_assets_table[0]) : [];
    const totalPages = Math.ceil(processedData.length / rowsPerPage);
    const currentTableData = processedData.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);
    
    const handlePageChange = (pageNumber) => {
        if (pageNumber >= 1 && pageNumber <= totalPages) {
            setCurrentPage(pageNumber);
        }
    };
    
    if (loading) return <LoadingOverlay />;
    
    if (error || !data) {
        return (
            <Card className="p-8 text-center bg-red-50 border-red-200">
                <AlertCircle className="h-16 w-16 text-brand-red mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Gagal Memuat Data</h2>
                <p className="text-gray-600">{error || "Data siklus aset tidak tersedia."}</p>
                <Button onClick={fetchCycleData} className="mt-4" variant="outline">Coba Lagi</Button>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header & Tombol Aksi */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800">Rekomendasi Siklus Aset</h1>
                    <p className="text-gray-600 mt-1">
                        Daftar aset yang direkomendasikan untuk peremajaan atau penggantian.
                    </p>
                </div>
                <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                    <Button onClick={fetchCycleData} variant="outline" disabled={loading || isSaving}>
                        <RefreshCw className={`mr-2 ${loading ? 'animate-spin' : ''}`} size={16} /> Refresh
                    </Button>
                    {data?.is_temporary && (
                        <Button onClick={handleSaveAnalysis} disabled={isSaving || loading} loading={isSaving} variant="success">
                            <Save className="mr-2" size={16} /> Simpan Analisis
                        </Button>
                    )}
                    <div className="relative w-full sm:w-auto">
                        <Button onClick={() => setIsDownloadOpen(!isDownloadOpen)} variant="secondary" disabled={loading || isSaving || !data?.cycle_assets_table?.length} className="w-full">
                            <Download className="mr-2" size={16} /> Unduh Data <ChevronDown size={16} className={`ml-1 transition-transform ${isDownloadOpen ? 'rotate-180' : ''}`} />
                        </Button>
                        {isDownloadOpen && (
                            <div className="absolute right-0 mt-2 w-full sm:w-48 bg-white rounded-md shadow-lg z-10 border overflow-hidden">
                                <button type="button" onClick={() => handleDownload('csv')} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-b">Unduh sebagai CSV</button>
                                <button type="button" onClick={() => handleDownload('xlsx')} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Unduh sebagai XLSX</button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Kartu Status Waktu Analisis */}
            <Card shadow="subtle" className="p-4 flex items-center space-x-4 bg-blue-50 border-blue-200">
                <div className="p-3 bg-brand-blue/10 rounded-full">
                    <Clock className="h-6 w-6 text-brand-blue" />
                </div>
                <div>
                    <p className="text-sm text-text-secondary">Waktu Analisis Terakhir</p>
                    <p className="text-lg font-bold text-text-primary">
                        {parseAndFormatDate(data.last_updated || data.timestamp)}
                    </p>
                </div>
            </Card>

            {/* Bagian Utama: Filter & Tabel */}
            <Card shadow="subtle">
                <Card.Header className="p-4 border-b flex items-center">
                    <RefreshCcw className="h-5 w-5 text-brand-green mr-3" />
                    <Card.Title>Tabel Daftar Rekomendasi</Card.Title>
                </Card.Header>
                <Card.Content className="p-4">
                    {/* Control Grid: Pencarian, Filter, dan Sortir */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 p-4 bg-gray-50 rounded-lg border">
                        <div className="md:col-span-3">
                            <label htmlFor="cycle-search" className="text-sm font-medium text-gray-700">Cari Cepat</label>
                            <Input 
                                id="cycle-search"
                                type="text" 
                                placeholder="Cari aset di semua kolom..." 
                                value={searchTerm} 
                                onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }} 
                                className="mt-1" 
                            />
                        </div>
                        <div className="w-full">
                            <label htmlFor="cycle-filter-area" className="text-sm font-medium text-gray-700">Filter Area</label>
                            <select 
                                id="cycle-filter-area"
                                value={filterArea} 
                                onChange={e => { setFilterArea(e.target.value); setCurrentPage(1); }} 
                                className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300 focus:ring-2 focus:ring-brand-blue"
                            >
                                {areaOptions.map(area => <option key={area} value={area}>{area}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label htmlFor="cycle-filter-kondisi" className="text-sm font-medium text-gray-700">Filter Kondisi</label>
                            <select 
                                id="cycle-filter-kondisi"
                                value={filterKondisi} 
                                onChange={e => { setFilterKondisi(e.target.value); setCurrentPage(1); }} 
                                className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300 focus:ring-2 focus:ring-brand-blue"
                            >
                                {kondisiOptions.map(kondisi => <option key={kondisi} value={kondisi}>{kondisi}</option>)}
                            </select>
                        </div>
                        <div className="w-full">
                            <label htmlFor="cycle-sort-select" className="text-sm font-medium text-gray-700">Urutkan Berdasarkan</label>
                            <select
                                id="cycle-sort-select"
                                className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300 focus:ring-2 focus:ring-brand-blue"
                                onChange={(e) => {
                                    const [keyRaw, direction] = e.target.value.split('-');
                                    // Mencari key asli dari header tabel (untuk support label dinamis)
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

                    {/* Render Tabel Data Aset */}
                    <div className="overflow-x-auto">
                        {currentTableData.length > 0 ? (
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        {tableHeaders.map(key => (
                                            <th key={key} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                {key}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {currentTableData.map((row, idx) => (
                                        <tr key={row['NO ASSET'] || `cycle-row-${idx}`} className="hover:bg-gray-50 transition-colors">
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
                            <div className="text-center p-12 text-gray-500">
                                <AlertCircle className="mx-auto h-12 w-12 mb-4 opacity-20" />
                                <p className="text-lg">Tidak ada aset yang ditemukan.</p>
                                <p className="text-sm">Cobalah untuk menyesuaikan filter atau pencarian Anda.</p>
                            </div>
                        )}
                    </div>

                    {/* Pagination Bar */}
                    {totalPages > 1 && (
                        <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <span className="text-sm text-gray-500">
                                Menampilkan {currentTableData.length} dari {processedData.length} baris
                            </span>
                            <div className="flex items-center space-x-2">
                                <Button size="sm" variant="outline" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>
                                    Sebelumnya
                                </Button>
                                <div className="px-4 py-1.5 text-sm font-medium bg-brand-blue/10 text-brand-blue rounded-md">
                                    {currentPage} / {totalPages}
                                </div>
                                <Button size="sm" variant="outline" onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>
                                    Berikutnya
                                </Button>
                            </div>
                        </div>
                    )}
                </Card.Content>
            </Card>
        </div>
    );
};

export default Cycle;