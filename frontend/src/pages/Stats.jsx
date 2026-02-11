import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { useMcp } from '../contexts/McpProvider';
import { useAuth } from '../hooks/useAuth';
import { getAuth, getIdToken } from "firebase/auth";
import apiService from '../services/api';

// Impor UI & Ikon
import {
    BarChart2,
    FileText,
    AlertCircle,
    RefreshCw,
    History,
    MapPin,
    Save,
    Download,
    ChevronDown,
    PieChart,
    TrendingUp,
    DollarSign
} from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import LoadingOverlay from '../components/common/LoadingOverlay';

// Impor Komponen Grafik dari Syncfusion
import {
    ChartComponent,
    SeriesCollectionDirective,
    SeriesDirective,
    Inject,
    Legend,
    Category,
    Tooltip,
    DataLabel,
    BarSeries,
    LineSeries
} from '@syncfusion/ej2-react-charts';
import {
    AccumulationChartComponent,
    AccumulationSeriesCollectionDirective,
    AccumulationSeriesDirective,
    PieSeries,
    AccumulationDataLabel,
    AccumulationTooltip,
    AccumulationLegend
} from '@syncfusion/ej2-react-charts';

const chartPalettes = ['#003A70', '#00A859', '#E82A2A', '#F7941E', '#5A6474', '#00B4F1'];

// Helper untuk format angka tanpa Regex (Mencegah ReDoS)
const formatIDRCurrency = (value) => {
    return new Intl.NumberFormat('id-ID').format(value);
};

const ChartCard = ({ title, icon: Icon, children }) => (
    <Card shadow="subtle">
        <Card.Header className="p-4 border-b flex items-center">
            <Icon className="h-5 w-5 text-brand-blue mr-3 flex-shrink-0" />
            <Card.Title>{title}</Card.Title>
        </Card.Header>
        <Card.Content className="p-4">
            {children}
        </Card.Content>
    </Card>
);

