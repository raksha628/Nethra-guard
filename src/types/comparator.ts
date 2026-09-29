export interface RunMetadata {
  runId: string;
  dataset: string;
  model: string;
  preprocessing: string;
  configuration: string;
  timestamp: string;
  configJson: Record<string, any>;
}

export interface CompatibilityInfo {
  isCompatible: boolean;
  reason?: string;
  mismatchedFields?: string[];
}

export interface MetricDelta {
  metric: string;
  baselineValue: string | number;
  currentValue: string | number;
  delta: string | number;
  status: 'IMPROVED' | 'DEGRADED' | 'UNCHANGED' | 'N/A';
}

export interface FindingChange {
  findingId: string;
  category: string;
  description: string;
  baselineStatus?: string;
  currentStatus?: string;
  type: 'NEW' | 'CLEARED' | 'UNCHANGED' | 'STATUS_CHANGE';
}

export interface ComparatorContext {
  baselineRun: RunMetadata;
  currentRun: RunMetadata;
  compatibility: CompatibilityInfo;
  metricDeltas: MetricDelta[];
  findingChanges: FindingChange[];
  summary: string;
  modelHashChanged: boolean;
}
