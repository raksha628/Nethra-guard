import { useNavigate } from 'react-router-dom';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { useRunProgress } from '../../hooks/useRunProgress';
import { 
  AlertTriangle, AlertCircle, CheckCircle2, XCircle, 
  MinusCircle, Clock, Info, ShieldAlert, ArrowLeft, RefreshCw,
  GitCommit, Download, Search
} from 'lucide-react';
import clsx from 'clsx';
import type { StageStatus } from '../../types';

function getStatusColor(status: StageStatus) {
  switch (status) {
    case 'COMPLETE': return 'text-status-pass';
    case 'WARNING': return 'text-status-warning';
    case 'FAILED': return 'text-status-fail';
    case 'RUNNING': return 'text-ng-accent';
    case 'SKIPPED': return 'text-ng-text-muted';
    default: return 'text-ng-text-muted';
  }
}

function getStatusIcon(status: StageStatus, className: string = "w-5 h-5") {
  switch (status) {
    case 'COMPLETE': return <CheckCircle2 className={clsx(className, getStatusColor(status))} />;
    case 'WARNING': return <AlertTriangle className={clsx(className, getStatusColor(status))} />;
    case 'FAILED': return <XCircle className={clsx(className, getStatusColor(status))} />;
    case 'RUNNING': return <RefreshCw className={clsx(className, getStatusColor(status), 'animate-spin')} />;
    case 'SKIPPED': return <MinusCircle className={clsx(className, getStatusColor(status))} />;
    default: return <Clock className={clsx(className, getStatusColor(status))} />;
  }
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

export function RunProgress() {
  const navigate = useNavigate();
  // Using MODEL_MISMATCH for testing the error state explicitly as required.
  const { state, cancelRun, retryFailed } = useRunProgress('MODEL_MISMATCH');

  const currentStage = state.stages.find(s => s.status === 'RUNNING');
  const failedStage = state.stages.find(s => s.status === 'FAILED');

  const completedStages = state.stages.filter(s => ['COMPLETE', 'WARNING', 'FAILED', 'SKIPPED'].includes(s.status));

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <SectionHeader 
        title="Assurance Run"
        description="Monitor dataset, model, inference, distribution and provenance assurance."
      >
        <div className="flex items-center space-x-2 text-xs font-semibold px-2 py-1 bg-status-warning/10 text-status-warning border border-status-warning/20 rounded uppercase tracking-wider">
          <ShieldAlert className="w-3.5 h-3.5 mr-1" />
          PROTOTYPE / CONTROLLED DEMO
        </div>
      </SectionHeader>

      <div className="flex items-start space-x-3 p-3 bg-ng-accent/10 border border-ng-accent/20 rounded text-sm text-ng-accent">
        <Info className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <p className="text-xs">
          <strong>Demo execution</strong> — results are simulated frontend data using the `useRunProgress` mock service.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* MAIN PROGRESS STEPPER */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-6">Execution Stages</h3>
            <div className="relative border-l border-white/10 ml-4 space-y-8">
              {state.stages.map((stage, idx) => (
                <div key={stage.id} className="relative pl-8">
                  <div className="absolute -left-[14px] top-0 p-1 bg-ng-dark-bg">
                    {getStatusIcon(stage.status, "w-5 h-5")}
                  </div>
                  
                  <div className="flex flex-col mb-1">
                    <div className="flex items-center justify-between">
                      <h4 className={clsx(
                        "text-sm font-bold",
                        stage.status === 'WAITING' ? "text-ng-text-muted" : "text-white"
                      )}>
                        {idx + 1}. {stage.name}
                      </h4>
                      <div className="flex items-center space-x-3">
                        {stage.status !== 'WAITING' && (
                          <span className={clsx(
                            "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border",
                            stage.status === 'COMPLETE' && "bg-status-pass/10 text-status-pass border-status-pass/20",
                            stage.status === 'WARNING' && "bg-status-warning/10 text-status-warning border-status-warning/20",
                            stage.status === 'FAILED' && "bg-status-fail/10 text-status-fail border-status-fail/20",
                            stage.status === 'RUNNING' && "bg-ng-accent/10 text-ng-accent border-ng-accent/20",
                            stage.status === 'SKIPPED' && "bg-white/5 text-ng-text-muted border-white/10"
                          )}>
                            {stage.status}
                          </span>
                        )}
                        {stage.startTime && <span className="text-xs font-mono text-ng-text-muted">{stage.startTime}</span>}
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-xs text-ng-text-secondary mb-2">{stage.description}</p>
                  
                  {stage.resultSummary && (
                    <div className="text-xs font-medium text-white bg-black/20 p-2 rounded border border-white/5">
                      {stage.resultSummary}
                    </div>
                  )}

                  {stage.errorDetail && (
                    <div className="text-xs font-medium text-status-fail bg-status-fail/10 p-2 rounded border border-status-fail/20 mt-2">
                      {stage.errorDetail}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-1 space-y-6">
          {/* HEADER DETAILS */}
          <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-ng-text-secondary">Run ID</span><span className="font-mono text-white">{state.runId}</span></div>
            <div className="flex justify-between"><span className="text-ng-text-secondary">Workspace</span><span className="font-mono text-white">{state.workspace}</span></div>
            <div className="flex justify-between"><span className="text-ng-text-secondary">Baseline</span><span className="font-mono text-white">{state.baseline}</span></div>
            <div className="flex justify-between"><span className="text-ng-text-secondary">Scenario</span><span className="text-white text-right max-w-[150px] truncate">{state.scenario.replace('_', ' ')}</span></div>
          </div>

          {/* PROGRESS PANEL */}
          <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-white tracking-wide">Overall Progress</h3>
              <span className="font-mono text-white text-lg">{state.progressPercentage}%</span>
            </div>
            
            <div className="h-2 w-full bg-black/40 rounded-full overflow-hidden mb-6">
              <div 
                className={clsx(
                  "h-full transition-all duration-500",
                  state.overallStatus === 'FAILED' ? "bg-status-fail" : "bg-ng-accent"
                )}
                style={{ width: `${state.progressPercentage}%` }}
              />
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm mb-6">
              <div className="bg-black/20 p-3 rounded border border-white/5">
                <div className="text-xs text-ng-text-muted mb-1">Elapsed Time</div>
                <div className="font-mono text-white text-xl">{formatTime(state.elapsedSeconds)}</div>
              </div>
              <div className="bg-black/20 p-3 rounded border border-white/5">
                <div className="text-xs text-ng-text-muted mb-1">Completed Checks</div>
                <div className="font-mono text-white text-xl">{state.completedChecks}</div>
              </div>
              <div className="bg-black/20 p-3 rounded border border-white/5">
                <div className="text-xs text-ng-text-muted mb-1">Warnings</div>
                <div className="font-mono text-status-warning text-xl">{state.warningsCount}</div>
              </div>
              <div className="bg-black/20 p-3 rounded border border-white/5">
                <div className="text-xs text-ng-text-muted mb-1">Findings Generated</div>
                <div className="font-mono text-white text-xl">{state.findingsCount}</div>
              </div>
            </div>

            {state.overallStatus === 'IN_PROGRESS' && currentStage && (
              <div className="text-xs text-ng-accent flex items-center mb-6">
                <RefreshCw className="w-3.5 h-3.5 mr-2 animate-spin" />
                Currently executing: {currentStage.name}...
              </div>
            )}

            {/* ERROR STATE */}
            {state.overallStatus === 'FAILED' && failedStage && (
              <div className="mb-6 p-4 bg-status-fail/10 border border-status-fail/20 rounded-lg">
                <div className="flex items-center text-status-fail font-bold mb-2">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  Run Failed at {failedStage.name}
                </div>
                <p className="text-xs text-status-fail/80 mb-4">{failedStage.errorDetail}</p>
                <div className="flex space-x-3">
                  <button onClick={retryFailed} className="px-3 py-1.5 bg-status-fail hover:bg-red-600 text-white text-xs font-bold rounded transition-colors flex-1 text-center">
                    Retry Stage
                  </button>
                  <button onClick={() => navigate('/run-assurance')} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded border border-white/10 transition-colors flex-1 text-center">
                    Reconfigure
                  </button>
                </div>
              </div>
            )}

            {/* SUCCESS STATE */}
            {state.overallStatus === 'COMPLETED' && (
              <div className="mb-6 space-y-3">
                <div className="p-3 bg-status-pass/10 border border-status-pass/20 text-status-pass text-sm font-bold flex items-center justify-center rounded">
                  <CheckCircle2 className="w-5 h-5 mr-2" />
                  Assurance Run Completed
                </div>
                <button onClick={() => navigate('/findings')} className="w-full flex items-center justify-center px-4 py-2 bg-ng-accent hover:bg-ng-accent-hover text-white text-sm font-bold rounded transition-colors">
                  <Search className="w-4 h-4 mr-2" />
                  View Findings
                </button>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => navigate('/comparator')} className="px-2 py-1.5 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded border border-white/10 transition-colors flex items-center justify-center">
                    <GitCommit className="w-3 h-3 mr-1.5" />
                    Compare Baseline
                  </button>
                  <button className="px-2 py-1.5 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded border border-white/10 transition-colors flex items-center justify-center">
                    <Download className="w-3 h-3 mr-1.5" />
                    Export Report
                  </button>
                </div>
              </div>
            )}

            {(state.overallStatus === 'IN_PROGRESS' || state.overallStatus === 'INITIALIZING') && (
              <button 
                onClick={cancelRun}
                className="w-full px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded transition-colors border border-white/10"
              >
                Cancel Run
              </button>
            )}

            {(state.overallStatus === 'CANCELLED') && (
              <div className="space-y-3">
                <div className="text-center text-status-warning text-sm font-bold">Run Cancelled</div>
                <button onClick={() => navigate('/run-assurance')} className="w-full flex items-center justify-center px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded transition-colors border border-white/10">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Return to Configuration
                </button>
              </div>
            )}
          </div>

          {/* LIVE RESULT PREVIEW */}
          {completedStages.length > 0 && (
            <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
              <h3 className="text-sm font-bold text-white tracking-wide mb-4">Live Results</h3>
              <div className="space-y-3">
                {completedStages.map(s => (
                  <div key={`preview-${s.id}`} className="bg-black/20 p-3 rounded border border-white/5 text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-white text-xs">{s.name}</span>
                      <span className={clsx("text-[10px] font-bold uppercase tracking-wider", getStatusColor(s.status))}>
                        {s.status}
                      </span>
                    </div>
                    {s.resultSummary && (
                      <div className="text-xs text-ng-text-secondary">{s.resultSummary}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
