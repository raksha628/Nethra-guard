import clsx from 'clsx';
import { ShieldAlert, Info } from 'lucide-react';
import type { DemoScenario } from '../../types';

interface ScenarioSelectorProps {
  value: DemoScenario;
  onChange: (scenario: DemoScenario) => void;
}

export function ScenarioSelector({ value, onChange }: ScenarioSelectorProps) {
  const scenarios: { id: DemoScenario; label: string; desc: string }[] = [
    { id: 'NONE', label: 'None / Baseline', desc: 'Execute normal checks against selected baseline.' },
    { id: 'DATA_ANOMALY', label: 'Dataset anomaly', desc: 'Simulates missing annotations and duplicate images in the current batch.' },
    { id: 'MODEL_MISMATCH', label: 'Model hash mismatch', desc: 'Simulates a changed model artifact that fails identity verification.' },
    { id: 'DISTRIBUTION_SHIFT', label: 'Distribution shift', desc: 'Simulates covariate shift using adversarial noise exceeding demonstration thresholds.' },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {scenarios.map(scenario => (
          <button
            key={scenario.id}
            onClick={() => onChange(scenario.id)}
            className={clsx(
              "text-left p-4 rounded-lg border transition-all relative overflow-hidden",
              value === scenario.id 
                ? "bg-ng-accent/10 border-ng-accent" 
                : "bg-ng-panel-bg border-ng-border hover:border-white/20"
            )}
          >
            {scenario.id !== 'NONE' && (
              <div className="absolute top-0 right-0">
                <div className="bg-status-warning text-black text-[9px] font-black px-2 py-0.5 rounded-bl uppercase tracking-widest flex items-center">
                  <ShieldAlert className="w-3 h-3 mr-1" />
                  CONTROLLED DEMO
                </div>
              </div>
            )}
            <div className={clsx("font-bold text-sm mb-1", value === scenario.id ? "text-white" : "text-ng-text-secondary")}>
              {scenario.label}
            </div>
            <div className="text-xs text-ng-text-muted mt-2">
              {scenario.desc}
            </div>
          </button>
        ))}
      </div>
      
      {value !== 'NONE' && (
        <div className="flex items-start space-x-3 p-3 bg-status-warning/10 border border-status-warning/20 rounded text-sm text-status-warning/90 mt-4">
          <Info className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p className="text-xs leading-relaxed">
            This scenario is simulated for demonstration and does not represent comprehensive real-world attack detection. 
            It is designed to showcase the dashboard's ability to capture and report specific failure states.
          </p>
        </div>
      )}
    </div>
  );
}
