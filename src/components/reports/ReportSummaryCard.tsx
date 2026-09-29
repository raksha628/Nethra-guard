import { Hash, Calendar, GitCommit } from 'lucide-react';
import type { ReportSummary } from '../../types';
import clsx from 'clsx';

export function ReportSummaryCard({ summary }: { summary: ReportSummary }) {
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
      <div className="flex justify-between items-start mb-6 pb-6 border-b border-white/5">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">{summary.project}</h2>
          <div className="text-sm text-ng-text-secondary font-mono">{summary.workspace} v{summary.version}</div>
        </div>
        <div className={clsx(
          "px-3 py-1 rounded border font-bold uppercase tracking-wider text-xs",
          summary.summaryStatus === 'PASS' ? "bg-status-pass/10 border-status-pass/20 text-status-pass" :
          summary.summaryStatus === 'WARNING' ? "bg-status-warning/10 border-status-warning/20 text-status-warning" :
          "bg-status-fail/10 border-status-fail/20 text-status-fail"
        )}>
          {summary.summaryStatus}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="flex items-center text-sm">
            <GitCommit className="w-4 h-4 text-ng-text-muted mr-3" />
            <span className="text-ng-text-secondary mr-2">Run ID:</span>
            <span className="text-white font-mono font-bold">{summary.runId}</span>
          </div>
          <div className="flex items-center text-sm">
            <Calendar className="w-4 h-4 text-ng-text-muted mr-3" />
            <span className="text-ng-text-secondary mr-2">Generated:</span>
            <span className="text-white font-mono">{new Date(summary.timestamp).toLocaleString()}</span>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center text-xs">
            <Hash className="w-3 h-3 text-ng-text-muted mr-3 flex-shrink-0" />
            <span className="text-ng-text-secondary w-24">Dataset:</span>
            <span className="text-white font-mono truncate">{summary.datasetHash}</span>
          </div>
          <div className="flex items-center text-xs">
            <Hash className="w-3 h-3 text-ng-text-muted mr-3 flex-shrink-0" />
            <span className="text-ng-text-secondary w-24">Model:</span>
            <span className="text-white font-mono truncate">{summary.modelHash}</span>
          </div>
          <div className="flex items-center text-xs">
            <Hash className="w-3 h-3 text-ng-text-muted mr-3 flex-shrink-0" />
            <span className="text-ng-text-secondary w-24">Config:</span>
            <span className="text-white font-mono truncate">{summary.configHash}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
