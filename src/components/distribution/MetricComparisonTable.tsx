import clsx from 'clsx';
import type { ShiftMetricRecord } from '../../types';

export function MetricComparisonTable({ metrics }: { metrics: ShiftMetricRecord[] }) {
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-black/40 border-b border-white/5 uppercase text-[10px] font-bold text-ng-text-muted tracking-wider">
          <tr>
            <th className="px-6 py-4">Metric</th>
            <th className="px-6 py-4">Reference Batch</th>
            <th className="px-6 py-4">Current Batch</th>
            <th className="px-6 py-4">Absolute Delta</th>
            <th className="px-6 py-4">Unit</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {metrics.map((m, idx) => {
            const isSignificant = Math.abs(m.delta) > (m.referenceValue * 0.1); // Simple arbitrary visual threshold for demo highlighting
            return (
              <tr key={idx} className="hover:bg-white/5 transition-colors">
                <td className="px-6 py-4 text-white font-medium">{m.metricName}</td>
                <td className="px-6 py-4 font-mono text-ng-text-secondary">{m.referenceValue.toFixed(3)}</td>
                <td className="px-6 py-4 font-mono text-white">{m.currentValue.toFixed(3)}</td>
                <td className="px-6 py-4">
                  <span className={clsx(
                    "font-mono px-2 py-1 rounded text-xs",
                    isSignificant ? "bg-status-warning/10 text-status-warning font-bold" : "text-ng-text-secondary"
                  )}>
                    {m.delta > 0 ? '+' : ''}{m.delta.toFixed(3)}
                  </span>
                </td>
                <td className="px-6 py-4 text-ng-text-muted text-xs">{m.unit}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
