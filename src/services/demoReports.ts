import type { DemoReportPayload, ReportHistoryEntry, ReportSummary } from '../types';
import { comprehensiveDemoFindings } from './demoFindings';

export const demoReportSummary: ReportSummary = {
  project: 'NETRA-Guard',
  version: '1.2.0-offline',
  runId: 'RUN-2026-004',
  timestamp: new Date().toISOString(),
  workspace: 'Vehicle Classification Workspace',
  datasetHash: '19c8f2b15e34d442',
  modelHash: 'c4e3a1f9a88bf02b',
  configHash: '9a31f24db21c11b2',
  summaryStatus: 'WARNING'
};

export const demoReportHistory: ReportHistoryEntry[] = [
  { reportId: 'RPT-2026-004-JSON', runId: 'RUN-2026-004', created: '2026-09-28T18:43:10Z', status: 'GENERATED' },
  { reportId: 'RPT-2026-003-JSON', runId: 'RUN-2026-003', created: '2026-09-28T14:16:00Z', status: 'GENERATED' },
  { reportId: 'RPT-2026-002-JSON', runId: 'RUN-2026-002', created: '2026-09-27T16:32:00Z', status: 'GENERATED' },
];

export const generateDemoReport = (): DemoReportPayload => {
  return {
    metadata: demoReportSummary,
    checksExecuted: [
      'Data Integrity (Duplicates, Anomalies)',
      'Model Integrity (Hash, Structure)',
      'Distribution Shift (KS-Test, Histogram)'
    ],
    checksSkipped: [
      'Adversarial Robustness (Skipped due to offline mode)'
    ],
    findings: comprehensiveDemoFindings,
    provenance: {
      sequence: 4,
      isValid: true,
      previousHash: '71ab93d6...92d1'
    },
    softwareVersions: {
      'netra-guard-core': '1.2.0',
      'python': '3.11.2',
      'torch': '2.1.0'
    },
    limitations: [
      'Offline local evaluation only.',
      'Dataset is an operational assessment subset.',
      'Thresholds are calibrated for analysis, not global production.'
    ]
  };
};
