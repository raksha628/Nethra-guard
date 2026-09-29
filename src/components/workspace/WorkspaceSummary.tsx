import { CheckCircle2, XCircle, MinusCircle } from 'lucide-react';

import type { AssetItem } from '../../types';

interface WorkspaceSummaryProps {
  dataset: AssetItem | null;
  model: AssetItem | null;
  baselineSelected: boolean;
}

export function WorkspaceSummary({ dataset, model, baselineSelected }: WorkspaceSummaryProps) {
  const getStatusItem = (label: string, isReady: boolean, notRunAllowed = false) => {
    if (isReady) {
      return (
        <div className="flex items-center justify-between text-sm py-2">
          <span className="text-ng-text-secondary">{label}</span>
          <span className="flex items-center text-status-pass font-medium">
            <CheckCircle2 className="w-4 h-4 mr-1.5" />
            PASS
          </span>
        </div>
      );
    }
    if (notRunAllowed) {
      return (
        <div className="flex items-center justify-between text-sm py-2">
          <span className="text-ng-text-secondary">{label}</span>
          <span className="flex items-center text-ng-text-muted font-medium">
            <MinusCircle className="w-4 h-4 mr-1.5" />
            NOT RUN
          </span>
        </div>
      );
    }
    return (
      <div className="flex items-center justify-between text-sm py-2">
        <span className="text-ng-text-secondary">{label}</span>
        <span className="flex items-center text-status-fail font-medium">
          <XCircle className="w-4 h-4 mr-1.5" />
          WARNING
        </span>
      </div>
    );
  };

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
      <h3 className="text-sm font-bold tracking-wide text-white mb-4">Workspace Summary</h3>
      <div className="space-y-1 divide-y divide-white/5">
        {getStatusItem('Dataset Status', dataset?.status === 'READY')}
        {getStatusItem('Model Status', model?.status === 'READY')}
        {getStatusItem('Baseline Status', baselineSelected, true)}
        {getStatusItem('Configuration', true)}
      </div>
    </div>
  );
}
