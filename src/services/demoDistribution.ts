import type { DistributionContext } from '../types';

export const demoDistributionContext: DistributionContext = {
  referenceBatch: 'rn_7e81b0',
  currentBatch: 'RUN-2026-001',
  runId: 'RUN-2026-001',
  primaryMetric: 'KS-Test Distance',
  threshold: 0.30,
  alertLevel: 'WARNING',
  observedScore: 0.45,
  method: 'Histogram distance (Wasserstein & KS-Test)',
  isControlledDemo: false,
  demoConditionName: 'BRIGHTNESS SHIFT',
  
  brightnessDistribution: [
    { name: '0-50', reference: 120, current: 40 },
    { name: '51-100', reference: 300, current: 150 },
    { name: '101-150', reference: 450, current: 280 },
    { name: '151-200', reference: 200, current: 520 },
    { name: '201-255', reference: 50, current: 400 },
  ],
  
  rgbDistribution: [
    { name: 'Red Mean', reference: 122, current: 165 },
    { name: 'Green Mean', reference: 118, current: 160 },
    { name: 'Blue Mean', reference: 115, current: 158 },
  ],

  dimensionsDistribution: [
    { name: '640x640', reference: 800, current: 790 },
    { name: '1280x720', reference: 200, current: 210 },
    { name: 'Other', reference: 120, current: 240 },
  ],

  metricsTable: [
    { metricName: 'Brightness Mean', referenceValue: 118.5, currentValue: 172.4, delta: 53.9, unit: 'intensity' },
    { metricName: 'Contrast (Std)', referenceValue: 42.1, currentValue: 45.3, delta: 3.2, unit: 'intensity' },
    { metricName: 'Edge Density', referenceValue: 0.12, currentValue: 0.11, delta: -0.01, unit: 'ratio' },
    { metricName: 'KS-Test Distance', referenceValue: 0.05, currentValue: 0.45, delta: 0.40, unit: 'D-score' },
  ]
};
