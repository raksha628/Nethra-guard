import { useState, useEffect, useRef } from 'react';
import type { RunState, RunStage } from '../types';
import { api } from '../services/api';

const INITIAL_STAGES: RunStage[] = [
  { id: 's1', name: 'Initializing', description: 'Preparing workspace and allocating local resources.', status: 'WAITING' },
  { id: 's2', name: 'Data Integrity', description: 'Validating dataset structure, labels, readability, and duplicates.', status: 'WAITING' },
  { id: 's3', name: 'Model Integrity', description: 'Verifying model artifact identity against registered baseline.', status: 'WAITING' },
  { id: 's4', name: 'Distribution Shift', description: 'Comparing reference and current image batches.', status: 'WAITING' },
  { id: 's5', name: 'Semantic Evaluation', description: 'Calculating Precision, Recall, and mAP against ground-truth dataset.', status: 'WAITING' },
  { id: 's6', name: 'Recording Provenance', description: 'Cryptographically logging execution steps to the local ledger.', status: 'WAITING' },
  { id: 's7', name: 'Finalizing', description: 'Generating reports and cleaning up temporary assets.', status: 'WAITING' }
];

export function useRunProgress(initialScenario: string, skipShift: boolean = false) {
  const [state, setState] = useState<RunState>({
    runId: '...',
    workspace: '...',
    startTime: new Date().toISOString(),
    baseline: '...',
    scenario: initialScenario,
    overallStatus: 'INITIALIZING',
    progressPercentage: 0,
    elapsedSeconds: 0,
    completedChecks: 0,
    warningsCount: 0,
    findingsCount: 0,
    stages: JSON.parse(JSON.stringify(INITIAL_STAGES))
  });

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const getCurrentTime = () => new Date().toLocaleTimeString([], { hour12: false });

  useEffect(() => {
    let active = true;

    async function execute() {
      try {
        setState(prev => ({ ...prev, overallStatus: 'IN_PROGRESS', progressPercentage: 10 }));
        const demo = await api.getDemoWorkspace();
        if (!active) return;
        
        setState(prev => ({ ...prev, workspace: demo.name, progressPercentage: 30 }));
        
        const checks = ['DATA_INTEGRITY', 'MODEL_INTEGRITY', 'DISTRIBUTION_SHIFT'];
        
        setState(prev => {
          const st = [...prev.stages];
          st[0].status = 'COMPLETE'; st[0].completionTime = getCurrentTime();
          st[1].status = 'RUNNING'; st[1].startTime = getCurrentTime();
          st[2].status = 'RUNNING'; st[2].startTime = getCurrentTime();
          st[3].status = 'RUNNING'; st[3].startTime = getCurrentTime();
          st[4].status = 'RUNNING'; st[4].startTime = getCurrentTime();
          return { ...prev, stages: st, progressPercentage: 50 };
        });

        const runRes = await api.createRun({
          workspace_id: demo.workspace_id,
          dataset_asset_id: demo.dataset.asset_id,
          model_asset_id: demo.model.asset_id,
          checks,
          configuration: { scenario: initialScenario, thresholds: { shiftThreshold: 0.5 } }
        });
        
        if (!active) return;

        setState(prev => {
          const st = [...prev.stages];
          st[1].status = 'COMPLETE'; st[1].completionTime = getCurrentTime();
          st[2].status = 'COMPLETE'; st[2].completionTime = getCurrentTime();
          st[3].status = 'COMPLETE'; st[3].completionTime = getCurrentTime();
          st[4].status = 'COMPLETE'; st[4].completionTime = getCurrentTime();
          st[5].status = 'COMPLETE'; st[5].completionTime = getCurrentTime();
          st[6].status = 'COMPLETE'; st[6].completionTime = getCurrentTime();
          return {
            ...prev,
            runId: runRes.id,
            overallStatus: runRes.state === 'COMPLETED' ? 'COMPLETED' : 'FAILED',
            progressPercentage: 100,
            completedChecks: checks.length,
            stages: st
          };
        });

      } catch (err) {
        console.error(err);
        setState(prev => ({ ...prev, overallStatus: 'FAILED' }));
      }
    }

    timerRef.current = setInterval(() => {
      setState(prev => {
        if (prev.overallStatus === 'IN_PROGRESS') {
          return { ...prev, elapsedSeconds: prev.elapsedSeconds + 1 };
        }
        return prev;
      });
    }, 1000);

    execute();

    return () => {
      active = false;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [initialScenario, skipShift]);

  const cancelRun = () => {
    setState(prev => ({ ...prev, overallStatus: 'CANCELLED' }));
  };

  const retryFailed = () => {
    // Basic retry
  };

  return { state, cancelRun, retryFailed };
}
