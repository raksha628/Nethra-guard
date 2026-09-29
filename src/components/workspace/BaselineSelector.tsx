import { GitCommit } from 'lucide-react';
import clsx from 'clsx';
import { HashDisplay } from './HashDisplay';

interface BaselineSelectorProps {
  selected?: {
    id: string;
    timestamp: string;
    datasetHash: string;
    modelHash: string;
  };
  onSelect: () => void;
  className?: string;
}

export function BaselineSelector({ selected, onSelect, className }: BaselineSelectorProps) {
  return (
    <div className={clsx("bg-ng-panel-bg border border-ng-border rounded-lg p-5", className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-black/20 rounded border border-white/5 text-ng-text-secondary">
            <GitCommit className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white tracking-wide">Baseline Configuration</h4>
            <div className="text-xs text-ng-text-muted mt-0.5">Select a verified run to compare against</div>
          </div>
        </div>
        <button 
          onClick={onSelect}
          className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded transition-colors border border-white/10"
        >
          {selected ? 'Change Baseline' : 'Select Baseline'}
        </button>
      </div>

      {selected ? (
        <div className="mt-4 pt-4 border-t border-white/5 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <div className="text-[10px] text-ng-text-muted uppercase tracking-wider mb-1">Run ID</div>
            <div className="text-xs font-mono text-white">{selected.id}</div>
          </div>
          <div>
            <div className="text-[10px] text-ng-text-muted uppercase tracking-wider mb-1">Timestamp</div>
            <div className="text-xs font-mono text-white">{selected.timestamp}</div>
          </div>
          <div>
            <div className="text-[10px] text-ng-text-muted uppercase tracking-wider mb-1">Dataset Hash</div>
            <HashDisplay hash={selected.datasetHash} />
          </div>
          <div>
            <div className="text-[10px] text-ng-text-muted uppercase tracking-wider mb-1">Model Hash</div>
            <HashDisplay hash={selected.modelHash} />
          </div>
        </div>
      ) : (
        <div className="mt-4 pt-4 border-t border-white/5 text-sm text-status-warning font-medium">
          No baseline selected. Comparator check will be disabled.
        </div>
      )}
    </div>
  );
}
