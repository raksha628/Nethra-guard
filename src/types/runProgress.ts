export type StageStatus = 'WAITING' | 'RUNNING' | 'COMPLETE' | 'WARNING' | 'FAILED' | 'SKIPPED';
export type RunOverallStatus = 'INITIALIZING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface RunStage {
  id: string;
  name: string;
  description: string;
  status: StageStatus;
  startTime?: string;
  completionTime?: string;
  errorDetail?: string;
  resultSummary?: string;
}

export interface RunState {
  runId: string;
  workspace: string;
  startTime: string;
  baseline: string;
  scenario: string;
  overallStatus: RunOverallStatus;
  progressPercentage: number;
  elapsedSeconds: number;
  completedChecks: number;
  warningsCount: number;
  findingsCount: number;
  stages: RunStage[];
}
