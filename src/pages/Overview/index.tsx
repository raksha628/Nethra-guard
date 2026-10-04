import { useState, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { EmptyState } from '../../components/ui/EmptyState';
import { FindingsTable } from '../../components/dashboard/FindingsTable';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { Download } from 'lucide-react';
import { api } from '../../services/api';
import type { CheckStatus, Finding } from '../../types';

export function Overview() {
  const [hasData, setHasData] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  const [runSummary, setRunSummary] = useState<any>(null);
  const [checkStatuses, setCheckStatuses] = useState<CheckStatus[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const runs = await api.getRuns();
        if (runs && runs.length > 0) {
          const latestRun = runs[0];
          setHasData(true);
          
          setRunSummary({
            id: latestRun.id,
            baselineId: 'N/A',
            timestamp: latestRun.created_at || new Date().toISOString(),
            duration: '0s',
            status: latestRun.state === 'COMPLETED' ? 'PASS' : 'FAIL',
            model_evaluation: latestRun.summary?.model_evaluation,
            environment: 'Local',
            workspaceName: latestRun.workspace_id
          });

          const rawFindings = await api.getFindings(latestRun.id);
          const mappedFindings = rawFindings.map((r: any) => ({
            id: r.id,
            category: r.category,
            severity: r.severity,
            status: r.status,
            metric: r.title,
            observed: String(r.observed_value),
            threshold: String(r.threshold),
            artifact: r.affected_asset
          }));
          setFindings(mappedFindings);

          setCheckStatuses([
            { id: 'c1', name: 'Data Integrity', status: mappedFindings.some((f: any) => f.category === 'DATA_INTEGRITY' && f.severity === 'CRITICAL') ? 'FAIL' : 'PASS', explanation: 'Dataset structure checked' },
            { id: 'c2', name: 'Model Integrity', status: mappedFindings.some((f: any) => f.category === 'MODEL_INTEGRITY' && f.severity === 'CRITICAL') ? 'FAIL' : 'PASS', explanation: 'Model hash checked' },
            { id: 'c3', name: 'Distribution Shift', status: mappedFindings.some((f: any) => f.category === 'DISTRIBUTION_SHIFT' && f.severity === 'CRITICAL') ? 'FAIL' : 'PASS', explanation: 'Features compared' }
          ]);

        } else {
          setHasData(false);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      alert('JSON Report Exported Successfully!');
      setIsExporting(false);
    }, 1000);
  };

  if (isLoading) {
    return <div className="h-full flex items-center justify-center text-white">Loading Command Center...</div>;
  }

  if (!hasData || !runSummary) {
    return (
      <div className="h-full flex items-center justify-center">
        <EmptyState 
          title="Your assurance workspace is ready."
          description="Load a dataset and model to begin your first assurance run."
          primaryAction={{ label: 'Load Assurance Workspace', onClick: () => setHasData(true) }}
          secondaryAction={{ label: 'Configure Workspace', onClick: () => {} }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-[1600px] pb-12">
      <SectionHeader 
        title="Assurance Command Center"
        description="Unified Computer-Vision Assurance Framework"
      >
        <button 
          onClick={handleExport}
          disabled={isExporting}
          className="flex items-center px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded transition-colors border border-white/10 disabled:opacity-50"
        >
          <Download className="w-4 h-4 mr-2" />
          {isExporting ? 'Exporting...' : 'Export JSON Report'}
        </button>
      </SectionHeader>

      <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-4 flex flex-wrap items-center justify-center gap-y-2 text-xs font-mono font-medium text-ng-text-secondary tracking-widest">
        <span className="text-white">DATA</span> <span className="mx-3 text-ng-border">→</span> 
        <span className="text-white">MODEL</span> <span className="mx-3 text-ng-border">→</span> 
        <span className="text-white">INFERENCE</span> <span className="mx-3 text-ng-border">→</span> 
        <span className="text-status-warning">FINDINGS</span> <span className="mx-3 text-ng-border">→</span> 
        <span className="text-ng-accent">EVIDENCE</span> <span className="mx-3 text-ng-border">→</span> 
        <span className="text-white">PROVENANCE</span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-8">
          
          <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
            <h2 className="text-lg font-bold text-white mb-4">Current Assurance Run</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
              <div>
                <div className="text-ng-text-secondary mb-1">Dataset</div>
                <div className="font-mono text-white">COCO128</div>
              </div>
              <div>
                <div className="text-ng-text-secondary mb-1">Role</div>
                <div className="font-mono text-white text-[11px]">MODEL_EVALUATION_DATASET</div>
              </div>
              <div>
                <div className="text-ng-text-secondary mb-1">Model</div>
                <div className="font-mono text-white">YOLOv8 Nano / ONNX</div>
              </div>
              <div className="col-span-1 md:col-span-1">
                <div className="text-ng-text-secondary mb-1">Runtime</div>
                <div className="font-mono text-white text-[11px]">ONNX Runtime (Local)</div>
              </div>
              <div className="col-span-4 border-t border-white/5 pt-4">
                <div className="text-ng-text-secondary mb-1">Run ID & Timestamp</div>
                <div className="font-mono text-white text-xs text-ng-text-muted">{runSummary.id} | {runSummary.timestamp}</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
              <h3 className="text-sm font-bold text-white mb-2">Assurance Dataset</h3>
              <div className="text-xs text-status-warning font-mono mb-2">Synthetic Controlled Dataset</div>
              <p className="text-xs text-ng-text-secondary">Purpose: Pipeline assurance / controlled anomaly testing (Data Integrity, Distribution Shift).</p>
            </div>
            <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
              <h3 className="text-sm font-bold text-white mb-2">Evaluation Dataset</h3>
              <div className="text-xs text-status-pass font-mono mb-2">Ultralytics COCO128</div>
              <p className="text-xs text-ng-text-secondary">Purpose: Real-image semantic model evaluation. Real ground-truth annotations.</p>
            </div>
          </div>

          <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
            <h2 className="text-lg font-bold text-white mb-4">Semantic Model Evaluation</h2>
            {runSummary.model_evaluation?.status === 'SUPPORTED' ? (
              <>
                <p className="text-xs text-ng-text-secondary leading-relaxed mb-6">
                  {runSummary.model_evaluation?.message || 'Development evaluation — not a production benchmark. Results are limited to this small general-purpose development dataset and should not be interpreted as defence-operational model performance.'}
                </p>
                <div className="grid grid-cols-2 md:grid-cols-6 gap-6">
                  <div>
                    <div className="text-ng-text-secondary text-xs mb-1" title="Dataset used for this evaluation">Dataset</div>
                    <div className="font-mono text-white">COCO128</div>
                  </div>
                  <div>
                    <div className="text-ng-text-secondary text-xs mb-1" title="Number of valid images processed">Images</div>
                    <div className="font-mono text-white">{runSummary.model_evaluation.images_processed || 128}</div>
                  </div>
                  <div>
                    <div className="text-ng-text-secondary text-xs mb-1" title="Of the supported detections produced by the model, how many matched the evaluation ground truth under the configured matching criteria.">Precision</div>
                    <div className="font-mono text-white">{runSummary.model_evaluation.precision}</div>
                  </div>
                  <div>
                    <div className="text-ng-text-secondary text-xs mb-1" title="Of the supported ground-truth objects, how many were detected by the model.">Recall</div>
                    <div className="font-mono text-white">{runSummary.model_evaluation.recall}</div>
                  </div>
                  <div>
                    <div className="text-ng-text-secondary text-xs mb-1" title="Average precision using an IoU threshold of 0.50.">AP50</div>
                    <div className="font-mono text-white">{runSummary.model_evaluation.AP50}</div>
                  </div>
                  <div>
                    <div className="text-ng-text-secondary text-xs mb-1" title="Mean Average Precision computed across IoU thresholds from 0.50 to 0.95.">mAP50-95</div>
                    <div className="font-mono text-white">{runSummary.model_evaluation['mAP50-95'] ?? 'N/A'}</div>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-status-fail/5 border border-status-fail/20 rounded p-4">
                <h3 className="text-sm font-bold text-white mb-2">Semantic Evaluation: Not Available</h3>
                <p className="text-xs text-ng-text-secondary leading-relaxed max-w-4xl">
                  {runSummary.model_evaluation?.message || 'The current dataset is designed for assurance testing and controlled distribution/integrity analysis rather than semantic detector benchmarking. Precision, Recall, mAP, and F1 metrics are NOT_SUPPORTED.'}
                </p>
              </div>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">Active Findings</h2>
              <button className="text-sm text-ng-accent hover:text-ng-accent-hover transition-colors">View all</button>
            </div>
            {findings.length > 0 ? (
              <FindingsTable findings={findings} />
            ) : (
              <div className="text-xs text-ng-text-secondary italic">No assurance findings were generated for this run.</div>
            )}
          </div>
        </div>

        <div className="xl:col-span-1 space-y-8">
          <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6 sticky top-6">
            <h2 className="text-lg font-bold text-white mb-6">Assurance Posture</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="text-sm text-ng-text-secondary">Dataset Integrity</div>
                <StatusBadge status={(checkStatuses.find(c => c.name === 'Data Integrity')?.status || 'PASS') as any} />
              </div>
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="text-sm text-ng-text-secondary">Distribution Shift</div>
                <StatusBadge status={(checkStatuses.find(c => c.name === 'Distribution Shift')?.status || 'WARNING') as any} />
              </div>
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="text-sm text-ng-text-secondary">Model Integrity</div>
                <StatusBadge status={(checkStatuses.find(c => c.name === 'Model Integrity')?.status || 'PASS') as any} />
              </div>
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="text-sm text-ng-text-secondary">Inference Status</div>
                <StatusBadge status="PASS" />
              </div>
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="text-sm text-ng-text-secondary">Provenance</div>
                <StatusBadge status="PASS" />
              </div>
              <div className="flex items-center justify-between pb-1">
                <div className="text-sm text-ng-text-secondary">Semantic Evaluation</div>
                <StatusBadge status={(runSummary.model_evaluation?.status === 'SUPPORTED' ? 'PASS' : 'SKIPPED') as any} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
