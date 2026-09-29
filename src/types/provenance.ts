export interface ProvenanceEntry {
  sequence: number;
  runId: string;
  timestamp: string;
  previousHash: string;
  currentHash: string;
  isValid: boolean;
  datasetHash: string;
  modelHash: string;
  configHash: string;
  summaryHash: string;
  actorLabel: string;
  baselineRunId?: string;
}

export interface LedgerVerificationState {
  status: 'VALID' | 'FAILED' | 'VERIFYING';
  firstInvalidSequence?: number;
  reason?: string;
  timestamp?: string;
}
