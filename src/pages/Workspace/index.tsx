import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, ShieldAlert, AlertCircle } from 'lucide-react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { EmptyState } from '../../components/ui/EmptyState';
import { AssetDropzone } from '../../components/workspace/AssetDropzone';
import { AssetCard } from '../../components/workspace/AssetCard';
import { BaselineSelector } from '../../components/workspace/BaselineSelector';
import { WorkspaceSummary } from '../../components/workspace/WorkspaceSummary';
import { ConfirmationDialog } from '../../components/ui/ConfirmationDialog';
import type { AssetItem } from '../../types';

export function Workspace() {
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<AssetItem | null>(null);
  const [model, setModel] = useState<AssetItem | null>(null);
  const [baseline, setBaseline] = useState<any | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const isWorkspaceEmpty = !dataset && !model && !baseline;

  const loadDemoWorkspace = () => {
    setDataset({
      id: 'ds_demo_01',
      name: 'vehicle_classification_v1.zip',
      type: 'DATASET',
      format: 'COCO JSON',
      size: '142 MB',
      hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      registeredAt: new Date().toISOString(),
      status: 'READY'
    });
    setModel({
      id: 'md_demo_01',
      name: 'yolov8_vehicle_detect.pt',
      type: 'MODEL',
      format: 'PyTorch',
      size: '86 MB',
      hash: '8f91893c5d808fa7a42c2b3e8ab802d3809fb0fa4b1b3699b6eb8b7c7e5fc7bb',
      registeredAt: new Date().toISOString(),
      status: 'READY'
    });
    setBaseline({
      id: 'rn_7e81b0',
      timestamp: '2026-09-27T10:00:00Z',
      datasetHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      modelHash: 'c4e3a1...f02b'
    });
  };

  const handleClear = () => {
    setDataset(null);
    setModel(null);
    setBaseline(null);
    setShowClearConfirm(false);
  };

  return (
    <div className="space-y-8 max-w-[1200px] pb-12">
      <SectionHeader 
        title="Workspace Setup"
        description="Register the computer-vision assets used for assurance analysis."
      >
        <div className="flex items-center space-x-2 text-xs font-semibold px-2 py-1 bg-status-warning/10 text-status-warning border border-status-warning/20 rounded uppercase tracking-wider">
          <AlertCircle className="w-3.5 h-3.5 mr-1" />
          DEMO / MOCK DATA
        </div>
      </SectionHeader>

      {/* SECTION 1 — DEMO WORKSPACE */}
      {isWorkspaceEmpty && (
        <div className="bg-ng-accent/10 border border-ng-accent/20 rounded-lg p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <PlayCircle className="w-24 h-24 text-ng-accent" />
          </div>
          <div className="relative z-10">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center">
              Recommended for Prototype Demo
            </h3>
            <p className="text-sm text-ng-text-secondary max-w-xl mb-6">
              Load the bundled NETRA-Guard sample workspace with a known-good baseline and controlled scenarios. No internet connection or cloud account is required for the prototype.
            </p>
            <button 
              onClick={loadDemoWorkspace}
              className="px-6 py-2.5 bg-ng-accent hover:bg-ng-accent-hover text-white text-sm font-bold rounded shadow-lg shadow-ng-accent/20 transition-all"
            >
              Load Demo Workspace
            </button>
          </div>
        </div>
      )}

      {!isWorkspaceEmpty && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-2 space-y-8">
            {/* SECTION 2 — ASSET REGISTRATION */}
            <div>
              <h2 className="text-lg font-bold text-white mb-4">Dataset</h2>
              {dataset ? (
                <AssetCard asset={dataset} onRemove={() => setDataset(null)} />
              ) : (
                <AssetDropzone label="Dataset" accept="COCO JSON / YOLO dataset" />
              )}
            </div>

            <div>
              <h2 className="text-lg font-bold text-white mb-4">Model</h2>
              {model ? (
                <AssetCard asset={model} onRemove={() => setModel(null)} />
              ) : (
                <AssetDropzone 
                  label="Model Artifact" 
                  accept="Configured model adapter (Example targets: YOLO / ONNX / PyTorch / TorchScript)" 
                />
              )}
            </div>

            <div>
              <h2 className="text-lg font-bold text-white mb-4">Baseline Comparison</h2>
              <BaselineSelector 
                selected={baseline} 
                onSelect={() => {
                  setBaseline({
                    id: 'rn_7e81b0',
                    timestamp: '2026-09-27T10:00:00Z',
                    datasetHash: 'e3b0c442...b855',
                    modelHash: 'c4e3a1...f02b'
                  });
                }} 
              />
            </div>
          </div>

          <div className="xl:col-span-1 space-y-6">
            {/* SECTION 3 — WORKSPACE SUMMARY */}
            <div className="sticky top-6 space-y-6">
              <WorkspaceSummary 
                dataset={dataset} 
                model={model} 
                baselineSelected={!!baseline} 
              />

              {/* SECTION 4 — ASSET VALIDATION */}
              <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
                <h3 className="text-sm font-bold tracking-wide text-white mb-4">Asset Validation</h3>
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-ng-text-muted uppercase mb-1">Dataset</div>
                    <div className="text-sm text-white font-medium">
                      {dataset ? "Ready for integrity checks" : "NOT READY"}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-ng-text-muted uppercase mb-1">Model</div>
                    <div className="text-sm text-white font-medium">
                      {model ? "Ready for integrity checks" : "NOT READY"}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-ng-text-muted uppercase mb-1">Baseline</div>
                    <div className="text-sm text-white font-medium">
                      {baseline ? "Baseline selected" : "NOT READY"}
                    </div>
                  </div>
                </div>
              </div>

              {/* FILE SAFETY UI */}
              <div className="flex items-start space-x-3 p-4 bg-status-warning/10 border border-status-warning/20 rounded-lg text-sm text-status-warning">
                <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <p>
                  Uploaded datasets and model files are treated as untrusted assets. 
                  Files are processed locally by the assurance backend.
                </p>
              </div>

              {/* SECTION 5 — WORKSPACE ACTIONS */}
              <div className="space-y-3">
                <button 
                  onClick={() => navigate('/run-assurance')}
                  disabled={!dataset || !model}
                  className="w-full px-4 py-3 bg-ng-accent hover:bg-ng-accent-hover disabled:bg-ng-border disabled:text-ng-text-muted text-white text-sm font-bold rounded transition-colors"
                >
                  Continue to Run Configuration
                </button>
                <div className="flex space-x-3">
                  <button 
                    disabled={!dataset && !model}
                    className="flex-1 px-4 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-50 text-white text-xs font-medium rounded transition-colors border border-white/10"
                  >
                    Register Assets
                  </button>
                  <button 
                    onClick={() => setShowClearConfirm(true)}
                    className="flex-1 px-4 py-2 bg-status-fail/10 hover:bg-status-fail/20 text-status-fail text-xs font-medium rounded transition-colors border border-status-fail/20"
                  >
                    Clear Workspace
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {isWorkspaceEmpty && (
        <div className="mt-8">
          <EmptyState 
            title="Start with Demo Workspace"
            description="The prototype environment supports immediate exploration using bundled mock data."
            primaryAction={{ label: 'Load Demo Workspace', onClick: loadDemoWorkspace }}
          />
        </div>
      )}

      <ConfirmationDialog 
        isOpen={showClearConfirm}
        title="Clear Workspace?"
        message="This will unregister your dataset, model, and baseline selection. Local files will not be deleted."
        onConfirm={handleClear}
        onCancel={() => setShowClearConfirm(false)}
      />
    </div>
  );
}
