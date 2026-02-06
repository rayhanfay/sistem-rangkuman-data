import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../hooks/useAuth';
import { useMcp } from '../contexts/McpProvider';
import { getAuth, getIdToken } from "firebase/auth";
import { AlertCircle, LayoutDashboard } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import LoadingOverlay from '../components/common/LoadingOverlay';
import { useAnalysis } from '../hooks/useAnalysis';
import DashboardHeader from '../components/dashboard/DashboardHeader';
import DashboardStats from '../components/dashboard/DashboardStats';

const Home = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isFiltering, setIsFiltering] = useState(false);
    const [error, setError] = useState('');
    const [selectedArea, setSelectedArea] = useState('Semua Area');
    const [availableAreas, setAvailableAreas] = useState(['Semua Area']);
    
    const [sheetName, setSheetName] = useState('master|MASTER-SHEET');
    
    const [availableSheets, setAvailableSheets] = useState({ master: [], siklus: [] });
    
    const { showToast } = useToast();
    const { service: mcpService, status: mcpStatus } = useMcp();
    const isInitialLoad = useRef(true);

    const fetchData = useCallback(async (isRefresh = false) => {
        if (mcpStatus !== 'connected') {
            if (isInitialLoad.current) setLoading(true);
            return;
        }

        setError('');
        if (isInitialLoad.current || isRefresh) setLoading(true); else setIsFiltering(true);

        try {
            const [masterSheetsResult, siklusSheetsResult, dashboardResult] = await Promise.all([
                mcpService.call('tools/call', { 
                    name: 'get_sheet_names', 
                    arguments: { source: 'master' } 
                }),
                mcpService.call('tools/call', { 
                    name: 'get_sheet_names', 
                    arguments: { source: 'siklus' } 
                }),
                mcpService.call('tools/call', { 
                    name: 'get_dashboard_data', 
                    arguments: { area: selectedArea } 
                })
            ]);
            
            setAvailableSheets({
                master: masterSheetsResult.content || [],
                siklus: siklusSheetsResult.content || []
            });

            const dashboardData = dashboardResult.content;
            
            if (!dashboardData.data_available) {
                console.log("Info: Belum ada data analisis yang tersedia.");
                setData(null);
            } else {
                setData(dashboardData);
                if(dashboardData.available_areas) {
                    setAvailableAreas(['Semua Area', ...dashboardData.available_areas.filter(a => a !== 'Semua Area')]);
                }
            }

        } catch (err) {
            console.error("Fetch Error:", err);
            setError(err.message);
        } finally {
            if (isInitialLoad.current || isRefresh) setLoading(false); else setIsFiltering(false);
            if (isInitialLoad.current) isInitialLoad.current = false;
        }
    }, [selectedArea, mcpService, mcpStatus]);

    const refreshData = useCallback(() => fetchData(true), [fetchData]);

    const { user } = useAuth();
    const analysis = useAnalysis(data, refreshData, user); 
    const { analysisResult, resetAnalysisResult, analysisCompletedTimestamp, resetAnalysisCompletedTimestamp } = analysis;

    const navigate = useNavigate();
    
    useEffect(() => {
        if (mcpStatus === 'connected') {
            fetchData(false);
        }
    }, [selectedArea, mcpStatus, fetchData]);

    useEffect(() => {
        if (analysisCompletedTimestamp) {
            refreshData();
            resetAnalysisCompletedTimestamp();
        }

        if (analysisResult.status === 'save_success' && analysisResult.data) {
            showToast('Analisis berhasil disimpan!', 'success');
            navigate(`/stats?timestamp=${analysisResult.data.timestamp}`);
            resetAnalysisResult();
        }
    }, [analysisCompletedTimestamp, analysisResult, navigate, showToast, resetAnalysisResult, refreshData, resetAnalysisCompletedTimestamp]);

    if (loading) {
        return <LoadingOverlay />;
    }

    const filters = { 
        selectedArea, 
        setSelectedArea, 
        availableAreas, 
        sheetName, 
        setSheetName, 
        availableSheets 
    };

    return (
        <div className="space-y-6">
            <DashboardHeader 
                filters={filters}
                analysis={{
                    ...analysis, 
                    handleDownload: (format) => analysis.handleDownload(format, filters), 
                    handleSaveAnalysis: async () => {
                        const auth = getAuth();
                        if (auth.currentUser) {
                            const token = await getIdToken(auth.currentUser);
                            analysis.handleSaveAnalysis(user, token);
                        } else {
                            showToast("Sesi tidak valid, silakan login ulang.", "error");
                        }
                    } 
                }}
                dashboardData={data}
                onRefresh={refreshData}
            />

            {/* AREA KONTEN UTAMA */}
            {error ? (
                // Tampilan jika server error/mati
                <Card className="p-8 text-center bg-red-50 border-red-200">
                    <AlertCircle className="h-16 w-16 text-brand-red mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">Gangguan Koneksi</h2>
                    <p className="text-gray-600 mb-4">{error}</p>
                    <Button onClick={refreshData} variant="outline">Coba Muat Ulang</Button>
                </Card>
            ) : !data ? (
                // Tampilan jika data kosong (Belum ada rangkuman)
                <Card className="p-12 text-center border-dashed border-2 border-gray-300 bg-gray-50">
                    <LayoutDashboard className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-gray-700 mb-2">Belum Ada Rangkuman Aset</h2>
                    <p className="text-gray-500 max-w-md mx-auto mb-6">
                        Sistem belum mendeteksi adanya hasil analisis data. 
                        Silakan pilih sheet pada dropdown di atas dan klik <strong>"Mulai Analisis"</strong> untuk membuat rangkuman pertama Anda.
                    </p>
                    <div className="flex justify-center">
                         <div className="">
                            <Button onClick={() => window.scrollTo({top: 0, behavior: 'smooth'})} variant="primary">
                                Pilih Data Sumber Di Atas
                            </Button>
                         </div>
                    </div>
                </Card>
            ) : (
                <DashboardStats data={data} isFiltering={isFiltering} />
            )}
        </div>
    );
};

export default Home;