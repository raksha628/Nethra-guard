import { StatusBadge } from '../ui/StatusBadge';
import { ArrowRight } from 'lucide-react';
import type { CheckStatus } from '../../types';

interface CheckCardProps {
  check: CheckStatus;
}

export function CheckCard({ check }: CheckCardProps) {
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col hover:border-white/10 transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-bold tracking-wide text-white">{check.name}</h3>
        <StatusBadge status={check.status} />
      </div>
      
      <p className="text-sm text-ng-text-secondary mb-4 flex-1">
        {check.explanation}
      </p>

      {(check.observed || check.threshold) && (
        <div className="bg-black/20 rounded p-3 mb-4 space-y-1 border border-white/5">
          {check.observed && (
            <div className="text-xs font-mono text-white">{check.observed}</div>
          )}
          {check.threshold && (
            <div className="text-xs font-mono text-ng-text-muted">{check.threshold}</div>
          )}
        </div>
      )}

      <button className="flex items-center text-xs font-medium text-ng-accent hover:text-ng-accent-hover mt-auto transition-colors">
        View findings
        <ArrowRight className="w-3.5 h-3.5 ml-1.5 group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  );
}
