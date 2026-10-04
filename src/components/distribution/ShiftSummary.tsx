import { AlertTriangle, CheckCircle2, XCircle, MinusCircle } from 'lucide-react';
import type { DistributionContext, ShiftStatus } from '../../types';
import clsx from 'clsx';

export function ShiftSummary({ context }: { context: DistributionContext }) {
  
  const getStatusColor = (status: ShiftStatus) => {
    switch (status) {
      case 'PASS': return 'text-status-pass border-status-pass/20 bg-status-pass/10';
      case 'WARNING': return 'text-status-warning border-status-warning/20 bg-status-warning/10';
      case 'FAIL': return 'text-status-fail border-status-fail/20 bg-status-fail/10';
      case 'NOT RUN': return 'text-ng-text-muted border-white/10 bg-white/5';
    }
  };

  const getStatusIcon = (status: ShiftStatus) => {
    switch (status) {
      case 'PASS': return <CheckCircle2 className="w-6 h-6 mr-2" />;
      case 'WARNING': return <AlertTriangle className="w-6 h-6 mr-2" />;
      case 'FAIL': return <XCircle className="w-6 h-6 mr-2" />;
      case 'NOT RUN': return <MinusCircle className="w-6 h-6 mr-2" />;
    }
  };

  const explanation = context.alertLevel === 'WARNING' || context.alertLevel === 'FAIL'
    ? "Distribution Shift identifies measurable differences between reference and evaluation data. SHIFT \u2192 POTENTIAL ASSURANCE CONCERN \u2192 INVESTIGATE. It does not automatically mean the model is broken."
    : context.alertLevel === 'PASS'
    ? "Current batch distribution aligns with reference baseline."
    : "Comparison was not executed.";

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6 space-y-6">
      
      <div className={clsx("flex items-center p-4 rounded-lg border", getStatusColor(context.alertLevel))}>
        {getStatusIcon(context.alertLevel)}
        <div>
          <h2 className="text-lg font-bold uppercase tracking-wider">{context.alertLevel}</h2>
          <p className="text-sm opacity-90">{explanation}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-black/30 p-4 rounded-lg border border-white/5">
          <div className="text-xs text-ng-text-muted uppercase tracking-wider mb-1">Shift Score ({context.primaryMetric})</div>
          <div className={clsx(
            "text-2xl font-mono font-bold",
            context.observedScore > context.threshold ? "text-status-warning" : "text-white"
          )}>
            {context.observedScore.toFixed(3)}
          </div>
        </div>
        <div className="bg-black/30 p-4 rounded-lg border border-white/5">
          <div className="text-xs text-ng-text-muted uppercase tracking-wider mb-1">Assessment Threshold</div>
          <div className="text-2xl font-mono text-white font-bold">{context.threshold.toFixed(3)}</div>
        </div>
      </div>

      <div className="space-y-3 pt-4 border-t border-white/5">
        <div className="flex justify-between text-sm">
          <span className="text-ng-text-secondary">Reference Batch</span>
          <span className="text-white font-mono">{context.referenceBatch}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-ng-text-secondary">Current Batch</span>
          <span className="text-white font-mono">{context.currentBatch}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-ng-text-secondary">Run ID</span>
          <span className="text-white font-mono">{context.runId}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-ng-text-secondary">Method</span>
          <span className="text-white text-right max-w-[200px]">{context.method}</span>
        </div>
      </div>

      <div className="text-[10px] text-status-warning/80 italic mt-4">
        Thresholds shown here are prototype demonstration values and are not universal deployment thresholds.
      </div>
    </div>
  );
}
