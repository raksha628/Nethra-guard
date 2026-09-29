import { PlusCircle, MinusCircle, AlertCircle, ArrowRight } from 'lucide-react';
import type { FindingChange } from '../../types';
import clsx from 'clsx';

interface FindingListProps {
  findings: FindingChange[];
  icon: React.ReactNode;
  title: string;
  emptyText: string;
}

function FindingList({ findings, icon, title, emptyText }: FindingListProps) {
  if (findings.length === 0) {
    return (
      <div className="bg-black/20 rounded-lg p-6 text-center border border-white/5">
        <p className="text-sm text-ng-text-muted">{emptyText}</p>
      </div>
    );
  }

  return (
    <div className="bg-black/20 rounded-lg border border-white/5 overflow-hidden">
      <div className="bg-black/40 px-4 py-3 border-b border-white/5 flex items-center">
        {icon}
        <h4 className="text-xs font-bold text-white uppercase tracking-wider ml-2">{title} ({findings.length})</h4>
      </div>
      <div className="divide-y divide-white/5">
        {findings.map(f => (
          <div key={f.findingId} className="p-4 hover:bg-white/5 transition-colors">
            <div className="flex items-start justify-between mb-2">
              <div className="font-mono text-white text-xs">{f.findingId}</div>
              <div className="text-[10px] font-bold text-ng-text-muted uppercase tracking-wider border border-white/10 px-2 py-0.5 rounded">
                {f.category}
              </div>
            </div>
            <div className="text-sm text-ng-text-secondary">{f.description}</div>
            
            {f.type === 'STATUS_CHANGE' && f.baselineStatus && f.currentStatus && (
              <div className="flex items-center space-x-2 mt-3 text-xs">
                <span className="font-mono text-ng-text-muted bg-white/5 px-2 py-1 rounded">{f.baselineStatus}</span>
                <ArrowRight className="w-3 h-3 text-ng-text-muted" />
                <span className={clsx(
                  "font-mono px-2 py-1 rounded",
                  f.currentStatus === 'Cleared' || f.currentStatus === 'Reviewed' ? 'text-status-pass bg-status-pass/10' : 'text-status-warning bg-status-warning/10'
                )}>
                  {f.currentStatus}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function FindingChanges({ changes }: { changes: FindingChange[] }) {
  const newFindings = changes.filter(c => c.type === 'NEW');
  const clearedFindings = changes.filter(c => c.type === 'CLEARED');
  const unchangedFindings = changes.filter(c => c.type === 'UNCHANGED' || c.type === 'STATUS_CHANGE');

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <FindingList 
        findings={newFindings} 
        icon={<PlusCircle className="w-4 h-4 text-status-fail" />} 
        title="New Findings" 
        emptyText="No new findings in the current run."
      />
      <FindingList 
        findings={clearedFindings} 
        icon={<MinusCircle className="w-4 h-4 text-status-pass" />} 
        title="Cleared Findings" 
        emptyText="No findings were cleared in the current run."
      />
      <FindingList 
        findings={unchangedFindings} 
        icon={<AlertCircle className="w-4 h-4 text-status-warning" />} 
        title="Unchanged / Updated" 
        emptyText="No findings carried over from baseline."
      />
    </div>
  );
}
