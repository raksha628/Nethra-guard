import clsx from 'clsx';
import { ArrowRight, ChevronUp, ChevronDown } from 'lucide-react';
import type { ComprehensiveFinding } from '../../types';
import { ExtendedSeverityBadge } from './ExtendedSeverityBadge';

interface FindingsTableProps {
  findings: ComprehensiveFinding[];
  onRowClick: (finding: ComprehensiveFinding) => void;
  sortField: keyof ComprehensiveFinding;
  sortDirection: 'asc' | 'desc';
  onSort: (field: keyof ComprehensiveFinding) => void;
}

export function FindingsTable({ findings, onRowClick, sortField, sortDirection, onSort }: FindingsTableProps) {
  
  const SortIcon = ({ field }: { field: keyof ComprehensiveFinding }) => {
    if (sortField !== field) return <div className="w-4 h-4 ml-1 opacity-0 group-hover:opacity-30" />;
    return sortDirection === 'asc' 
      ? <ChevronUp className="w-4 h-4 ml-1 text-ng-accent" />
      : <ChevronDown className="w-4 h-4 ml-1 text-ng-accent" />;
  };

  const headers: { label: string; field: keyof ComprehensiveFinding; className?: string }[] = [
    { label: 'ID', field: 'id', className: 'w-24' },
    { label: 'Category', field: 'category', className: 'w-36' },
    { label: 'Severity', field: 'severity', className: 'w-32' },
    { label: 'Status', field: 'status', className: 'w-24' },
    { label: 'Finding', field: 'description' },
    { label: 'Observed', field: 'observed', className: 'w-28' },
    { label: 'Threshold', field: 'threshold', className: 'w-28' },
    { label: 'Artifact', field: 'artifact', className: 'w-36 hidden lg:table-cell' },
    { label: 'Run', field: 'runId', className: 'w-32 hidden xl:table-cell' },
  ];

  if (findings.length === 0) {
    return (
      <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-12 text-center">
        <h3 className="text-lg font-medium text-white mb-2">No findings match your filters.</h3>
        <p className="text-sm text-ng-text-secondary">Try adjusting your search or category filters.</p>
      </div>
    );
  }

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-black/40 border-b border-white/5 uppercase text-[10px] font-bold text-ng-text-muted tracking-wider">
          <tr>
            {headers.map((h) => (
              <th 
                key={h.field} 
                className={clsx("px-4 py-3 cursor-pointer group select-none hover:text-white transition-colors", h.className)}
                onClick={() => onSort(h.field)}
              >
                <div className="flex items-center">
                  {h.label}
                  <SortIcon field={h.field} />
                </div>
              </th>
            ))}
            <th className="px-4 py-3 w-10"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {findings.map((finding) => (
            <tr 
              key={finding.id}
              onClick={() => onRowClick(finding)}
              className="hover:bg-white/5 transition-colors cursor-pointer group"
            >
              <td className="px-4 py-3 font-mono text-white text-xs">{finding.id}</td>
              <td className="px-4 py-3 text-ng-text-secondary text-xs">{finding.category}</td>
              <td className="px-4 py-3">
                <ExtendedSeverityBadge severity={finding.severity} />
              </td>
              <td className="px-4 py-3">
                <span className={clsx(
                  "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border",
                  finding.status === 'New' && "text-blue-400 bg-blue-400/10 border-blue-400/20",
                  finding.status === 'Open' && "text-status-warning bg-status-warning/10 border-status-warning/20",
                  finding.status === 'Reviewed' && "text-purple-400 bg-purple-400/10 border-purple-400/20",
                  finding.status === 'Cleared' && "text-status-pass bg-status-pass/10 border-status-pass/20",
                  finding.status === 'NOT RUN' && "text-ng-text-muted bg-white/5 border-white/10"
                )}>
                  {finding.status}
                </span>
              </td>
              <td className="px-4 py-3 text-white truncate max-w-[200px]" title={finding.description}>
                {finding.description}
              </td>
              <td className="px-4 py-3 font-mono text-white text-xs">{finding.observed}</td>
              <td className="px-4 py-3 font-mono text-ng-text-secondary text-xs">{finding.threshold}</td>
              <td className="px-4 py-3 font-mono text-ng-text-secondary text-xs hidden lg:table-cell truncate max-w-[120px]" title={finding.artifact}>
                {finding.artifact}
              </td>
              <td className="px-4 py-3 font-mono text-ng-text-secondary text-xs hidden xl:table-cell">{finding.runId}</td>
              <td className="px-4 py-3 text-right">
                <ArrowRight className="w-4 h-4 text-ng-text-muted group-hover:text-white transition-colors inline-block" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
