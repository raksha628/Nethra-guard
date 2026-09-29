import { useNavigate } from 'react-router-dom';
import { SeverityBadge } from '../ui/SeverityBadge';
import type { Finding } from '../../types';

interface FindingsTableProps {
  findings: Finding[];
}

export function FindingsTable({ findings }: FindingsTableProps) {
  const navigate = useNavigate();

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-ng-text-muted uppercase bg-black/20 border-b border-ng-border">
            <tr>
              <th className="px-4 py-3 font-semibold">Finding ID</th>
              <th className="px-4 py-3 font-semibold">Category</th>
              <th className="px-4 py-3 font-semibold">Severity</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 font-semibold">Metric</th>
              <th className="px-4 py-3 font-semibold">Observed</th>
              <th className="px-4 py-3 font-semibold">Artifact / Sample</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ng-border">
            {findings.map((finding) => (
              <tr 
                key={finding.id} 
                className="hover:bg-white/5 cursor-pointer transition-colors"
                onClick={() => navigate(`/findings/${finding.id}`)}
              >
                <td className="px-4 py-3 font-mono text-xs text-white">{finding.id}</td>
                <td className="px-4 py-3 text-ng-text-secondary">{finding.category}</td>
                <td className="px-4 py-3">
                  <SeverityBadge severity={finding.severity} />
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs px-2 py-1 rounded bg-white/5 text-ng-text-secondary">
                    {finding.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-white truncate max-w-[200px]" title={finding.metric}>
                  {finding.metric}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-ng-text-secondary">
                  {finding.observed}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-white truncate max-w-[150px]">
                  {finding.artifact}
                </td>
              </tr>
            ))}
            {findings.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ng-text-muted">
                  No findings recorded for this run.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
