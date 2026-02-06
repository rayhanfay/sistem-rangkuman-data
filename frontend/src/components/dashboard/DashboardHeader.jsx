import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import {
    Zap, RefreshCw, Save, Download, ChevronDown, MapPin, Sheet, Settings,
    Search, BarChart2, TrendingDown, BrainCircuit, ClipboardList
} from 'lucide-react';

const formatSheetName = (name) => {
    if (typeof name !== 'string' || !name) return '';
    
    if (name === 'MASTER-SHEET') return 'MASTER-SHEET (Pusat)';

    // Pola untuk CYCLE-X-YEAR-YYYY
    const cycleMatch = name.match(/CYCLE-(\d)-YEAR-(\d{4})/);
    if (cycleMatch) {
        const cycleNum = cycleMatch[1];
        const year = cycleMatch[2];
        const cycleDetails = {
            '1': 'Januari - April',
            '2': 'Mei - Agustus',
            '3': 'September - Desember',
        };
        return `Siklus ${cycleNum} Tahun ${year} (${cycleDetails[cycleNum] || ''})`;
    }

    return name;
};

const DashboardHeader = ({
    filters,
    analysis,
    dashboardData,
    onRefresh
}) => {
    const { 
        selectedArea, setSelectedArea, availableAreas, 
        sheetName, setSheetName, availableSheets 
    } = filters;

    const {
        isAnalyzing, isSaving, isDownloadOpen, setIsDownloadOpen,
        analysisOptions, setAnalysisOptions,
        handleTriggerAnalysis, handleSaveAnalysis, handleDownload
    } = analysis;

    const onOptionChange = (optionKey) => {
        setAnalysisOptions(prevOptions => ({
            ...prevOptions,
            [optionKey]: !prevOptions[optionKey]
        }));
    };

    const handleSheetSelectChange = (e) => {
        setSheetName(e.target.value);
    };

    const onStartAnalysis = () => {
        const selection = (sheetName && sheetName.includes('|')) 
            ? sheetName 
            : "master|MASTER-SHEET";
            
        const [source, name] = selection.split('|');
        handleTriggerAnalysis(name, source);
    };

    return (
        <div className="flex flex-col md:flex-row justify-between items-start gap-4">
            <div>
                <h1 className="text-3xl font-bold text-text-primary">Dashboard</h1>
                <p className="text-text-secondary mt-1">Ringkasan otomatis dari data aset terintegrasi.</p>
            </div>

            <div className="w-full md:w-auto flex flex-col items-start md:items-end gap-3">
                <Card shadow="subtle" padding="p-3" className="w-full">
                    <div className="flex flex-col md:flex-row flex-wrap items-start md:items-center gap-4">
                        <div className="flex items-center gap-2 w-full md:w-auto flex-grow">
                            <label htmlFor="sheet-filter" className="text-sm font-medium text-text-secondary flex items-center gap-2 whitespace-nowrap">
                                <Sheet size={16} /> Data Sumber:
                            </label>
                            <select 
                                id="sheet-filter" 
                                value={sheetName} 
                                onChange={handleSheetSelectChange} 
                                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-brand-blue focus:border-brand-blue block w-full p-2" 
                                disabled={isAnalyzing}
                            >
                                {/* PERBAIKAN: Cek apakah data master ada sebelum mapping */}
                                <optgroup label="Data Pusat (Master)">
                                    {Array.isArray(availableSheets?.master) && availableSheets.master
                                        // FILTER: Jangan tampilkan sheet 'backup' (abaikan huruf besar/kecil)
                                        .filter(name => name.toLowerCase() !== 'backup')
                                        .map(name => (
                                            <option key={`master-${name}`} value={`master|${name}`}>
                                                {name === 'MASTER-SHEET' ? 'MASTER-SHEET (Utama)' : name}
                                            </option>
                                        ))
                                    }
                                </optgroup>

                                {/* PERBAIKAN: Cek apakah data siklus ada sebelum mapping */}
                                <optgroup label="Data Lapangan (Siklus)">
                                    {Array.isArray(availableSheets?.siklus) && availableSheets.siklus.map(name => (
                                        <option key={`siklus-${name}`} value={`siklus|${name}`}>
                                            {formatSheetName(name)}
                                        </option>
                                    ))}
                                </optgroup>
                            </select>
                        </div>

                        <div className="flex items-center gap-2 w-full md:w-auto flex-grow">
                            <label htmlFor="area-filter" className="text-sm font-medium text-text-secondary flex items-center gap-2 whitespace-nowrap">
                                <MapPin size={16} /> Area:
                            </label>
                            <select 
                                id="area-filter" 
                                value={selectedArea} 
                                onChange={(e) => setSelectedArea(e.target.value)} 
                                className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-brand-blue focus:border-brand-blue block w-full p-2" 
                                disabled={isAnalyzing}
                            >
                                {availableAreas.map(area => (
                                    <option key={area} value={area}>{area}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </Card>

                <Card shadow="subtle" padding="p-4" className="w-full">
                    <div className="flex items-start gap-4">
                        <Settings className="w-5 h-5 text-text-secondary flex-shrink-0 mt-1" />
                        <div className="w-full space-y-4">
                            <div>
                                <h4 className="font-semibold text-text-primary mb-2">Analisis Kuantitatif</h4>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2">
                                    <label className="flex items-center space-x-2 cursor-pointer text-sm text-text-secondary hover:text-text-primary">
                                        <input type="checkbox" checked={analysisOptions.data_overview} onChange={() => onOptionChange('data_overview')} className="form-checkbox h-4 w-4 text-brand-blue rounded" />
                                        <ClipboardList className="w-4 h-4" /><span>Data Overview</span>
                                    </label>
                                    <label className="flex items-center space-x-2 cursor-pointer text-sm text-text-secondary hover:text-text-primary">
                                        <input type="checkbox" checked={analysisOptions.check_duplicates} onChange={() => onOptionChange('check_duplicates')} className="form-checkbox h-4 w-4 text-brand-blue rounded" />
                                        <Search className="w-4 h-4" /><span>Cek Duplikasi Data</span>
                                    </label>
                                    <label className="flex items-center space-x-2 cursor-pointer text-sm text-text-secondary hover:text-text-primary">
                                        <input type="checkbox" checked={analysisOptions.insight} onChange={() => onOptionChange('insight')} className="form-checkbox h-4 w-4 text-brand-blue rounded" />
                                        <BarChart2 className="w-4 h-4" /><span>Insight Kondisi Aset</span>
                                    </label>
                                    <label className="flex items-center space-x-2 cursor-pointer text-sm text-text-secondary hover:text-text-primary">
                                        <input type="checkbox" checked={analysisOptions.financial_analysis} onChange={() => onOptionChange('financial_analysis')} className="form-checkbox h-4 w-4 text-brand-blue rounded" />
                                        <TrendingDown className="w-4 h-4" /><span>Rangkuman Nilai Aset</span>
                                    </label>
                                </div>
                            </div>
                            <hr />
                            <div>
                                <h4 className="font-semibold text-text-primary mb-2">Analisis Berbasis AI</h4>
                                <div className="flex flex-col gap-y-2">
                                     <label className="flex items-center space-x-2 cursor-pointer text-sm text-text-secondary hover:text-text-primary">
                                        <input type="checkbox" checked={analysisOptions.summarize} onChange={() => onOptionChange('summarize')} className="form-checkbox h-4 w-4 text-brand-blue rounded" />
                                        <BrainCircuit className="w-4 h-4" /><span>Ringkasan Eksekutif (AI)</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </Card>
                
                <div className="flex flex-col sm:flex-row sm:flex-wrap justify-start md:justify-end gap-2 w-full">
                    <Button onClick={onStartAnalysis} disabled={isAnalyzing} loading={isAnalyzing} className="w-full sm:w-auto">
                        <Zap className="mr-2" size={16} />{isAnalyzing ? 'Menganalisis...' : 'Mulai Analisis'}
                    </Button>
                    <Button onClick={onRefresh} variant="outline" disabled={isAnalyzing || isSaving} className="w-full sm:w-auto">
                        <RefreshCw className="mr-2" size={16} />Refresh
                    </Button>
                    <Button onClick={handleSaveAnalysis} disabled={isSaving || isAnalyzing || !dashboardData?.is_temporary} loading={isSaving} variant="success" className="w-full sm:w-auto">
                        <Save className="mr-2" size={16} />{isSaving ? 'Menyimpan...' : 'Simpan'}
                    </Button>
                    <div className="relative w-full sm:w-auto">
                        <Button onClick={() => setIsDownloadOpen(!isDownloadOpen)} variant="secondary" disabled={isAnalyzing || !dashboardData?.data_available} className="flex items-center w-full justify-center">
                            <Download className="mr-2" size={16} /> Unduh Data <ChevronDown size={16} className={`ml-1 transition-transform ${isDownloadOpen ? 'rotate-180' : ''}`} />
                        </Button>
                        {isDownloadOpen && (
                            <div className="absolute right-0 mt-2 w-full sm:w-48 bg-white rounded-md shadow-lg z-20 border border-gray-200 py-1">
                                <button onClick={() => handleDownload('csv')} className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Unduh sebagai CSV</button>
                                <button onClick={() => handleDownload('xlsx')} className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Unduh sebagai XLSX</button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardHeader;