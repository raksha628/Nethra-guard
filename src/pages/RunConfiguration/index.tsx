import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SectionHeader } from '../../components/ui/SectionHeader';

export function RunConfiguration() {
  const navigate = useNavigate();
  
  const [selectedDataset, setSelectedDataset] = useState('model_evaluation');
  const [isExecuting, setIsExecuting] = useState(false);

  const handleStartRun = () => {
    setIsExecuting(true);
    // Move to next step or mock start
    setTimeout(() => {
      navigate('/run-progress');
    }, 500);
  };

  return (
    <div className="space-y-8 max-w-[1200px] pb-12">
      <SectionHeader 
        title="Execute Assurance Run"
        description="Configure your dataset and model settings for the assurance pipeline."
      />

      <div className="grid grid-cols-1 gap-8">
        {/* Step 1: Dataset */}
        <section className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
          <div className="flex items-center mb-6">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white/5 border border-white/10 text-white font-bold mr-4">1</div>
            <h2 className="text-lg font-bold text-white">Select Dataset</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 ml-12">
            <div 
              onClick={() => setSelectedDataset('assurance')}
              className={`border rounded-lg p-5 cursor-pointer transition-colors ${selectedDataset === 'assurance' ? 'bg-ng-accent/10 border-ng-accent' : 'bg-black/20 border-white/10 hover:border-white/30'}`}
            >
              <h3 className="text-sm font-bold text-white mb-2">Assurance Dataset</h3>
              <div className="text-xs text-status-warning font-mono mb-2">workspace/synthetic_cv/</div>
              <p className="text-xs text-ng-text-secondary leading-relaxed">
                Synthetic controlled data used for testing pipeline integrity, distribution shift, and anomaly detection. Not for semantic evaluation.
              </p>
            </div>
            
            <div 
              onClick={() => setSelectedDataset('model_evaluation')}
              className={`border rounded-lg p-5 cursor-pointer transition-colors ${selectedDataset === 'model_evaluation' ? 'bg-ng-accent/10 border-ng-accent' : 'bg-black/20 border-white/10 hover:border-white/30'}`}
            >
              <h3 className="text-sm font-bold text-white mb-2">Model Evaluation Dataset</h3>
              <div className="text-xs text-status-pass font-mono mb-2">Ultralytics COCO128</div>
              <p className="text-xs text-ng-text-secondary leading-relaxed">
                Real photographic data with ground-truth COCO JSON annotations. Used for genuine semantic model evaluation.
              </p>
            </div>
          </div>
        </section>

        {/* Step 2: Model */}
        <section className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
          <div className="flex items-center mb-6">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white/5 border border-white/10 text-white font-bold mr-4">2</div>
            <h2 className="text-lg font-bold text-white">Select Model</h2>
          </div>
          <div className="ml-12 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`border rounded-lg p-5 transition-colors bg-ng-accent/10 border-ng-accent`}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-sm font-bold text-white mb-1">YOLOv8 Nano ONNX</h3>
                  <div className="text-xs text-ng-text-muted font-mono mb-3">detector.onnx</div>
                </div>
                <div className="text-[10px] bg-ng-accent/20 text-ng-accent px-2 py-1 rounded">PRE-TRAINED</div>
              </div>
              <p className="text-xs text-ng-text-secondary">
                Real pretrained general-purpose detector. Evaluated via genuine ONNX Runtime offline inference.
              </p>
            </div>
          </div>
        </section>

        {/* Step 3: Review Configuration */}
        <section className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
          <div className="flex items-center mb-6">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white/5 border border-white/10 text-white font-bold mr-4">3</div>
            <h2 className="text-lg font-bold text-white">Review Configuration</h2>
          </div>
          <div className="ml-12 grid grid-cols-2 md:grid-cols-4 gap-6 bg-black/20 rounded border border-white/5 p-5">
            <div>
              <div className="text-xs text-ng-text-secondary mb-1">Input Dimensions</div>
              <div className="text-sm font-mono text-white">640 × 640 RGB</div>
            </div>
            <div>
              <div className="text-xs text-ng-text-secondary mb-1">Confidence Threshold</div>
              <div className="text-sm font-mono text-white">0.25</div>
            </div>
            <div>
              <div className="text-xs text-ng-text-secondary mb-1">NMS IoU</div>
              <div className="text-sm font-mono text-white">0.45</div>
            </div>
            <div>
              <div className="text-xs text-ng-text-secondary mb-1">Runtime</div>
              <div className="text-sm font-mono text-white">ONNX Runtime</div>
            </div>
          </div>
        </section>

        {/* Execution */}
        <div className="flex justify-end pt-4">
          <button
            onClick={handleStartRun}
            disabled={isExecuting}
            className="px-8 py-4 bg-ng-accent hover:bg-ng-accent-hover text-white font-bold rounded-lg transition-colors flex items-center shadow-lg disabled:opacity-50"
          >
            {isExecuting ? 'Starting Pipeline...' : 'Step 4: Execute Assurance Run'}
          </button>
        </div>

      </div>
    </div>
  );
}
