import { useState } from 'react';
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

import { 
  demoRunSummary, 
  demoCheckStatuses, 
  demoFindings, 
  demoTimeline, 
  demoEvidence,
  demoComparatorDeltas 
} from '../../services/demoData';

export function Overview() {
  const [hasData, setHasData] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      alert('Mock JSON Report Exported Successfully!');
      setIsExporting(false);
    }, 1000);
  };

  if (!hasData) {
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
          {isExporting ? 'Exporting...' : 'Export JSON Report (Demo)'}
        </button>
      </SectionHeader>

      {/* TOP SUMMARY CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col justify-between">
          <div className="text-sm font-medium text-ng-text-secondary tracking-wide mb-4">Overall Assurance</div>
          <div>
            <div className="mb-2"><StatusBadge status={demoRunSummary.status} className="text-sm px-3 py-1.5" /></div>
            <div className="text-xs text-status-warning font-medium">2 warnings require analyst review</div>
          </div>
        </div>

        <MetricCard 
          title="Checks Passed" 
          value="8 / 10" 
          trend={{ value: '2 Failed', direction: 'down' }}
        />

        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col justify-between">
          <div className="text-sm font-medium text-ng-text-secondary tracking-wide mb-4">Findings</div>
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-white tracking-tight">3</div>
            <div className="flex space-x-3 text-xs font-medium">
              <div className="text-status-fail flex flex-col items-center"><span>1</span><span className="text-[10px] text-ng-text-muted uppercase">Crit</span></div>
              <div className="text-status-warning flex flex-col items-center"><span>1</span><span className="text-[10px] text-ng-text-muted uppercase">Warn</span></div>
              <div className="text-ng-accent flex flex-col items-center"><span>1</span><span className="text-[10px] text-ng-text-muted uppercase">Info</span></div>
            </div>
          </div>
        </div>

        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col justify-between">
          <div className="text-sm font-medium text-ng-text-secondary tracking-wide mb-4">Latest Run</div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="font-mono text-white text-lg">{demoRunSummary.id}</div>
              <div className="text-xs font-mono text-ng-text-muted">{demoRunSummary.duration}</div>
            </div>
            <div className="text-xs text-ng-text-muted">{demoRunSummary.timestamp}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-8">
          {/* CHECK STATUS SECTION */}
          <div>
            <h2 className="text-lg font-bold text-white mb-4">Assurance Checks</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {demoCheckStatuses.map(check => (
                <CheckCard key={check.id} check={check} />
              ))}
            </div>
          </div>

          {/* BASELINE VS CURRENT */}
          <BaselineComparator 
            deltas={demoComparatorDeltas} 
            baselineId={demoRunSummary.baselineId}
            currentId={demoRunSummary.id}
          />

          {/* FINDINGS PREVIEW */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">Active Findings</h2>
              <button className="text-sm text-ng-accent hover:text-ng-accent-hover transition-colors">View all</button>
            </div>
            <FindingsTable findings={demoFindings} />
          </div>
          
          {/* SAMPLE EVIDENCE PREVIEW */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">Sample Evidence</h2>
              <button className="text-sm text-ng-accent hover:text-ng-accent-hover transition-colors">View gallery</button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {demoEvidence.map(evidence => (
                <EvidenceCard key={evidence.id} evidence={evidence} />
              ))}
            </div>
          </div>
        </div>

        {/* SIDEBAR TIMELINE */}
        <div className="xl:col-span-1">
          <div className="sticky top-6">
            <RunTimeline events={demoTimeline} />
          </div>
        </div>
      </div>
    </div>
  );
}
