import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../hooks/useAuth';
import { useMcp } from '../contexts/McpProvider';
import { getAuth, getIdToken } from "firebase/auth";
import { AlertCircle } from 'lucide-react';
import Card from '../components/ui/Card';
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
    const [sheetName, setSheetName] = useState('');
    const [availableSheets, setAvailableSheets] = useState([]);
    
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
            const [sheetsResult, dashboardResult] = await Promise.all([
                mcpService.call('tools/call', { name: 'get_sheet_names', arguments: {} }),
                mcpService.call('tools/call', { name: 'get_dashboard_data', arguments: { area: selectedArea } })
            ]);
            
            setAvailableSheets(sheetsResult.content);
            const dashboardData = dashboardResult.content;
            
            if (!dashboardData.data_available) {
                throw new Error(dashboardData.message || "Belum ada data untuk ditampilkan.");
            }
            setData(dashboardData);
            if(dashboardData.available_areas) {
                setAvailableAreas(['Semua Area', ...dashboardData.available_areas.filter(a => a !== 'Semua Area')]);
            }

            if (isRefresh) {
                // showToast('Data berhasil diperbarui!', 'success');
            }
        } catch (err) {
            setData(null);
            setError(err.message);
            showToast(err.message, 'error');
        } finally {
            if (isInitialLoad.current || isRefresh) setLoading(false); else setIsFiltering(false);
            if (isInitialLoad.current) isInitialLoad.current = false;
        }
    }, [selectedArea, mcpService, mcpStatus, showToast]);

    const refreshData = useCallback(() => fetchData(true), [fetchData]);

    const { user } = useAuth();
    const analysis = useAnalysis(data, refreshData, user); 
    const { analysisResult, resetAnalysisResult, analysisCompletedTimestamp, resetAnalysisCompletedTimestamp } = analysis;

    const navigate = useNavigate();
    
    useEffect(() => {
        if (mcpStatus === 'connected') {
            fetchData(false);
        }
    }, [selectedArea, mcpStatus]);

    useEffect(() => {
        if (analysisCompletedTimestamp) {
            console.log("Analysis completed signal received in Home.jsx, refreshing...");
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

    const filters = { selectedArea, setSelectedArea, availableAreas, sheetName, setSheetName, availableSheets };

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

            {error || !data ? (
                <Card className="p-8 text-center bg-red-50 border-red-200">
                    <AlertCircle className="h-16 w-16 text-brand-red mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">Gagal Memuat Data Dashboard</h2>
                    <p className="text-gray-600">{error}</p>
                </Card>
            ) : (
                <DashboardStats data={data} isFiltering={isFiltering} />
            )}
        </div>
    );
};

export default Home;