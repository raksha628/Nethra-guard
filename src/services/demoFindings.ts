import type { ComprehensiveFinding } from '../types';
import { fixtureImages } from '../assets/fixtureImages';

export const comprehensiveDemoFindings: ComprehensiveFinding[] = [
  {
    id: 'FND-0021',
    category: 'Data Integrity',
    severity: 'Medium',
    status: 'New',
    findingType: 'Duplicate Detection',
    description: 'Near-duplicate samples detected',
    observed: 14,
    threshold: 5,
    artifact: 'IMG-0182',
    runId: 'RUN-2026-001',
    timestamp: '2026-09-28T22:42:15Z',
    isControlledDemo: true,
    explanation: 'Multiple image samples within the dataset exhibit structural similarity scores above the set threshold, indicating potential dataset poisoning or leakage.',
    testMethod: 'Structural Similarity Index (SSIM) > 0.95 and exact SHA-256 duplicate detection.',
    certainty: 'Rule-based / deterministic check',
    limitations: 'This prototype demonstrates deterministic duplicate detection on the configured dataset. It does not establish that the sample is maliciously poisoned.',
    remediation: 'Review affected samples and confirm whether duplicate content is expected. Purge exact duplicates if they bias the training split.',
    evidenceSamples: [
      { id: 'ev_1', sampleId: 'tank.jpg', expectedLabel: 'reference sample', observedLabel: 'Tank', fileHash: '8f91...f02b', score: '1.00', evidenceType: 'Tank', imageUrl: fixtureImages.tank },
      { id: 'ev_2', sampleId: 'ship.jpg', expectedLabel: 'reference sample', observedLabel: 'Naval ship', fileHash: 'a31c...91e4', score: '1.00', evidenceType: 'Ship', imageUrl: fixtureImages.ship }
    ]
  },
  {
    id: 'FND-0022',
    category: 'Model Integrity',
    severity: 'Critical',
    status: 'Open',
    findingType: 'Hash Mismatch',
    description: 'SHA-256 hash differs from registered baseline',
    observed: 'a9f4c2...e81d',
    threshold: 'c4e3a1...f02b',
    artifact: 'yolov8_vehicle.pt',
    runId: 'RUN-2026-001',
    timestamp: '2026-09-28T22:43:10Z',
    isControlledDemo: true,
    explanation: 'The current model artifact loaded into the workspace does not match the cryptographic signature of the established baseline artifact.',
    testMethod: 'Exact SHA-256 checksum comparison against the registered ledger baseline.',
    certainty: 'Rule-based / deterministic check',
    limitations: 'Hash mismatches indicate the file was modified, but cannot determine if the modification was a legitimate update or unauthorized tampering.',
    remediation: 'Do not deploy this artifact. Verify the provenance of the model file with the MLOps team before proceeding.'
  },
  {
    id: 'FND-0023',
    category: 'Distribution Shift',
    severity: 'High',
    status: 'Reviewed',
    findingType: 'Covariate Shift',
    description: 'KS-Test distance exceeds demonstration threshold',
    observed: 0.45,
    threshold: 0.30,
    artifact: 'batch_09_test',
    runId: 'RUN-2026-001',
    timestamp: '2026-09-28T22:44:45Z',
    isControlledDemo: true,
    explanation: 'The statistical distribution of the current inference batch significantly diverges from the reference baseline, suggesting a potential covariate shift.',
    testMethod: 'Kolmogorov-Smirnov (KS-Test) comparing feature embeddings.',
    certainty: 'Statistical Estimate',
    limitations: 'This is a statistical measurement of distribution distance and does not guarantee model performance degradation or active adversarial attack.',
    remediation: 'Review the flagged batch for out-of-distribution characteristics. Consider retraining if the shift represents a permanent environmental change.',
    evidenceSamples: [
      { id: 'ev_3', sampleId: 'jets.jpg', expectedLabel: 'reference sample', observedLabel: 'Fighter aircraft', score: 0.1, evidenceType: 'Aircraft', imageUrl: fixtureImages.jets },
      { id: 'ev_4', sampleId: 'tank.jpg', expectedLabel: 'reference sample', observedLabel: 'Tank', score: 0.1, evidenceType: 'Tank', imageUrl: fixtureImages.tank },
      { id: 'ev_5', sampleId: 'ship.jpg', expectedLabel: 'reference sample', observedLabel: 'Naval ship', score: 0.1, evidenceType: 'Ship', imageUrl: fixtureImages.ship }
    ]
  }
];
