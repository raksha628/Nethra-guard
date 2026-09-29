export interface ReportSummary {
  project: string;
  version: string;
  runId: string;
  timestamp: string;
  workspace: string;
  datasetHash: string;
  modelHash: string;
  configHash: string;
  summaryStatus: 'PASS' | 'WARNING' | 'FAIL';
}

export interface ReportHistoryEntry {
  reportId: string;
  runId: string;
  created: string;
  status: 'GENERATED' | 'FAILED' | 'PENDING';
  downloadUrl?: string;
}

export interface DemoReportPayload {
  metadata: ReportSummary;
  checksExecuted: string[];
  checksSkipped: string[];
  findings: any[];
  provenance: any;
  softwareVersions: Record<string, string>;
  limitations: string[];
}
