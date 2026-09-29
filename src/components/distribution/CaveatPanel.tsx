import { ShieldAlert } from 'lucide-react';

interface CaveatPanelProps {
  isControlledDemo: boolean;
  demoConditionName?: string;
}

export function CaveatPanel({ isControlledDemo, demoConditionName }: CaveatPanelProps) {
  return (
    <div className="space-y-4">
      {isControlledDemo && (
        <div className="bg-status-warning/10 border border-status-warning/30 rounded-lg p-5">
          <div className="flex items-center space-x-2 text-status-warning mb-2">
            <ShieldAlert className="w-5 h-5" />
            <h3 className="font-bold text-sm tracking-wide uppercase">
              CONTROLLED DEMO — {demoConditionName}
            </h3>
          </div>
          <p className="text-sm text-status-warning/90 leading-relaxed">
            This scenario intentionally changes image characteristics to demonstrate distribution-shift detection. 
            It is simulated frontend data.
          </p>
        </div>
      )}

      <div className="bg-black/20 border border-white/5 rounded-lg p-5">
        <h3 className="text-sm font-bold text-white mb-3 uppercase tracking-wider text-[11px]">Analysis Caveats</h3>
        <ul className="text-xs text-ng-text-secondary space-y-2 list-disc list-inside">
          <li><strong>Sample Size:</strong> Shift metrics are sensitive to small batch sizes. Ensure inference batches are statistically significant.</li>
          <li><strong>Metric Limitations:</strong> Histogram and KS-test distances measure pixel-level and embedding distributions, but do not guarantee safety.</li>
          <li><strong>Not Malicious:</strong> A "Shift condition detected" alert does not prove malicious adversarial activity. It only indicates a deviation from the reference baseline (e.g. weather changes, camera sensor issues).</li>
        </ul>
      </div>
    </div>
  );
}
