import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { CheckSelector } from '../../components/run/CheckSelector';
import { ThresholdControl } from '../../components/run/ThresholdControl';
import { ScenarioSelector } from '../../components/run/ScenarioSelector';
import { ConfigurationSummary } from '../../components/run/ConfigurationSummary';
import { JsonViewer } from '../../components/run/JsonViewer';
import { RunConfirmationModal } from '../../components/run/RunConfirmationModal';
import type { AssuranceCheckConfig, RunConfigurationState } from '../../types';

const CHECK_CONFIGS: AssuranceCheckConfig[] = [
  {
    id: 'chk_data',
    name: 'DATA INTEGRITY',
    description: 'Validate dataset structure, labels, readability, duplicates and basic anomaly conditions.',
    enabled: true,
    icon: 'database',
    summary: 'Mode: Strict | DupThresh: 0.95 | AnnCheck: Enabled'
  },
  {
    id: 'chk_model',
    name: 'MODEL INTEGRITY',
    description: 'Verify model artifact identity and compare against registered baseline.',
    enabled: true,
    icon: 'box',
    summary: 'Hashing: SHA-256 | Target: yolov8_vehicle_detect.pt'
  },
  {
    id: 'chk_shift',
    name: 'DISTRIBUTION SHIFT',
    description: 'Compare reference and current image batches using configured assessment metrics.',
    enabled: true,
    icon: 'bar-chart',
    summary: 'Metric: KS-Test | RefBatch: rn_7e81b0'
  },
  {
    id: 'chk_comp',
    name: 'ASSURANCE COMPARATOR',
    description: 'Compare current findings and metrics against a compatible baseline run.',
    enabled: true,
    icon: 'git-compare',
    summary: 'Baseline: rn_7e81b0 | Strict Compatibility: True'
  }
];

export function RunAssurance() {
  const navigate = useNavigate();
  
  const [config, setConfig] = useState<RunConfigurationState>({
    version: '1.2.0-rc',
    checks: {
      chk_data: true,
      chk_model: true,
      chk_shift: true,
      chk_comp: true,
    },
    thresholds: {
      shiftMetric: 'KS-Test',
      shiftThreshold: 0.05,
      duplicateThreshold: 0.95,
      annotationValidation: true,
      baselineCompatibility: true,
    },
    scenario: 'NONE'
  });

  const [showJson, setShowJson] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // Checking if workspace is ready
  const isWorkspaceReady = true;

  const handleToggleCheck = (id: string, enabled: boolean) => {
    setConfig(prev => ({
      ...prev,
      checks: { ...prev.checks, [id]: enabled }
    }));
  };

  const handleThresholdChange = (key: keyof RunConfigurationState['thresholds'], value: any) => {
    setConfig(prev => ({
      ...prev,
      thresholds: { ...prev.thresholds, [key]: value }
    }));
  };

  const handleStartRun = () => {
    setShowConfirm(false);
    navigate('/run-progress');
  };

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <SectionHeader 
        title="Run Assurance"
        description="Configure and execute a reproducible assurance run."
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-10">
          
          {/* SECTION 2 — CHECK SELECTION */}
          <section>
            <h2 className="text-lg font-bold text-white mb-4">Check Selection</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {CHECK_CONFIGS.map(check => (
                <CheckSelector 
                  key={check.id} 
                  check={{...check, enabled: config.checks[check.id]}} 
                  onToggle={handleToggleCheck} 
                />
              ))}
            </div>
          </section>

          {/* SECTION 3 — THRESHOLDS */}
          <section>
            <h2 className="text-lg font-bold text-white mb-4">Analysis Thresholds</h2>
            <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6 space-y-8">
              
              <div>
                <h3 className="text-sm font-bold text-white mb-3">Distribution Shift</h3>
                <ThresholdControl 
                  label="Shift Metric" 
                  value={config.thresholds.shiftMetric}
                  type="select"
                  options={[{label: 'KS-Test', value: 'KS-Test'}, {label: 'MMD', value: 'MMD'}, {label: 'Wasserstein', value: 'Wasserstein'}]}
                  onChange={(v) => handleThresholdChange('shiftMetric', v)}
                />
                <ThresholdControl 
                  label="D-value Threshold" 
                  value={config.thresholds.shiftThreshold}
                  type="number"
                  warning={true}
                  description="Maximum allowed distance before flagging a distribution shift."
                  onChange={(v) => handleThresholdChange('shiftThreshold', v)}
                />
              </div>

              <div>
                <h3 className="text-sm font-bold text-white mb-3">Dataset Anomaly</h3>
                <ThresholdControl 
                  label="Duplicate SSIM Threshold" 
                  value={config.thresholds.duplicateThreshold}
                  type="number"
                  warning={true}
                  description="Structural similarity threshold for marking images as exact duplicates."
                  onChange={(v) => handleThresholdChange('duplicateThreshold', v)}
                />
                <ThresholdControl 
                  label="Strict Annotation Validation" 
                  value={config.thresholds.annotationValidation}
                  type="toggle"
                  description="Fail data integrity check if any unmatched annotations are detected."
                  onChange={(v) => handleThresholdChange('annotationValidation', v)}
                />
              </div>

            </div>
          </section>

          {/* SECTION 5 — CONTROLLED SCENARIO */}
          <section>
            <h2 className="text-lg font-bold text-white mb-4">Assessment Scenario</h2>
            <ScenarioSelector 
              value={config.scenario} 
              onChange={(v) => setConfig(prev => ({...prev, scenario: v}))} 
            />
          </section>
        </div>

        <div className="xl:col-span-1 space-y-6">
          {/* SECTION 1 — RUN CONTEXT & SECTION 4 — REPRODUCIBILITY */}
          <div className="sticky top-6 space-y-6">
            <ConfigurationSummary 
              config={config} 
              checkConfigs={CHECK_CONFIGS}
              onViewJson={() => setShowJson(true)}
            />

            {/* SECTION 6 — ACTION */}
            <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 space-y-3">
              <button 
                onClick={() => setShowConfirm(true)}
                disabled={!isWorkspaceReady}
                className="w-full px-4 py-3 bg-ng-accent hover:bg-ng-accent-hover disabled:bg-ng-border disabled:text-ng-text-muted text-white text-sm font-bold rounded transition-colors shadow-lg shadow-ng-accent/20"
              >
                Start Assurance Run
              </button>
              <button 
                className="w-full px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded transition-colors border border-white/10"
              >
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      </div>

      <JsonViewer 
        isOpen={showJson} 
        onClose={() => setShowJson(false)} 
        config={config} 
      />

      <RunConfirmationModal 
        isOpen={showConfirm}
        onConfirm={handleStartRun}
        onCancel={() => setShowConfirm(false)}
        config={config}
        checkConfigs={CHECK_CONFIGS}
      />
    </div>
  );
}
