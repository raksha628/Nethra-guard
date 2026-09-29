import type { ProvenanceEntry } from '../types';

export const demoProvenanceEntries: ProvenanceEntry[] = [
  {
    sequence: 4,
    runId: 'RUN-2026-004',
    timestamp: '2026-09-28T18:42:00Z',
    previousHash: '71ab93d6...92d1',
    currentHash: '4f18d7f2...aa90',
    isValid: true,
    datasetHash: '19c8f2b1...d442',
    modelHash: 'c4e3a1f9...f02b',
    configHash: '9a31f24d...11b2',
    summaryHash: '8b7d91e3...cc33',
    actorLabel: 'Analyst Workstation (Local)',
    baselineRunId: 'RUN-2026-001'
  },
  {
    sequence: 3,
    runId: 'RUN-2026-003',
    timestamp: '2026-09-28T14:15:00Z',
    previousHash: '3b2d184a...77f1',
    currentHash: '71ab93d6...92d1',
    isValid: true,
    datasetHash: '88a31b22...e8f9',
    modelHash: 'c4e3a1f9...f02b',
    configHash: '7f9a11c8...3b92',
    summaryHash: '6c1a84f2...dd10',
    actorLabel: 'Analyst Workstation (Local)',
    baselineRunId: 'RUN-2026-001'
  },
  {
    sequence: 2,
    runId: 'RUN-2026-002',
    timestamp: '2026-09-27T16:30:00Z',
    previousHash: '9f8a1b2c...3d4e',
    currentHash: '3b2d184a...77f1',
    isValid: true,
    datasetHash: '19c8f2b1...d442',
    modelHash: 'a9f4c28b...e81d',
    configHash: '9a31f24d...11b2',
    summaryHash: '4b3d11a2...99c4',
    actorLabel: 'Analyst Workstation (Local)',
    baselineRunId: 'RUN-2026-001'
  },
  {
    sequence: 1,
    runId: 'RUN-2026-001',
    timestamp: '2026-09-27T10:00:00Z',
    previousHash: '00000000...0000',
    currentHash: '9f8a1b2c...3d4e',
    isValid: true,
    datasetHash: '19c8f2b1...d442',
    modelHash: 'c4e3a1f9...f02b',
    configHash: '9a31f24d...11b2',
    summaryHash: '1a2b3c4d...5e6f',
    actorLabel: 'Analyst Workstation (Local)'
  }
];
