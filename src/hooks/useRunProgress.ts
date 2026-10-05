import { useState, useEffect, useRef } from 'react';
import type { RunState, RunStage } from '../types';

const INITIAL_STAGES: RunStage[] = [
  { id: 's1', name: 'Initializing', description: 'Preparing workspace and allocating local resources.', status: 'WAITING' },
  { id: 's2', name: 'Data Integrity', description: 'Validating dataset structure, labels, readability, and duplicates.', status: 'WAITING' },
  { id: 's3', name: 'Model Integrity', description: 'Verifying model artifact identity against registered baseline.', status: 'WAITING' },
  { id: 's4', name: 'Distribution Shift', description: 'Comparing reference and current image batches.', status: 'WAITING' },
  { id: 's5', name: 'Assurance Comparator', description: 'Comparing current findings against baseline.', status: 'WAITING' },
  { id: 's6', name: 'Recording Provenance', description: 'Cryptographically logging execution steps to the local ledger.', status: 'WAITING' },
  { id: 's7', name: 'Finalizing', description: 'Generating reports and cleaning up temporary assets.', status: 'WAITING' }
];

export function useRunProgress(initialScenario: string, skipShift: boolean = false) {
  const [state, setState] = useState<RunState>({
    runId: 'rn_9a2b4c',
    workspace: 'default-ws-01',
    startTime: new Date().toISOString(),
    baseline: 'rn_7e81b0',
    scenario: initialScenario,
    overallStatus: 'INITIALIZING',
    progressPercentage: 0,
    elapsedSeconds: 0,
    completedChecks: 0,
    warningsCount: 0,
    findingsCount: 0,
    stages: JSON.parse(JSON.stringify(INITIAL_STAGES)) // Deep copy
  });

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sequenceRef = useRef<number>(0);

  // Helper to format time
  const getCurrentTime = () => new Date().toLocaleTimeString([], { hour12: false });

  const updateStage = (index: number, updates: Partial<RunStage>) => {
    setState(prev => {
      const newStages = [...prev.stages];
      newStages[index] = { ...newStages[index], ...updates };
      return { ...prev, stages: newStages };
    });
  };

  const executeNextStep = () => {
    const step = sequenceRef.current;
    
    if (state.overallStatus === 'CANCELLED' || state.overallStatus === 'FAILED') {
      return;
    }

    if (step === 0) {
      setState(prev => ({ ...prev, overallStatus: 'IN_PROGRESS' }));
      updateStage(0, { status: 'RUNNING', startTime: getCurrentTime() });
      setTimeout(() => {
        updateStage(0, { status: 'COMPLETE', completionTime: getCurrentTime(), resultSummary: 'Workspace initialized locally.' });
        sequenceRef.current++;
        executeNextStep();
      }, 1500);
      return;
    }

    if (step === 1) {
      updateStage(1, { status: 'RUNNING', startTime: getCurrentTime() });
      setTimeout(() => {
        const isAnomaly = initialScenario === 'DATA_ANOMALY';
        updateStage(1, { 
          status: isAnomaly ? 'WARNING' : 'COMPLETE', 
          completionTime: getCurrentTime(), 
          resultSummary: isAnomaly ? '2 duplicates and 5 missing labels found.' : '1,240 images checked. Valid structure.' 
        });
        setState(prev => ({ 
          ...prev, 
          progressPercentage: 15,
          completedChecks: prev.completedChecks + 1,
          warningsCount: isAnomaly ? prev.warningsCount + 1 : prev.warningsCount,
          findingsCount: isAnomaly ? prev.findingsCount + 2 : prev.findingsCount
        }));
        sequenceRef.current++;
        executeNextStep();
      }, 2000);
      return;
    }

    if (step === 2) {
      updateStage(2, { status: 'RUNNING', startTime: getCurrentTime() });
      setTimeout(() => {
        const isMismatch = initialScenario === 'MODEL_MISMATCH';
        updateStage(2, { 
          status: isMismatch ? 'FAILED' : 'COMPLETE', 
          completionTime: getCurrentTime(), 
          resultSummary: isMismatch ? 'Hash differs from baseline.' : 'Hash matches baseline.',
          errorDetail: isMismatch ? 'SHA-256 hash does not match registered model artifact. Suspected tampering or wrong version.' : undefined
        });
        
        setState(prev => ({ 
          ...prev, 
          progressPercentage: 35,
          completedChecks: prev.completedChecks + 1,
          findingsCount: isMismatch ? prev.findingsCount + 1 : prev.findingsCount,
          overallStatus: isMismatch ? 'FAILED' : prev.overallStatus
        }));
        
        if (!isMismatch) {
          sequenceRef.current++;
          executeNextStep();
        }
      }, 2500);
      return;
    }

    if (step === 3) {
      if (skipShift) {
        updateStage(3, { 
          status: 'SKIPPED', 
          resultSummary: 'Skipped because no current reference batch was configured.' 
        });
        setState(prev => ({ ...prev, progressPercentage: 50 }));
        sequenceRef.current++;
        executeNextStep();
        return;
      }

      updateStage(3, { status: 'RUNNING', startTime: getCurrentTime() });
      setTimeout(() => {
        const isShift = initialScenario === 'DISTRIBUTION_SHIFT';
        updateStage(3, { 
          status: isShift ? 'WARNING' : 'COMPLETE', 
          completionTime: getCurrentTime(), 
          resultSummary: isShift ? 'Covariate shift detected (D-score: 0.45 > 0.30).' : 'Batch within acceptable thresholds.' 
        });
        
        setState(prev => ({ 
          ...prev, 
          progressPercentage: 65,
          completedChecks: prev.completedChecks + 1,
          warningsCount: isShift ? prev.warningsCount + 1 : prev.warningsCount,
          findingsCount: isShift ? prev.findingsCount + 1 : prev.findingsCount
        }));
        sequenceRef.current++;
        executeNextStep();
      }, 3000);
      return;
    }

    if (step === 4) {
      updateStage(4, { status: 'RUNNING', startTime: getCurrentTime() });
      setTimeout(() => {
        updateStage(4, { 
          status: 'COMPLETE', 
          completionTime: getCurrentTime(), 
          resultSummary: 'Metrics compared. 2 new findings since baseline.' 
        });
        setState(prev => ({ 
          ...prev, 
          progressPercentage: 80,
          completedChecks: prev.completedChecks + 1 
        }));
        sequenceRef.current++;
        executeNextStep();
      }, 1500);
      return;
    }

    if (step === 5) {
      updateStage(5, { status: 'RUNNING', startTime: getCurrentTime() });
      setTimeout(() => {
        updateStage(5, { 
          status: 'COMPLETE', 
          completionTime: getCurrentTime(), 
          resultSummary: 'Cryptographic log generated and stored.' 
        });
        setState(prev => ({ ...prev, progressPercentage: 90 }));
        sequenceRef.current++;
        executeNextStep();
      }, 1500);
      return;
    }

    if (step === 6) {
      updateStage(6, { status: 'RUNNING', startTime: getCurrentTime() });
      setTimeout(() => {
        updateStage(6, { 
          status: 'COMPLETE', 
          completionTime: getCurrentTime(), 
          resultSummary: 'Report generated.' 
        });
        setState(prev => ({ 
          ...prev, 
          progressPercentage: 100,
          overallStatus: 'COMPLETED'
        }));
        if (timerRef.current) clearInterval(timerRef.current);
      }, 1000);
      return;
    }
  };

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setState(prev => {
        if (prev.overallStatus === 'IN_PROGRESS') {
          return { ...prev, elapsedSeconds: prev.elapsedSeconds + 1 };
        }
        return prev;
      });
    }, 1000);

    // Start mock execution
    executeNextStep();

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cancelRun = () => {
    setState(prev => ({ ...prev, overallStatus: 'CANCELLED' }));
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const retryFailed = () => {
    setState(prev => ({ ...prev, overallStatus: 'IN_PROGRESS' }));
    executeNextStep();
  };

  return { state, cancelRun, retryFailed };
}
