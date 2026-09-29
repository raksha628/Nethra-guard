export type AssuranceStatus = 'PASS' | 'WARNING' | 'FAIL' | 'NOT RUN';

export interface RunSummary {
  id: string;
  baselineId: string;
  timestamp: string;
  duration: string;
  status: AssuranceStatus;
  environment: string;
  workspaceName: string;
}

export interface MetricTrend {
  value: string;
  direction: 'up' | 'down' | 'neutral';
}

export interface CheckStatus {
  id: string;
  name: string;
  status: AssuranceStatus;
  explanation: string;
  observed?: string;
  threshold?: string;
}

export interface Finding {
  id: string;
  category: 'DATA' | 'MODEL' | 'SHIFT' | 'COMPARATOR';
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  status: 'OPEN' | 'RESOLVED' | 'IGNORED';
  metric: string;
  observed: string;
  threshold: string;
  artifact: string;
}

export interface TimelineEvent {
  id: string;
  label: string;
  timestamp: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' | 'ERROR';
}

export interface EvidenceSample {
  id: string;
  sampleId: string;
  findingType: string;
  expectedLabel: string;
  observedLabel: string;
  score?: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  imageUrl: string;
}

export interface ComparatorDelta {
  metric: string;
  baselineValue: string | number;
  currentValue: string | number;
  delta: string;
  deltaType: 'positive' | 'negative' | 'neutral';
}

export * from './workspace';
export * from './runConfig';
export * from './runProgress';
export * from './findings';
export * from './distribution';
export * from './comparator';
export * from './provenance';
export * from './reports';