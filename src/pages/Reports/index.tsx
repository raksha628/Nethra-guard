import { useState, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { ReportSummaryCard } from '../../components/reports/ReportSummaryCard';
import { ReportContentChecklist } from '../../components/reports/ReportContentChecklist';
import { ReportPreviewTabs } from '../../components/reports/ReportPreviewTabs';
import { ReportJsonExportPanel } from '../../components/reports/ReportJsonExportPanel';
import { ReportHistoryTable } from '../../components/reports/ReportHistoryTable';
import { api } from '../../services/api';
import { FileJson } from 'lucide-react';

export function Reports() {
  const [report, setReport] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const runs = await api.getRuns();
        if (runs && runs.length > 0) {
          const latestRun = runs[0];
          
          // Wait, I can just fetch it manually!
          const reportRaw = await fetch(`http://127.0.0.1:8000/api/runs/${latestRun.id}/report`).then(r => r.json());
          
          setReport({
            metadata: {
              runId: latestRun.id,
              timestamp: latestRun.created_at,
              status: latestRun.state === 'COMPLETED' ? 'PASS' : 'FAIL',
              overallScore: '100%',
              totalFindings: 0
            },
            raw: reportRaw
          });
          
          setHistory(runs.map((r: any) => ({
            id: r.id,
            timestamp: r.created_at,
            dataset: r.reference_dataset_asset_id,
            model: r.model_asset_id,
            status: r.state,
            reportHash: r.summary_hash || 'N/A'
          })));
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  if (isLoading) return <div className="p-8 text-white">Loading Reports...</div>;

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
          {report && <ReportSummaryCard summary={report.metadata} />}
          
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-white mb-2">Report Content Preview</h2>
            {report && <ReportPreviewTabs report={report} />}
          </div>

          <div className="space-y-4 pt-6">
            <h2 className="text-lg font-bold text-white mb-2">Report History</h2>
            <ReportHistoryTable history={history} />
          </div>
        </div>

        <div className="xl:col-span-1 space-y-6">
          <div className="sticky top-6 space-y-6">
            <ReportContentChecklist />
            <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
              {report && <ReportJsonExportPanel report={report} />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
