import { useState, useEffect, useCallback } from 'react';
import { useMcp } from '../contexts/McpProvider';
import { useToast } from '../contexts/ToastContext';
import apiService from '../services/api';

export const useAnalysis = (dashboardData, refreshData, user) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isDownloadOpen, setIsDownloadOpen] = useState(false);
    
    const [analysisCompletedTimestamp, setAnalysisCompletedTimestamp] = useState(null);
    
    const [analysisOptions, setAnalysisOptions] = useState({
        data_overview: true,
        check_duplicates: true,
        summarize: true,
        insight: true,
        financial_analysis: true,
    });
    
    const [analysisResult, setAnalysisResult] = useState({ status: 'idle', data: null, error: null });

    const { service: mcpService, status: mcpStatus } = useMcp();
    const { showToast } = useToast();

    useEffect(() => {
        if (mcpStatus !== 'connected') return;

        const unsubscribe = mcpService.on('analysis/progress', (progress) => {
            if (progress.status === 'starting' || progress.status === 'progress') {
                showToast(progress.message, 'info');
            } 
            else if (progress.status === 'completed') {
                showToast(progress.message, 'success');
                setIsAnalyzing(false);
                setAnalysisCompletedTimestamp(Date.now());
            } 
            else if (progress.status === 'error') {
                showToast(progress.message, 'error');
                setIsAnalyzing(false);
            }
        });

        return () => unsubscribe();
        
    }, [mcpService, mcpStatus, showToast]);

    const handleTriggerAnalysis = useCallback(async (sheetName, source = 'master') => {
        if (mcpStatus !== 'connected') { 
            showToast('Koneksi ke server belum siap.', 'error');
            return;
        }
        setIsAnalyzing(true);
        try {
            mcpService.call('tools/call', { 
                name: 'trigger_analysis', 
                arguments: { 
                    ...analysisOptions, 
                    sheet_name: sheetName,
                    source: source // 'master' atau 'siklus'
                } 
            });
        } catch (err) {
            showToast(err.message || 'Gagal memulai analisis.', 'error');
            setIsAnalyzing(false); 
        }
    }, [analysisOptions, mcpService, mcpStatus, showToast]);

    const handleSaveAnalysis = useCallback(async (user, token) => {
        if (mcpStatus !== 'connected') { 
            showToast('Koneksi ke server belum siap.', 'warning'); 
            return;
        }
        if (!user || !user.email || !token) {
            showToast('Informasi otentikasi tidak lengkap, tidak dapat menyimpan.', 'error');
            return;
        }
        setIsSaving(true);
        try {
            const result = await mcpService.call('tools/call', { 
                name: 'save_analysis',
                arguments: { auth_token: token }
            });
            setAnalysisResult({ status: 'save_success', data: result.content, error: null });
        } catch (err) {
            showToast(err.message || 'Gagal menyimpan.', 'error');
        } finally {
            setIsSaving(false);
        }
    }, [mcpService, mcpStatus, showToast]); 

    const handleDownload = useCallback(async (format, filters) => {
        if (!dashboardData?.data_available) {
            showToast("Tidak ada data untuk diunduh.", "error"); 
            return;
        }

        const isTemporary = dashboardData.is_temporary;
        
        const currentSheetFromData = dashboardData.options?.sheet_name;

        const params = {
            file_format: format,
            source: isTemporary ? 'temporary' : 'history',
            timestamp: isTemporary ? null : dashboardData.timestamp,
            area: filters.selectedArea,
            sheet_name: isTemporary ? (currentSheetFromData || 'MASTER-SHEET') : null,
        };

        try {
            await apiService.downloadAnalyzedData(params);
        } catch (err) {
            showToast(`Gagal mengunduh file: ${err.message}`, "error");
        }
        setIsDownloadOpen(false);
    }, [dashboardData, showToast]);
    
    const resetAnalysisResult = useCallback(() => {
        setAnalysisResult({ status: 'idle', data: null, error: null });
    }, []);

    const resetAnalysisCompletedTimestamp = useCallback(() => {
        setAnalysisCompletedTimestamp(null);
    }, []);

    return {
        isAnalyzing, isSaving, isDownloadOpen, setIsDownloadOpen,
        analysisOptions, setAnalysisOptions,
        handleTriggerAnalysis, handleSaveAnalysis, handleDownload,
        analysisResult, resetAnalysisResult,
        analysisCompletedTimestamp,
        resetAnalysisCompletedTimestamp,
    };
};