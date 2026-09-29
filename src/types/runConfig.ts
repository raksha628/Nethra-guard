export interface AssuranceCheckConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  icon: string;
  summary: string;
}

export interface ThresholdConfig {
  shiftMetric: string;
  shiftThreshold: number;
  duplicateThreshold: number;
  annotationValidation: boolean;
  baselineCompatibility: boolean;
}

export type DemoScenario = 'NONE' | 'DATA_ANOMALY' | 'MODEL_MISMATCH' | 'DISTRIBUTION_SHIFT';

export interface RunConfigurationState {
  version: string;
  checks: Record<string, boolean>;
  thresholds: ThresholdConfig;
  scenario: DemoScenario;
}
