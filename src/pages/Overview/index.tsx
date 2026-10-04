import { useState, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { MetricCard } from '../../components/ui/MetricCard';
import { EmptyState } from '../../components/ui/EmptyState';
import { CheckCard } from '../../components/dashboard/CheckCard';
import { BaselineComparator } from '../../components/dashboard/BaselineComparator';
import { FindingsTable } from '../../components/dashboard/FindingsTable';
import { RunTimeline } from '../../components/dashboard/RunTimeline';
import { EvidenceCard } from '../../components/dashboard/EvidenceCard';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { Download } from 'lucide-react';
import { api } from '../../services/api';
import type { CheckStatus, Finding, TimelineEvent, EvidenceSample } from '../../types';

export function Overview() {
  const [hasData, setHasData] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  // States for real data
  const [runSummary, setRunSummary] = useState<any>(null);
  const [checkStatuses, setCheckStatuses] = useState<CheckStatus[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [evidence] = useState<EvidenceSample[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const runs = await api.getRuns();
        if (runs && runs.length > 0) {
          const latestRun = runs[0];
          setHasData(true);
          
          setRunSummary({
            id: latestRun.id,
            baselineId: 'N/A',
            timestamp: latestRun.created_at || new Date().toISOString(),
            duration: '0s',
            status: latestRun.state === 'COMPLETED' ? 'PASS' : 'FAIL',
            environment: 'Local',
            workspaceName: latestRun.workspace_id
          });

          // Fetch findings
          const rawFindings = await api.getFindings(latestRun.id);
          const mappedFindings = rawFindings.map((r: any) => ({
            id: r.id,
            category: r.category,
            severity: r.severity,
            status: r.status,
            metric: r.title,
            observed: String(r.observed_value),
            threshold: String(r.threshold),
            artifact: r.affected_asset
          }));
          setFindings(mappedFindings);

          // Build check statuses from findings
          setCheckStatuses([
            { id: 'c1', name: 'Data Integrity', status: mappedFindings.some((f: any) => f.category === 'DATA_INTEGRITY' && f.severity === 'CRITICAL') ? 'FAIL' : 'PASS', explanation: 'Dataset structure checked' },
            { id: 'c2', name: 'Model Integrity', status: mappedFindings.some((f: any) => f.category === 'MODEL_INTEGRITY' && f.severity === 'CRITICAL') ? 'FAIL' : 'PASS', explanation: 'Model hash checked' },
            { id: 'c3', name: 'Distribution Shift', status: mappedFindings.some((f: any) => f.category === 'DISTRIBUTION_SHIFT' && f.severity === 'CRITICAL') ? 'FAIL' : 'PASS', explanation: 'Features compared' }
          ]);

          // Timeline mock for real run
          setTimeline([
            { id: '1', label: 'Run Started', timestamp: latestRun.created_at, status: 'COMPLETED' },
            { id: '2', label: 'Completed', timestamp: latestRun.created_at, status: 'COMPLETED' }
          ]);

        } else {
          setHasData(false);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      alert('Mock JSON Report Exported Successfully!');
      setIsExporting(false);
    }, 1000);
  };

  if (isLoading) {
    return <div className="h-full flex items-center justify-center text-white">Loading Overview...</div>;
  }

  if (!hasData || !runSummary) {
    return (
      <div className="h-full flex items-center justify-center">
        <EmptyState 
          title="Your assurance workspace is ready."
          description="Load a dataset and model to begin your first assurance run."
          primaryAction={{ label: 'Load Demo Workspace', onClick: () => setHasData(true) }}
          secondaryAction={{ label: 'Configure Workspace', onClick: () => {} }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-[1600px] pb-12">
      <SectionHeader 
        title="Assurance Overview"
        description="Monitor dataset, model, inference, distribution and provenance assurance."
      >
        <button 
          onClick={handleExport}
          disabled={isExporting}
          className="flex items-center px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded transition-colors border border-white/10 disabled:opacity-50"
        >
          <Download className="w-4 h-4 mr-2" />
          {isExporting ? 'Exporting...' : 'Export JSON Report'}
        </button>
      </SectionHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col justify-between">
          <div className="text-sm font-medium text-ng-text-secondary tracking-wide mb-4">Overall Assurance</div>
          <div>
            <div className="mb-2"><StatusBadge status={runSummary.status} className="text-sm px-3 py-1.5" /></div>
            <div className="text-xs text-status-warning font-medium">Auto-derived from latest run</div>
          </div>
        </div>

        <MetricCard 
          title="Checks Passed" 
          value={`${checkStatuses.filter(c => c.status === 'PASS').length} / ${checkStatuses.length}`} 
          trend={{ value: 'Real Data', direction: 'neutral' }}
        />

        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col justify-between">
          <div className="text-sm font-medium text-ng-text-secondary tracking-wide mb-4">Findings</div>
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-white tracking-tight">{findings.length}</div>
            <div className="flex space-x-3 text-xs font-medium">
              <div className="text-status-fail flex flex-col items-center"><span>{findings.filter(f => f.severity === 'CRITICAL').length}</span><span className="text-[10px] text-ng-text-muted uppercase">Crit</span></div>
            </div>
          </div>
        </div>

        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col justify-between">
          <div className="text-sm font-medium text-ng-text-secondary tracking-wide mb-4">Latest Run</div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="font-mono text-white text-lg truncate w-32">{runSummary.id}</div>
              <div className="text-xs font-mono text-ng-text-muted">{runSummary.duration}</div>
            </div>
            <div className="text-xs text-ng-text-muted">{runSummary.timestamp}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-8">
          <div>
            <h2 className="text-lg font-bold text-white mb-4">Assurance Checks</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {checkStatuses.map(check => (
                <CheckCard key={check.id} check={check} />
              ))}
            </div>
          </div>

          <BaselineComparator 
            deltas={[]} 
            baselineId={runSummary.baselineId}
            currentId={runSummary.id}
          />

          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">Active Findings</h2>
              <button className="text-sm text-ng-accent hover:text-ng-accent-hover transition-colors">View all</button>
            </div>
            <FindingsTable findings={findings} />
          </div>
          
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">Sample Evidence</h2>
              <button className="text-sm text-ng-accent hover:text-ng-accent-hover transition-colors">View gallery</button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {evidence.map(e => (
                <EvidenceCard key={e.id} evidence={e as any} />
              ))}
            </div>
          </div>
        </div>

        <div className="xl:col-span-1">
          <div className="sticky top-6">
            <RunTimeline events={timeline} />
          </div>
        </div>
      </div>
    </div>
  );
}
