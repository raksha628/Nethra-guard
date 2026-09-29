import type { 
  RunSummary, 
  CheckStatus, 
  Finding, 
  TimelineEvent, 
  EvidenceSample,
  ComparatorDelta 
} from '../types';

export const demoRunSummary: RunSummary = {
  id: 'rn_8f92a1',
  baselineId: 'rn_7e81b0',
  timestamp: '2026-09-28T22:45:43Z',
  duration: '4m 12s',
  status: 'WARNING',
  environment: 'Local / Offline',
  workspaceName: 'default-ws-01'
};

export const demoCheckStatuses: CheckStatus[] = [
  {
    id: 'chk_data_01',
    name: 'DATA INTEGRITY',
    status: 'PASS',
    explanation: 'Dataset structure and annotation validation completed.',
    observed: '1,240 images | 1,238 annotations',
  },
  {
    id: 'chk_model_01',
    name: 'MODEL INTEGRITY',
    status: 'WARNING',
    explanation: 'Registered artifact hash differs from baseline.',
    observed: 'Hash mismatch detected',
  },
  {
    id: 'chk_shift_01',
    name: 'DISTRIBUTION SHIFT',
    status: 'PASS',
    explanation: 'Current batch remains within demonstration threshold.',
    observed: 'Shift score: 0.18',
    threshold: 'Threshold: 0.30',
  },
  {
    id: 'chk_comp_01',
    name: 'COMPARATOR',
    status: 'WARNING',
    explanation: '2 findings changed since baseline.',
  },
  {
    id: 'chk_prov_01',
    name: 'LEDGER PROVENANCE',
    status: 'NOT RUN',
    explanation: 'This check has not been executed for the current run.',
  }
];

export const demoFindings: Finding[] = [
  {
    id: 'FND-001',
    category: 'MODEL',
    severity: 'WARNING',
    status: 'OPEN',
    metric: 'SHA-256 Hash Match',
    observed: 'a9f4c2...e81d',
    threshold: 'c4e3a1...f02b (Baseline)',
    artifact: 'weights_v2.pt'
  },
  {
    id: 'FND-002',
    category: 'DATA',
    severity: 'INFO',
    status: 'OPEN',
    metric: 'Unmatched Annotations',
    observed: '2 missing labels',
    threshold: '0 missing allowed',
    artifact: 'batch_04.json'
  },
  {
    id: 'FND-003',
    category: 'SHIFT',
    severity: 'CRITICAL',
    status: 'OPEN',
    metric: 'Adversarial Noise Detection',
    observed: '0.45 score',
    threshold: '< 0.30 required',
    artifact: 'image_844.png'
  }
];

export const demoTimeline: TimelineEvent[] = [
  { id: 't1', label: 'Run started', timestamp: '22:41:31', status: 'COMPLETED' },
  { id: 't2', label: 'Data checks', timestamp: '22:42:05', status: 'COMPLETED' },
  { id: 't3', label: 'Model checks', timestamp: '22:43:10', status: 'COMPLETED' },
  { id: 't4', label: 'Distribution analysis', timestamp: '22:44:45', status: 'COMPLETED' },
  { id: 't5', label: 'Comparator', timestamp: '22:45:20', status: 'COMPLETED' },
  { id: 't6', label: 'Ledger recorded', timestamp: '--:--:--', status: 'PENDING' },
  { id: 't7', label: 'Run completed', timestamp: '22:45:43', status: 'COMPLETED' }
];

export const demoEvidence: EvidenceSample[] = [
  {
    id: 'ev_001',
    sampleId: 'img_844',
    findingType: 'Adversarial Noise',
    expectedLabel: 'Authorized Vehicle',
    observedLabel: 'Unknown Object',
    score: '0.45',
    severity: 'CRITICAL',
    imageUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjM2YzZjRmIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZpbGw9IiM5Y2EzYWYiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5TYW1wbGUgSW1hZ2UgUHJldmlldzwvdGV4dD48L3N2Zz4='
  },
  {
    id: 'ev_002',
    sampleId: 'img_845',
    findingType: 'Blur Degradation',
    expectedLabel: 'License Plate',
    observedLabel: 'License Plate',
    score: '0.88',
    severity: 'INFO',
    imageUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjM2YzZjRmIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZpbGw9IiM5Y2EzYWYiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5TYW1wbGUgSW1hZ2UgUHJldmlldzwvdGV4dD48L3N2Zz4='
  },
  {
    id: 'ev_003',
    sampleId: 'img_846',
    findingType: 'Illumination Shift',
    expectedLabel: 'Face',
    observedLabel: 'Face',
    score: '0.72',
    severity: 'WARNING',
    imageUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjM2YzZjRmIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZpbGw9IiM5Y2EzYWYiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5TYW1wbGUgSW1hZ2UgUHJldmlldzwvdGV4dD48L3N2Zz4='
  },
  {
    id: 'ev_004',
    sampleId: 'img_847',
    findingType: 'Data Poisoning Demo',
    expectedLabel: 'Person',
    observedLabel: 'Stop Sign',
    score: '0.94',
    severity: 'CRITICAL',
    imageUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjM2YzZjRmIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZpbGw9IiM5Y2EzYWYiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5TYW1wbGUgSW1hZ2UgUHJldmlldzwvdGV4dD48L3N2Zz4='
  }
];

export const demoComparatorDeltas: ComparatorDelta[] = [
  { metric: 'Total Findings', baselineValue: 1, currentValue: 3, delta: '+2', deltaType: 'negative' },
  { metric: 'Critical Findings', baselineValue: 0, currentValue: 2, delta: '+2', deltaType: 'negative' },
  { metric: 'Warning Findings', baselineValue: 1, currentValue: 1, delta: '0', deltaType: 'neutral' },
  { metric: 'Passed Checks', baselineValue: 12, currentValue: 11, delta: '-1', deltaType: 'negative' },
  { metric: 'Shift Score', baselineValue: 0.12, currentValue: 0.18, delta: '+0.06', deltaType: 'negative' },
  { metric: 'Model Hash', baselineValue: 'MATCH', currentValue: 'MISMATCH', delta: 'Changed', deltaType: 'negative' },
];
