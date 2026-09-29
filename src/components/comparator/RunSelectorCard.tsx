import type { RunMetadata } from '../../types';

interface RunSelectorCardProps {
  label: string;
  run: RunMetadata;
}

export function RunSelectorCard({ label, run }: RunSelectorCardProps) {
  return (
    <div className="bg-black/30 border border-white/5 rounded-lg p-5">
      <div className="text-xs text-ng-text-muted uppercase tracking-wider mb-4 flex justify-between items-center">
        <span>{label}</span>
        <span className="font-mono text-white text-sm bg-black/50 px-2 py-1 rounded">{run.runId}</span>
      </div>
      
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Dataset</span>
          <span className="text-white font-mono truncate max-w-[150px]" title={run.dataset}>{run.dataset}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Model</span>
          <span className="text-white font-mono truncate max-w-[150px]" title={run.model}>{run.model}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Preprocessing</span>
          <span className="text-white font-mono">{run.preprocessing}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Configuration</span>
          <span className="text-white font-medium">{run.configuration}</span>
        </div>
      </div>
    </div>
  );
}