const Stats = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [isDownloadOpen, setIsDownloadOpen] = useState(false);
    const [selectedArea, setSelectedArea] = useState('Semua Area');
    const [availableAreas, setAvailableAreas] = useState(['Semua Area']);
    const [currentPage, setCurrentPage] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'none' });
    const [kondisiFilter, setKondisiFilter] = useState('Semua');
    const [isSummaryVisible, setIsSummaryVisible] = useState(false);
    
    const rowsPerPage = 50;
    const location = useLocation();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const { service: mcpService, status: mcpStatus } = useMcp();
    const { user } = useAuth();

    const getTimestampFromURL = () => new URLSearchParams(location.search).get('timestamp');

    const fetchStatsData = useCallback(async (timestamp, area) => {
        if (mcpStatus !== 'connected') return;

        setLoading(true);
        setError('');
        try {
            const result = await mcpService.call('tools/call', {
                name: 'get_stats_data',
                arguments: { timestamp, area }
            });

            const statsData = result?.content;
            if (!statsData?.data_available) {
                throw new Error(statsData?.error_message || "Data tidak ditemukan.");
            }
            setData(statsData);
            if (statsData.available_areas) {
                setAvailableAreas(statsData.available_areas);
            }
            setCurrentPage(1);
        } catch (err) {
            setData(null);
            setError(err.message);
            showToast(err.message, 'error');
        } finally {
            setLoading(false);
        }
    }, [mcpService, mcpStatus, showToast]);

    useEffect(() => {
        const timestamp = getTimestampFromURL();
        fetchStatsData(timestamp, selectedArea);
    }, [selectedArea, location.search, fetchStatsData]);

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
    
    const handleDownload = (format) => {
        if (!data?.data_available) {
            showToast("Tidak ada data untuk diunduh.", 'warning');
            return;
        }
        const params = {
            file_format: format,
            source: data.is_temporary ? 'temporary' : 'history',
            timestamp: data.is_temporary ? null : data.timestamp,
            area: selectedArea,
            sheet_name: null,
        };
        apiService.downloadAnalyzedData(params)
            .catch(err => showToast(`Gagal mengunduh file: ${err.message}`, 'error'));
        setIsDownloadOpen(false);
    };

    const kondisiOptions = useMemo(() => {
        if (!data?.table_data) return ['Semua'];
        const uniqueKondisi = new Set(data.table_data.map(item => item.KONDISI).filter(Boolean));
        return ['Semua', ...Array.from(uniqueKondisi).sort((a, b) => a.localeCompare(b))];
    }, [data]);

    const processedData = useMemo(() => {
        if (!data?.table_data) return [];
        let processed = [...data.table_data];

        if (kondisiFilter !== 'Semua') {
            processed = processed.filter(item => item.KONDISI === kondisiFilter);
        }
        if (searchTerm) {
            const lowercasedTerm = searchTerm.toLowerCase();
            processed = processed.filter(item => 
                Object.values(item).some(value => String(value || '').toLowerCase().includes(lowercasedTerm))
            );
        }

        // --- LOGIKA SORTING FIX (Dukungan Nilai Aset & Tgl Inventory) ---
        if (sortConfig.key && sortConfig.direction !== 'none') {
            processed.sort((a, b) => {
                const key = sortConfig.key;
                let aValue = a[key];
                let bValue = b[key];

                if (key.includes('NILAI ASET')) {
                    // Membersihkan format titik dan non-angka
                    const clean = (val) => parseInt(String(val || '0').replace(/[^0-9]/g, ''), 10) || 0;
                    aValue = clean(aValue);
                    bValue = clean(bValue);
                } else if (key.includes('TANGGAL')) {
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
        }
        return processed;
    }, [data, searchTerm, kondisiFilter, sortConfig]);

    const totalPages = Math.ceil(processedData.length / rowsPerPage);
    const currentTableData = processedData.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);
    const tableHeaders = data?.table_data?.length > 0 ? Object.keys(data.table_data[0]) : [];
    
    const handlePageChange = (pageNumber) => {
        if (pageNumber >= 1 && pageNumber <= totalPages) {
            setCurrentPage(pageNumber);
        }
    };
    
    const renderEmptyChart = (title) => (
        <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center p-4 bg-gray-50 rounded-lg">
            <BarChart2 className="w-12 h-12 text-gray-300 mb-4" />
            <h4 className="font-semibold text-gray-600">{title}</h4>
            <p className="text-sm text-gray-400">Data tidak tersedia.</p>
        </div>
    );

    // FIXED: Menggunakan Intl.NumberFormat untuk keamanan dan kecepatan (Bukan Regex)
    const onTooltipRender = (args) => {
        if (args.point && typeof args.point.y === 'number') {
            args.text = `<b>${args.point.x}</b><br/>Nilai: <b>Rp ${formatIDRCurrency(args.point.y)}</b>`;
        }
    };

    const onAxisLabelRender = (args) => {
        if (args.axis.name === 'primaryYAxis') {
            args.text = formatIDRCurrency(Number(args.value));
        }
    };

    if (loading) return <LoadingOverlay />;

    if (error) {
        return (
            <div className="max-w-4xl mx-auto">
                <Card className="p-8 text-center bg-red-50 border-red-200">
                    <AlertCircle className="h-16 w-16 text-brand-red mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">Gagal Memuat Data</h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <div className="flex justify-center space-x-4">
                        <Button onClick={() => fetchStatsData(getTimestampFromURL(), selectedArea)}>
                            <RefreshCw className="mr-2" size={16} /> Coba Lagi
                        </Button>
                        <Button variant="outline" onClick={() => navigate('/history')}>
                            <History className="mr-2" size={16} /> Lihat Riwayat
                        </Button>
                    </div>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Detail Statistik Analisis</h1>
                    <p className="text-gray-600 mt-1">
                        Hasil Analisis untuk Sheet: 
                        <span className="font-medium text-brand-blue break-all"> {data?.sheet_name || 'Tidak Diketahui'}</span>
                    </p>
                </div>
                <div className="flex flex-col sm:flex-row sm:flex-wrap justify-start md:justify-end gap-2 w-full md:w-auto">
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                        <label htmlFor="area-filter-stats" className="text-sm font-medium text-text-secondary flex items-center gap-2 flex-shrink-0">
                            <MapPin size={16}/>Filter Area:
                        </label>
                        <select 
                            id="area-filter-stats" 
                            value={selectedArea} 
                            onChange={(e) => setSelectedArea(e.target.value)} 
                            className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-brand-blue focus:border-brand-blue block w-full p-2" 
                            disabled={loading}
                        >
                            {availableAreas.map(area => (<option key={area} value={area}>{area}</option>))}
                        </select>
                    </div>
                    {data?.is_temporary && (
                        <Button onClick={handleSaveAnalysis} disabled={isSaving || loading} loading={isSaving} variant="success" className="w-full sm:w-auto">
                            <Save className="mr-2" size={16} /> Simpan
                        </Button>
                    )}
                    <div className="relative w-full sm:w-auto">
                        <Button onClick={() => setIsDownloadOpen(!isDownloadOpen)} variant="secondary" disabled={loading || !data?.data_available} className="flex items-center justify-center w-full">
                            <Download className="mr-2" size={16} /> Unduh Data <ChevronDown size={16} className={`ml-1 transition-transform ${isDownloadOpen ? 'rotate-180' : ''}`} />
                        </Button>
                        {isDownloadOpen && (
                            <div className="absolute right-0 mt-2 w-full sm:w-48 bg-white rounded-md shadow-lg z-10 border overflow-hidden">
                                <button 
                                    type="button"
                                    onClick={() => handleDownload('csv')} 
                                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-b"
                                >
                                    Unduh sebagai CSV
                                </button>
                                <button 
                                    type="button"
                                    onClick={() => handleDownload('xlsx')} 
                                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                >
                                    Unduh sebagai XLSX
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartCard title="Distribusi Kondisi Aset" icon={PieChart}>
                    {data?.chart_data?.kondisi?.length > 0 ? (
                        <AccumulationChartComponent id="stats-pie-kondisi" legendSettings={{ visible: true, position: 'Bottom' }} tooltip={{ enable: true, format: '${point.x}: <b>${point.y} unit</b>' }} palettes={chartPalettes}>
                            <Inject services={[PieSeries, AccumulationDataLabel, AccumulationTooltip, AccumulationLegend]} />
                            <AccumulationSeriesCollectionDirective>
                                <AccumulationSeriesDirective dataSource={data.chart_data.kondisi} xName="x" yName="y" innerRadius="40%" dataLabel={{ visible: true, name: 'text', position: 'Inside', font: { fontWeight: '600', color: '#fff' } }} />
                            </AccumulationSeriesCollectionDirective>
                        </AccumulationChartComponent>
                    ) : renderEmptyChart("Distribusi Kondisi Aset")}
                </ChartCard>
                <ChartCard title="Distribusi Hasil Inventaris" icon={PieChart}>
                    {data?.chart_data?.hasilInventory?.length > 0 ? (
                        <AccumulationChartComponent id="stats-pie-hasil" legendSettings={{ visible: true, position: 'Bottom' }} tooltip={{ enable: true, format: '${point.x}: <b>${point.y} unit</b>' }} palettes={chartPalettes}>
                            <Inject services={[PieSeries, AccumulationDataLabel, AccumulationTooltip, AccumulationLegend]} />
                            <AccumulationSeriesCollectionDirective>
                                <AccumulationSeriesDirective dataSource={data.chart_data.hasilInventory} xName="x" yName="y" innerRadius="40%" dataLabel={{ visible: true, name: 'text', position: 'Inside', font: { fontWeight: '600', color: '#fff' } }} />
                            </AccumulationSeriesCollectionDirective>
                        </AccumulationChartComponent>
                    ) : renderEmptyChart("Distribusi Hasil Inventaris")}
                </ChartCard>
                <ChartCard title="Total Nilai Aset per Lokasi (Top 10)" icon={DollarSign}>
                    {data?.chart_data?.assetValue?.length > 0 ? (
                        <ChartComponent id="stats-bar-nilai" primaryXAxis={{ valueType: 'Category', majorGridLines: { width: 0 }, labelRotation: -45, labelIntersectAction: 'Rotate45' }} primaryYAxis={{ title: 'Nilai Aset (Rp)', edgeLabelPlacement: 'Shift' }} tooltipRender={onTooltipRender} tooltip={{ enable: true }} palettes={chartPalettes} axisLabelRender={onAxisLabelRender}>
                            <Inject services={[BarSeries, Legend, Tooltip, DataLabel, Category]} />
                            <SeriesCollectionDirective>
                                <SeriesDirective dataSource={data.chart_data.assetValue} xName="x" yName="y" type="Bar" name="Nilai Aset" />
                            </SeriesCollectionDirective>
                        </ChartComponent>
                    ) : renderEmptyChart("Total Nilai Aset per Lokasi")}
                </ChartCard>
                <ChartCard title="Tren Inventaris Bulanan" icon={TrendingUp}>
                    {data?.chart_data?.trenInventory?.length > 0 ? (
                        <ChartComponent id="stats-line-tren" primaryXAxis={{ valueType: 'Category', labelRotation: -45, labelIntersectAction: 'Rotate45' }} primaryYAxis={{ title: 'Jumlah Aset Diinventaris', minimum: 0 }} tooltip={{ enable: true, format: '${point.x}: <b>${point.y}</b>' }} palettes={chartPalettes}>
                            <Inject services={[LineSeries, Legend, Tooltip, DataLabel, Category]} />
                            <SeriesCollectionDirective>
                                <SeriesDirective dataSource={data.chart_data.trenInventory} xName="x" yName="y" type="Line" name="Jumlah" marker={{ visible: true, width: 10, height: 10 }} />
                            </SeriesCollectionDirective>
                        </ChartComponent>
                    ) : renderEmptyChart("Tren Inventaris Bulanan")}
                </ChartCard>
            </div>
            
            <Card shadow="subtle">
                <Card.Header 
                    className="p-4 border-b flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors" 
                    onClick={() => setIsSummaryVisible(!isSummaryVisible)}
                >
                    <div className="flex items-center">
                        <FileText className="h-5 w-5 text-brand-blue mr-3" />
                        <Card.Title>Analisa Rangkuman (AI)</Card.Title>
                    </div>
                    <div className='flex items-center text-sm font-medium text-brand-blue'>
                        <span>{isSummaryVisible ? 'Sembunyikan' : 'Tampilkan'}</span>
                        <ChevronDown size={20} className={`ml-1 transition-transform duration-300 ${isSummaryVisible ? 'rotate-180' : ''}`} />
                    </div>
                </Card.Header>
                {isSummaryVisible && (
                     <Card.Content className="p-6">
                         <div
                             className="prose max-w-none prose-li:my-2 prose-strong:text-text-primary prose-strong:font-semibold whitespace-pre-line"
                             dangerouslySetInnerHTML={{ __html: data?.summary_text || '<p class="text-gray-500">Tidak ada rangkuman yang dihasilkan untuk analisis ini.</p>' }}
                         />
                     </Card.Content>
                )}
            </Card>

            <Card shadow="subtle">
                <Card.Header className="p-4 border-b flex items-center">
                    <BarChart2 className="h-5 w-5 text-brand-green mr-3" />
                    <Card.Title>Data Tabel Mentah</Card.Title>
                </Card.Header>
                <Card.Content className="p-4">
                    <div className="flex flex-col md:flex-row gap-4 mb-4 p-4 bg-gray-50 rounded-lg border">
                        <div className="flex-grow">
                            <label htmlFor="search-table-stats" className="text-sm font-medium text-gray-700">Cari Data</label>
                            <Input id="search-table-stats" type="text" placeholder="Ketik untuk mencari di semua kolom..." value={searchTerm} onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }} className="mt-1" />
                        </div>
                        <div className="w-full md:w-48">
                            <label htmlFor="kondisi-filter-stats" className="text-sm font-medium text-gray-700">Filter Kondisi</label>
                            <select id="kondisi-filter-stats" value={kondisiFilter} onChange={(e) => { setKondisiFilter(e.target.value); setCurrentPage(1); }} className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300 focus:ring-2 focus:ring-brand-blue">
                                {kondisiOptions.map(opsi => <option key={opsi} value={opsi}>{opsi}</option>)}
                            </select>
                        </div>
                        <div className="w-full md:w-56">
                            <label htmlFor="sort-filter-stats" className="text-sm font-medium text-gray-700">Urutkan Berdasarkan</label>
                            <select 
                                id="sort-filter-stats" 
                                onChange={(e) => { 
                                    const direction = e.target.value.split('-')[1];
                                    const keyRaw = e.target.value.split('-')[0];
                                    const actualKey = tableHeaders.find(h => h.includes(keyRaw)) || keyRaw;
                                    setSortConfig({ key: actualKey, direction }); 
                                    setCurrentPage(1); 
                                }} 
                                className="mt-1 w-full p-2 border rounded-md bg-white border-gray-300 focus:ring-2 focus:ring-brand-blue"
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
                                    {currentTableData.map((row, index) => (
                                        <tr key={row['NO ASSET'] || index} className="hover:bg-gray-50">
                                            {tableHeaders.map(header => (
                                                <td key={`${header}-${index}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                                    {String(row[header] ?? '')}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div className="text-center p-8 text-gray-500">
                                <AlertCircle className="mx-auto h-10 w-10 mb-2"/>
                                <p>Tidak ada data tabel yang cocok dengan kriteria Anda.</p>
                            </div>
                        )}
                    </div>
                    
                    {totalPages > 1 && (
                        <div className="mt-4 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <span className="text-sm text-gray-700">Menampilkan {currentTableData.length} dari {processedData.length} baris (Halaman {currentPage} dari {totalPages})</span>
                            <div className="flex items-center space-x-2">
                                <Button size="sm" variant="outline" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>Sebelumnya</Button>
                                <Button size="sm" variant="outline" onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>Berikutnya</Button>
                            </div>
                        </div>
                    )}
                </Card.Content>
            </Card>
        </div>
    );
};

export default Stats;