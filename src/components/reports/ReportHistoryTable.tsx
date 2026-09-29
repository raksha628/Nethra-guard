import { Download } from 'lucide-react';
import type { ReportHistoryEntry } from '../../types';

export function ReportHistoryTable({ history }: { history: ReportHistoryEntry[] }) {
  if (history.length === 0) {
    return (
      <div className="bg-black/20 border border-white/5 rounded-lg p-8 text-center">
        <p className="text-sm text-ng-text-muted">No reports generated yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-black/40 border-b border-white/5 uppercase text-[10px] font-bold text-ng-text-muted tracking-wider">
          <tr>
            <th className="px-6 py-4">Report ID</th>
            <th className="px-6 py-4">Run ID</th>
            <th className="px-6 py-4">Created</th>
            <th className="px-6 py-4">Status</th>
            <th className="px-6 py-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {history.map(entry => (
            <tr key={entry.reportId} className="hover:bg-white/5 transition-colors group">
              <td className="px-6 py-4 font-mono text-white text-xs">{entry.reportId}</td>
              <td className="px-6 py-4 font-mono text-ng-text-secondary text-xs">{entry.runId}</td>
              <td className="px-6 py-4 text-ng-text-secondary">{new Date(entry.created).toLocaleString()}</td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border text-status-pass bg-status-pass/10 border-status-pass/20">
                  {entry.status}
                </span>
              </td>
              <td className="px-6 py-4 text-right">
                <button className="p-2 text-ng-text-muted hover:text-white transition-colors">
                  <Download className="w-4 h-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
