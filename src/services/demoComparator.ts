import type { ComparatorContext } from '../types';

export const demoComparatorCompatible: ComparatorContext = {
  baselineRun: {
    runId: 'RUN-2026-001',
    dataset: 'vehicle_classification_v1.zip',
    model: 'yolov8_vehicle_detect.pt',
    preprocessing: 'v1.0.0-standard',
    configuration: 'Strict Assurance v1.2',
    timestamp: '2026-09-27T10:00:00Z',
    configJson: { "assuranceMode": "strict", "thresholds": { "shift": 0.3 } }
  },
  currentRun: {
    runId: 'RUN-2026-002',
    dataset: 'vehicle_classification_v1.zip',
    model: 'yolov8_vehicle_detect_tampered.pt',
    preprocessing: 'v1.0.0-standard',
    configuration: 'Strict Assurance v1.2',
    timestamp: '2026-09-28T23:01:00Z',
    configJson: { "assuranceMode": "strict", "thresholds": { "shift": 0.3 } }
  },
  compatibility: {
    isCompatible: true,
  },
  modelHashChanged: true,
  summary: 'Current run differs from baseline in 4 tracked conditions.',
  metricDeltas: [
    { metric: 'Total Findings', baselineValue: 5, currentValue: 8, delta: '+3', status: 'DEGRADED' },
    { metric: 'Critical Findings', baselineValue: 1, currentValue: 2, delta: '+1', status: 'DEGRADED' },
    { metric: 'Passed Checks', baselineValue: 42, currentValue: 40, delta: '-2', status: 'DEGRADED' },
    { metric: 'Shift Score (KS-Test)', baselineValue: 0.28, currentValue: 0.45, delta: '+0.17', status: 'DEGRADED' },
    { metric: 'Model Identity Status', baselineValue: 'MATCH', currentValue: 'MISMATCH', delta: 'MISMATCH', status: 'DEGRADED' },
    { metric: 'Dataset Anomaly Count', baselineValue: 14, currentValue: 14, delta: '0', status: 'UNCHANGED' }
  ],
  findingChanges: [
    { findingId: 'FND-0026', category: 'Distribution Shift', description: 'High-frequency noise patterns detected', type: 'NEW' },
    { findingId: 'FND-0027', category: 'Model Integrity', description: 'SHA-256 hash differs from registered baseline', type: 'NEW' },
    { findingId: 'FND-0021', category: 'Data Integrity', description: 'Near-duplicate evidence detected', baselineStatus: 'New', currentStatus: 'Reviewed', type: 'STATUS_CHANGE' },
    { findingId: 'FND-0018', category: 'Distribution Shift', description: 'Slight illumination change', baselineStatus: 'Open', currentStatus: 'Cleared', type: 'CLEARED' },
    { findingId: 'FND-0024', category: 'Data Integrity', description: 'Annotations exist without corresponding image file', type: 'UNCHANGED' },
  ]
};

export const demoComparatorIncompatible: ComparatorContext = {
  ...demoComparatorCompatible,
  currentRun: {
    ...demoComparatorCompatible.currentRun,
    dataset: 'vehicle_classification_v2_new_labels.zip',
  },
  compatibility: {
    isCompatible: false,
    reason: 'Runs are not directly comparable because configuration or evaluation inputs differ.',
    mismatchedFields: ['Dataset']
  }
};
