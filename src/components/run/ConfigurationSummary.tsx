import type { RunConfigurationState, AssuranceCheckConfig } from '../../types';

interface ConfigurationSummaryProps {
  config: RunConfigurationState;
  checkConfigs: AssuranceCheckConfig[];
  onViewJson: () => void;
}

export function ConfigurationSummary({ config, checkConfigs, onViewJson }: ConfigurationSummaryProps) {
  const activeChecks = checkConfigs.filter(c => config.checks[c.id]).length;
  
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold tracking-wide text-white">Reproducibility</h3>
        <span className="text-xs font-mono text-ng-text-muted">v{config.version}</span>
      </div>

      <div className="space-y-4 text-sm mb-6">
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Selected Checks</span>
          <span className="text-white font-medium">{activeChecks} / {checkConfigs.length}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Baseline ID</span>
          <span className="text-white font-mono">rn_7e81b0</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Dataset</span>
          <span className="text-white font-mono truncate max-w-[150px]" title="vehicle_classification_v1.zip">vehicle_class...zip</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Model</span>
          <span className="text-white font-mono truncate max-w-[150px]" title="yolov8_vehicle_detect.pt">yolov8_vehicle...pt</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ng-text-secondary">Evaluation Mode</span>
          <span className="text-white font-medium">Assurance Platform</span>
        </div>
      </div>

      <button 
        onClick={onViewJson}
        className="w-full px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded transition-colors border border-white/10"
      >
        View configuration JSON
      </button>
    </div>
  );
}
