import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    History as HistoryIcon, 
    FileText, 
    Trash2, 
    Eye, 
    RefreshCw, 
    AlertCircle, 
    Filter, 
    Download, 
    ChevronDown, 
    User,
    BarChart3, 
    RefreshCcw 
} from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import LoadingOverlay from '../components/common/LoadingOverlay';
import ConfirmationModal from '../components/common/ConfirmationModal';
import { useToast } from '../contexts/ToastContext';
import { useMcp } from '../contexts/McpProvider';
import apiService from '../services/api';

const History = () => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [deleting, setDeleting] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [itemToDelete, setItemToDelete] = useState(null);
    const [filterType, setFilterType] = useState('Semua');
    const [currentPage, setCurrentPage] = useState(1);
    const [openDownloadMenu, setOpenDownloadMenu] = useState(null);
    const [openDetailMenu, setOpenDetailMenu] = useState(null);
    const rowsPerPage = 10;

    const navigate = useNavigate();
    const { showToast } = useToast();
    const { service: mcpService, status: mcpStatus } = useMcp();

    const fetchHistory = useCallback(async () => {
        if (mcpStatus !== 'connected') return;

        setLoading(true);
        setError('');
        try {
            const result = await mcpService.call('tools/call', { 
                name: 'get_history', 
                arguments: {} 
            });
            setHistory(result.content);
        } catch (err) {
            console.error('Failed to fetch history:', err);
            setError(err.message || 'Gagal memuat riwayat.');
            showToast(err.message || 'Gagal memuat riwayat.', 'error');
        } finally {
            setLoading(false);
        }
    }, [mcpService, mcpStatus, showToast]);

    useEffect(() => {
        fetchHistory();
    }, [fetchHistory]);

    const confirmDelete = async () => {
        if (!itemToDelete || mcpStatus !== 'connected') return;
        
        setDeleting(itemToDelete.timestamp);
        setIsModalOpen(false);
        try {
            await mcpService.call('tools/call', {
                name: 'delete_history',
                arguments: { timestamp: itemToDelete.timestamp }
            });
            showToast('Item riwayat berhasil dihapus.', 'success');
            fetchHistory();
        } catch (err) {
            console.error('Failed to delete:', err);
            showToast(err.message || 'Gagal menghapus item.', 'error');
        } finally {
            setDeleting(null);
            setItemToDelete(null);
        }
    };
    
    const handleDownload = (format, timestamp) => {
        const params = {
            file_format: format,
            source: 'history',
            timestamp: timestamp,
            area: 'Semua Area',
        };
        apiService.downloadAnalyzedData(params)
            .catch(err => showToast(`Gagal mengunduh file: ${err.message}`, 'error'));
        setOpenDownloadMenu(null);
    };

    const filteredHistory = useMemo(() => {
        if (filterType === 'Semua') return history;
        return history.filter(item => item.filename.includes(filterType));
    }, [history, filterType]);

    const totalPages = Math.ceil(filteredHistory.length / rowsPerPage);
    const currentItems = filteredHistory.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

    const handleDeleteClick = (item) => {
        setItemToDelete(item);
        setIsModalOpen(true);
    };

    const handleRefresh = () => fetchHistory();
    const handlePageChange = (page) => {
        if (page > 0 && page <= totalPages) setCurrentPage(page);
    };

    if (loading) {
        return <LoadingOverlay />;
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto">
                <Card className="p-8 text-center">
                    <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">Gagal Memuat Riwayat</h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <Button onClick={handleRefresh}>
                        <RefreshCw className="mr-2" size={16} /> Coba Lagi
                    </Button>
                </Card>
            </div>
        );
    }

    return (
        <>
            <ConfirmationModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onConfirm={confirmDelete}
                title="Konfirmasi Penghapusan"
                message={`Yakin ingin menghapus riwayat "${itemToDelete?.filename}"?`}
            />
            <div className="space-y-8">
                <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Riwayat Analisis</h1>
                        <p className="text-gray-600 mt-1">Daftar semua analisis data aset yang telah dilakukan.</p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap justify-start md:justify-end">
                        <div className="flex items-center gap-2">
                            <Filter className="h-4 w-4 text-gray-500" />
                           <select
                                id="filter-history"
                                value={filterType}
                                onChange={(e) => { setFilterType(e.target.value); setCurrentPage(1); }}
                                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-brand-blue focus:border-brand-blue block p-2"
                            >
                                <option value="Semua">Semua Jenis</option>
                                <option value="Manual">Laporan Manual</option>
                                <option value="Otomatis">Laporan Otomatis</option>
                            </select>
                        </div>
                        <Button onClick={handleRefresh} variant="outline" disabled={loading}>
                            <RefreshCw className={`mr-2 ${loading ? 'animate-spin' : ''}`} size={16} /> Refresh
                        </Button>
                    </div>
                </div>

                {history.length === 0 ? (
                    <Card className="p-8 text-center">
                        <HistoryIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-gray-800 mb-2">Belum Ada Riwayat</h2>
                        <p className="text-gray-600 mb-6">Mulai analisis data di Dashboard untuk melihat riwayat di sini.</p>
                        <Button onClick={() => navigate('/')}>Ke Dashboard</Button>
                    </Card>
                ) : (
                    <>
                        <div className="space-y-4">
                            {currentItems.length > 0 ? currentItems.map((item) => (
                                <Card key={item.timestamp} className="p-4 hover:shadow-lg transition-shadow duration-200">
                                    <div className="flex flex-col sm:flex-row sm:justify-between gap-4">
                                        <div className="flex items-start space-x-4 min-w-0">
                                            <div className="p-3 bg-blue-100 rounded-full mt-1 flex-shrink-0">
                                                <FileText className="h-6 w-6 text-blue-600" />
                                            </div>
                                            <div className="min-w-0">
                                                <h3 className="text-lg font-semibold text-gray-800 break-words">{item.filename}</h3>
                                                <p className="text-sm text-gray-600 mt-1">
                                                    {new Date(item.upload_date).toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' })}
                                                </p>
                                                {item.user_email && (
                                                    <p className="text-xs text-gray-500 mt-2 pt-2 border-t flex items-center gap-2">
                                                        <User size={12} />
                                                        Dianalisis oleh: <span className="font-medium text-gray-700">{item.user_email}</span>
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                        
                                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 w-full sm:w-auto sm:min-w-[300px] self-end sm:self-center">
                                            <div className="relative">
                                                <Button variant="secondary" size="sm" onClick={() => setOpenDownloadMenu(openDownloadMenu === item.timestamp ? null : item.timestamp)} className="w-full h-9 justify-center text-xs px-2">
                                                    <Download className="mr-1" size={14} /> Unduh <ChevronDown size={14} className={`ml-1 transition-transform ${openDownloadMenu === item.timestamp ? 'rotate-180' : ''}`} />
                                                </Button>
                                                {openDownloadMenu === item.timestamp && (
                                                    <div className="absolute right-0 mt-2 w-full bg-white rounded-md shadow-lg z-10 border">
                                                        <a href="#" onClick={(e) => { e.preventDefault(); handleDownload('csv', item.timestamp); }} className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Unduh CSV</a>
                                                        <a href="#" onClick={(e) => { e.preventDefault(); handleDownload('xlsx', item.timestamp); }} className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Unduh XLSX</a>
                                                    </div>
                                                )}
                                            </div>

                                            <div className="relative">
                                                <Button variant="outline" size="sm" onClick={() => setOpenDetailMenu(openDetailMenu === item.timestamp ? null : item.timestamp)} className="w-full h-9 justify-center text-xs px-2">
                                                    <Eye className="mr-1" size={14} /> Lihat Detail <ChevronDown size={14} className={`ml-1 transition-transform ${openDetailMenu === item.timestamp ? 'rotate-180' : ''}`} />
                                                </Button>
                                                {openDetailMenu === item.timestamp && (
                                                    <div className="absolute right-0 mt-2 w-full bg-white rounded-md shadow-lg z-10 border">
                                                        <a href="#" onClick={(e) => { e.preventDefault(); navigate(`/stats?timestamp=${item.timestamp}`); setOpenDetailMenu(null); }} className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                                          <BarChart3 size={14} /> Detail Statistik
                                                        </a>
                                                        <a href="#" onClick={(e) => { e.preventDefault(); navigate(`/cycle?timestamp=${item.timestamp}`); setOpenDetailMenu(null); }} className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                                          <RefreshCcw size={14} /> Detail Siklus Aset
                                                        </a>
                                                    </div>
                                                )}
                                            </div>

                                            <Button variant="danger" size="sm" onClick={() => handleDeleteClick(item)} disabled={deleting === item.timestamp} loading={deleting === item.timestamp} className="w-full h-9 justify-center text-xs px-2">
                                                <Trash2 className="mr-1" size={14} /> {deleting === item.timestamp ? 'Menghapus...' : 'Hapus'}
                                            </Button>
                                        </div>
                                    </div>
                                </Card>
                            )) : (
                                <Card className="p-8 text-center text-gray-500">
                                    <p>Tidak ada riwayat yang cocok dengan filter ini.</p>
                                </Card>
                            )}
                        </div>

                        {totalPages > 1 && (
                            <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
                                <span className="text-sm text-gray-700">Halaman {currentPage} dari {totalPages}</span>
                                <div className="flex items-center space-x-2">
                                    <Button size="sm" variant="outline" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>Sebelumnya</Button>
                                    <Button size="sm" variant="outline" onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>Berikutnya</Button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </>
    );
};

export default History;