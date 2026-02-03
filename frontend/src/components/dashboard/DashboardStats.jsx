import React from 'react';
import Card from '../ui/Card';
import {
    Clock,
    Database,
    FileText,
    BarChart2,
    PieChart,
    TrendingUp,
    DollarSign,
    AlertCircle
} from 'lucide-react';

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

const ChartCard = ({ title, icon: Icon, children }) => (
    <Card>
        <Card.Header className="p-4 border-b flex items-center">
            <Icon className="h-5 w-5 text-brand-blue mr-3 flex-shrink-0" />
            <Card.Title>{title}</Card.Title>
        </Card.Header>
        <Card.Content className="p-4">
            {children}
        </Card.Content>
    </Card>
);

const DashboardStats = ({ data, isFiltering }) => {

    const renderEmptyChart = (title) => (
        <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center p-4 bg-gray-50 rounded-lg">
            <BarChart2 className="w-12 h-12 text-gray-300 mb-4" />
            <h4 className="font-semibold text-gray-600">{title}</h4>
            <p className="text-sm text-gray-400">Data tidak tersedia untuk analisis ini.</p>
        </div>
    );

    const onTooltipRender = (args) => {
        if (args.point && typeof args.point.y === 'number') {
            const value = args.point.y.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
            args.text = `<b>${args.point.x}</b><br/>Nilai: <b>Rp ${value}</b>`;
        }
    };

    const onAxisLabelRender = (args) => {
        if (args.axis.name === 'primaryYAxis') {
            const value = Number(args.value);
            args.text = value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card shadow="subtle" className="p-4 flex items-center space-x-4">
                    <div className="p-3 bg-brand-blue/10 rounded-full">
                        <Clock className="h-6 w-6 text-brand-blue" />
                    </div>
                    <div>
                        <p className="text-sm text-text-secondary">Analisis Terakhir</p>
                        <p className="text-lg font-bold text-text-primary">
                            {data?.last_updated ? new Date(data.last_updated).toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' }) : 'N/A'}
                        </p>
                    </div>
                </Card>
                <Card shadow="subtle" className="p-4 flex items-center space-x-4">
                    <div className="p-3 bg-brand-green/10 rounded-full">
                        <Database className="h-6 w-6 text-brand-green" />
                    </div>
                    <div>
                        <p className="text-sm text-text-secondary">Status Data</p>
                        <p className="text-lg font-bold text-text-primary">
                            {data?.is_temporary ? "Pratinjau (Belum Disimpan)" : "Tersimpan di Riwayat"}
                        </p>
                    </div>
                </Card>
            </div>

            <Card shadow="subtle">
                <Card.Header className="p-4 border-b flex items-center">
                    <FileText className="h-5 w-5 text-brand-blue mr-3" />
                    <Card.Title>Analisa Rangkuman</Card.Title>
                </Card.Header>
                <Card.Content className="p-6">
                    <div
                        className="prose max-w-none prose-li:my-2 prose-strong:text-text-primary prose-strong:font-semibold whitespace-pre-line"
                        dangerouslySetInnerHTML={{ __html: data?.summary_text || '<p class="text-gray-500">Tidak ada rangkuman yang dihasilkan.</p>' }}
                    />
                </Card.Content>
            </Card>

            <div className="relative">
                {isFiltering && (
                    <div className="absolute inset-0 bg-white/70 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-blue"></div>
                    </div>
                )}
                
                <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 transition-opacity duration-300 ${isFiltering ? 'opacity-50' : 'opacity-100'}`}>
                    
                    <ChartCard title="Distribusi Kondisi Aset" icon={PieChart}>
                        {data?.chart_data?.kondisi?.length > 0 ? (
                            <AccumulationChartComponent id="pie-kondisi" legendSettings={{ visible: true, position: 'Bottom' }} tooltip={{ enable: true, format: '${point.x}: <b>${point.y} unit</b>' }} palettes={chartPalettes}>
                                <Inject services={[PieSeries, AccumulationDataLabel, AccumulationTooltip, AccumulationLegend]} />
                                <AccumulationSeriesCollectionDirective>
                                    <AccumulationSeriesDirective dataSource={data.chart_data.kondisi} xName="x" yName="y" innerRadius="40%" dataLabel={{ visible: true, name: 'text', position: 'Inside', font: { fontWeight: '600', color: '#fff' } }} />
                                </AccumulationSeriesCollectionDirective>
                            </AccumulationChartComponent>
                        ) : renderEmptyChart("Distribusi Kondisi Aset")}
                    </ChartCard>

                    <ChartCard title="Distribusi Hasil Inventaris" icon={PieChart}>
                        {data?.chart_data?.hasilInventory?.length > 0 ? (
                            <AccumulationChartComponent id="pie-hasil-inv" legendSettings={{ visible: true, position: 'Bottom' }} tooltip={{ enable: true, format: '${point.x}: <b>${point.y} unit</b>' }} palettes={chartPalettes}>
                                <Inject services={[PieSeries, AccumulationDataLabel, AccumulationTooltip, AccumulationLegend]} />
                                <AccumulationSeriesCollectionDirective>
                                    <AccumulationSeriesDirective dataSource={data.chart_data.hasilInventory} xName="x" yName="y" innerRadius="40%" dataLabel={{ visible: true, name: 'text', position: 'Inside', font: { fontWeight: '600', color: '#fff' } }} />
                                </AccumulationSeriesCollectionDirective>
                            </AccumulationChartComponent>
                        ) : renderEmptyChart("Distribusi Hasil Inventaris")}
                    </ChartCard>

                    <ChartCard title="Total Nilai Aset per Lokasi (Top 10)" icon={DollarSign}>
                        {data?.chart_data?.assetValue?.length > 0 ? (
                            <ChartComponent id="bar-nilai-aset" primaryXAxis={{ valueType: 'Category', majorGridLines: { width: 0 }, labelRotation: -45, labelIntersectAction: 'Rotate45' }} primaryYAxis={{ title: 'Nilai Aset (Rp)', edgeLabelPlacement: 'Shift' }} tooltipRender={onTooltipRender} tooltip={{ enable: true }} palettes={chartPalettes} axisLabelRender={onAxisLabelRender}>
                                <Inject services={[BarSeries, Legend, Tooltip, DataLabel, Category]} />
                                <SeriesCollectionDirective>
                                    <SeriesDirective dataSource={data.chart_data.assetValue} xName="x" yName="y" type="Bar" name="Nilai Aset" />
                                </SeriesCollectionDirective>
                            </ChartComponent>
                        ) : renderEmptyChart("Total Nilai Aset per Lokasi")}
                    </ChartCard>

                    <ChartCard title="Tren Inventaris Bulanan" icon={TrendingUp}>
                        {data?.chart_data?.trenInventory?.length > 0 ? (
                            <ChartComponent id="line-tren" primaryXAxis={{ valueType: 'Category', labelRotation: -45, labelIntersectAction: 'Rotate45' }} primaryYAxis={{ title: 'Jumlah Aset Diinventaris', minimum: 0 }} tooltip={{ enable: true, format: '${point.x}: <b>${point.y}</b>' }} palettes={chartPalettes}>
                                <Inject services={[LineSeries, Legend, Tooltip, DataLabel, Category]} />
                                <SeriesCollectionDirective>
                                    <SeriesDirective dataSource={data.chart_data.trenInventory} xName="x" yName="y" type="Line" name="Jumlah" marker={{ visible: true, width: 10, height: 10 }} />
                                </SeriesCollectionDirective>
                            </ChartComponent>
                        ) : renderEmptyChart("Tren Inventaris Bulanan")}
                    </ChartCard>
                </div>
            </div>
        </div>
    );
};

export default DashboardStats;