import clsx from 'clsx';
import type { ComparatorDelta } from '../../types';

interface BaselineComparatorProps {
  deltas: ComparatorDelta[];
  baselineId: string;
  currentId: string;
}

export function BaselineComparator({ deltas, baselineId, currentId }: BaselineComparatorProps) {
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
        <h3 className="text-lg font-bold text-white">Baseline vs Current</h3>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center">
            <span className="text-ng-text-muted mr-2">Baseline:</span>
            <span className="font-mono text-white bg-black/20 px-2 py-1 rounded">{baselineId}</span>
          </div>
          <div className="text-ng-text-muted">vs</div>
          <div className="flex items-center">
            <span className="text-ng-text-muted mr-2">Current:</span>
            <span className="font-mono text-white bg-black/20 px-2 py-1 rounded">{currentId}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {deltas.map((delta, idx) => (
          <div key={idx} className="bg-black/20 border border-white/5 rounded p-4 flex flex-col justify-between">
            <div className="text-sm text-ng-text-secondary mb-3">{delta.metric}</div>
            <div className="flex items-end justify-between">
              <div className="space-y-1">
                <div className="text-xs text-ng-text-muted">Prev: {delta.baselineValue}</div>
                <div className="text-lg font-bold text-white">{delta.currentValue}</div>
              </div>
              <div
                className={clsx(
                  "text-sm font-bold px-2 py-1 rounded",
                  delta.deltaType === 'positive' && "bg-status-pass/10 text-status-pass",
                  delta.deltaType === 'negative' && "bg-status-fail/10 text-status-fail",
                  delta.deltaType === 'neutral' && "bg-white/5 text-ng-text-secondary"
                )}
              >
                {delta.delta}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
