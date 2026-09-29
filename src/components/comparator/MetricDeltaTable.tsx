import clsx from 'clsx';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import type { MetricDelta } from '../../types';

export function MetricDeltaTable({ deltas }: { deltas: MetricDelta[] }) {
  const getStatusIcon = (status: MetricDelta['status']) => {
    switch (status) {
      case 'IMPROVED': return <ArrowDownRight className="w-4 h-4 text-status-pass" />;
      case 'DEGRADED': return <ArrowUpRight className="w-4 h-4 text-status-fail" />;
      case 'UNCHANGED': return <Minus className="w-4 h-4 text-ng-text-muted" />;
      default: return null;
    }
  };

  const getStatusColor = (status: MetricDelta['status']) => {
    switch (status) {
      case 'IMPROVED': return 'text-status-pass bg-status-pass/10 border-status-pass/20';
      case 'DEGRADED': return 'text-status-fail bg-status-fail/10 border-status-fail/20';
      case 'UNCHANGED': return 'text-ng-text-muted bg-white/5 border-white/10';
      default: return 'text-ng-text-muted bg-white/5 border-white/10';
    }
  };

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-black/40 border-b border-white/5 uppercase text-[10px] font-bold text-ng-text-muted tracking-wider">
          <tr>
            <th className="px-6 py-4">Metric</th>
            <th className="px-6 py-4">Baseline</th>
            <th className="px-6 py-4">Current</th>
            <th className="px-6 py-4">Delta</th>
            <th className="px-6 py-4">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {deltas.map((m, idx) => (
            <tr key={idx} className="hover:bg-white/5 transition-colors">
              <td className="px-6 py-4 text-white font-medium">{m.metric}</td>
              <td className="px-6 py-4 font-mono text-ng-text-secondary">{m.baselineValue}</td>
              <td className="px-6 py-4 font-mono text-white">{m.currentValue}</td>
              <td className="px-6 py-4 font-mono">
                <span className={clsx(
                  "px-2 py-1 rounded text-xs",
                  m.status === 'DEGRADED' ? "text-status-fail" :
                  m.status === 'IMPROVED' ? "text-status-pass" : "text-ng-text-secondary"
                )}>
                  {m.delta}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className={clsx("inline-flex items-center px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border", getStatusColor(m.status))}>
                  <span className="mr-1">{getStatusIcon(m.status)}</span>
                  {m.status}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
