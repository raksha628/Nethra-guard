import { SectionHeader } from '../../components/ui/SectionHeader';
import { ReportSummaryCard } from '../../components/reports/ReportSummaryCard';
import { ReportContentChecklist } from '../../components/reports/ReportContentChecklist';
import { ReportPreviewTabs } from '../../components/reports/ReportPreviewTabs';
import { ReportJsonExportPanel } from '../../components/reports/ReportJsonExportPanel';
import { ReportHistoryTable } from '../../components/reports/ReportHistoryTable';
import { generateDemoReport, demoReportHistory } from '../../services/demoReports';
import { FileJson } from 'lucide-react';

export function Reports() {
  const report = generateDemoReport();

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <SectionHeader 
          title="Reports"
          description="Export reproducible assurance results and supporting evidence."
        />
        <button className="flex items-center self-start px-4 py-2 bg-ng-accent hover:bg-ng-accent-hover text-white text-sm font-bold rounded transition-colors shadow-lg shadow-ng-accent/20">
          <FileJson className="w-4 h-4 mr-2" />
          Generate JSON Report
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-6">
          <ReportSummaryCard summary={report.metadata} />
          
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-white mb-2">Report Content Preview</h2>
            <ReportPreviewTabs report={report} />
          </div>

          <div className="space-y-4 pt-6">
            <h2 className="text-lg font-bold text-white mb-2">Report History</h2>
            <ReportHistoryTable history={demoReportHistory} />
          </div>
        </div>

        <div className="xl:col-span-1 space-y-6">
          <div className="sticky top-6 space-y-6">
            <ReportContentChecklist />
            <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
              <ReportJsonExportPanel report={report} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
