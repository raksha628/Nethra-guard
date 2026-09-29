export type ShiftStatus = 'PASS' | 'WARNING' | 'FAIL' | 'NOT RUN';

export interface ShiftMetricRecord {
  metricName: string;
  referenceValue: number;
  currentValue: number;
  delta: number;
  unit: string;
}

export interface ChartDataPoint {
  name: string;
  reference: number;
  current: number;
}

export interface DistributionContext {
  referenceBatch: string;
  currentBatch: string;
  runId: string;
  primaryMetric: string;
  threshold: number;
  alertLevel: ShiftStatus;
  observedScore: number;
  method: string;
  isControlledDemo: boolean;
  demoConditionName?: string;
  brightnessDistribution: ChartDataPoint[];
  rgbDistribution: ChartDataPoint[];
  dimensionsDistribution: ChartDataPoint[];
  metricsTable: ShiftMetricRecord[];
}
