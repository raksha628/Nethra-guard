import { PlayCircle, ShieldAlert } from 'lucide-react';
import type { RunConfigurationState, AssuranceCheckConfig } from '../../types';

interface RunConfirmationModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  config: RunConfigurationState;
  checkConfigs: AssuranceCheckConfig[];
}

export function RunConfirmationModal({ isOpen, onConfirm, onCancel, config, checkConfigs }: RunConfirmationModalProps) {
  if (!isOpen) return null;

  const activeChecks = checkConfigs.filter(c => config.checks[c.id]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-ng-panel-bg border border-ng-border rounded-lg shadow-xl max-w-lg w-full flex flex-col animate-in fade-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-ng-accent/10 text-ng-accent rounded border border-ng-accent/20">
              <PlayCircle className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-white">Start Assurance Run</h3>
          </div>
          <p className="text-sm text-ng-text-secondary">Please review your run configuration.</p>
        </div>
        
        <div className="p-6 space-y-6 overflow-y-auto max-h-[60vh]">
          <div>
            <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-2">Selected Checks</h4>
            <div className="flex flex-wrap gap-2">
              {activeChecks.map(c => (
                <span key={c.id} className="text-xs font-medium bg-black/30 text-white px-2 py-1 rounded border border-white/5">
                  {c.name}
                </span>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-1">Baseline</h4>
              <div className="font-mono text-white">rn_7e81b0</div>
            </div>
            <div>
              <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-1">Scenario</h4>
              <div className="text-white">{config.scenario.replace('_', ' ')}</div>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-2">Thresholds</h4>
            <div className="bg-black/30 border border-white/5 rounded p-3 text-xs space-y-2 font-mono text-ng-text-secondary">
              <div className="flex justify-between"><span>Shift Metric:</span><span className="text-white">{config.thresholds.shiftMetric}</span></div>
              <div className="flex justify-between"><span>Shift Threshold:</span><span className="text-white">{config.thresholds.shiftThreshold}</span></div>
              <div className="flex justify-between"><span>Dup Threshold:</span><span className="text-white">{config.thresholds.duplicateThreshold}</span></div>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-3 bg-status-warning/10 border border-status-warning/20 rounded text-sm text-status-warning/90">
            <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="text-xs leading-relaxed">
              <strong>Prototype Warning:</strong> This is a local offline demonstration. Results are simulated based on configured scenarios and prototype thresholds.
            </p>
          </div>
        </div>

        <div className="p-6 border-t border-white/5 bg-ng-panel-bg flex justify-end space-x-3 rounded-b-lg">
          <button 
            onClick={onCancel}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={onConfirm}
            className="px-6 py-2 bg-ng-accent hover:bg-ng-accent-hover text-white text-sm font-bold rounded shadow-lg shadow-ng-accent/20 transition-all flex items-center"
          >
            Start Run
            <PlayCircle className="w-4 h-4 ml-2" />
          </button>
        </div>
      </div>
    </div>
  );
}
