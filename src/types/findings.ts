export type FindingCategory = 'Data Integrity' | 'Model Integrity' | 'Distribution Shift' | 'Comparator';
export type FindingSeverity = 'Critical' | 'High' | 'Medium' | 'Low' | 'Informational';
export type FindingStatus = 'New' | 'Open' | 'Reviewed' | 'Cleared' | 'NOT RUN';

export interface ComprehensiveFinding {
  id: string;
  category: FindingCategory;
  severity: FindingSeverity;
  status: FindingStatus;
  findingType: string;
  description: string;
  observed: string | number;
  threshold: string | number;
  artifact: string;
  runId: string;
  timestamp: string;
  isControlledDemo?: boolean;
  explanation?: string;
  testMethod?: string;
  certainty?: string;
  limitations?: string;
  remediation?: string;
  evidenceSamples?: EvidenceSample[];
}

export interface EvidenceSample {
  id: string;
  sampleId: string;
  expectedLabel?: string;
  observedLabel?: string;
  fileHash?: string;
  score?: string | number;
  evidenceType: string;
  imageUrl?: string;
}
