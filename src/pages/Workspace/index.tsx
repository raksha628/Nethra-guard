

import { SectionHeader } from '../../components/ui/SectionHeader';

export function Workspace() {
  

  return (
    <div className="space-y-8 max-w-[1200px] pb-12">
      <SectionHeader 
        title="Model Integrity & Workspace"
        description="Verify model artifact identity and manage assurance assets."
      />
      
      <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6 mb-8 text-sm text-ng-text-secondary">
        <h3 className="text-white font-bold text-base mb-2">Model Artifact Identity</h3>
        <ul className="list-none space-y-1 mb-4 text-white font-mono">
          <li>Filename: detector.onnx</li>
          <li>Format: ONNX</li>
          <li>Architecture: YOLOv8 Nano</li>
          <li>SHA-256: 8005c3dd5226bee1e7e080e909f163a466002bf375bf8e97892742ef296ba6e1</li>
          <li>Adapter: ONNXModelAdapter</li>
          <li>Runtime: ONNX Runtime</li>
          <li>Integrity: VERIFIED</li>
        </ul>
        <p>The hash provides a deterministic identity for the evaluated model artifact. It proves artifact identity and integrity relative to the recorded hash. It does not prove the model is safe or accurate.</p>
      </div>

      <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6 mb-8 text-sm text-ng-text-secondary">
        <h3 className="text-white font-bold text-base mb-2">Assurance Data Assets</h3>
        <ul className="list-none space-y-1 mb-4 text-white font-mono">
          <li>Dataset: Ultralytics COCO128</li>
          <li>Format: COCO JSON</li>
          <li>SHA-256: 9271814fce81bb7455c86dbfa992c1c309b54aba3031ba1b4e943c6221b0af93</li>
          <li>Integrity: VERIFIED</li>
        </ul>
      </div>
    </div>
  );
}
