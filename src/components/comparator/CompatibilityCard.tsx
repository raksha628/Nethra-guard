import { CheckCircle2, AlertTriangle } from 'lucide-react';
import type { CompatibilityInfo } from '../../types';

export function CompatibilityCard({ compatibility }: { compatibility: CompatibilityInfo }) {
  if (compatibility.isCompatible) {
    return (
      <div className="bg-status-pass/10 border border-status-pass/20 rounded-lg p-5 flex items-center justify-between">
        <div className="flex items-center">
          <CheckCircle2 className="w-5 h-5 text-status-pass mr-3" />
          <div>
            <h3 className="text-sm font-bold text-status-pass tracking-wide uppercase">Compatible</h3>
            <p className="text-xs text-status-pass/80 mt-1">Runs are directly comparable. Dataset, model, and configuration inputs match.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-status-warning/10 border border-status-warning/20 rounded-lg p-5">
      <div className="flex items-start">
        <AlertTriangle className="w-5 h-5 text-status-warning mr-3 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="text-sm font-bold text-status-warning tracking-wide uppercase">Comparison Unavailable</h3>
          <p className="text-sm text-status-warning/90 mt-2 mb-3 leading-relaxed">
            {compatibility.reason || 'Runs are not directly comparable because configuration or evaluation inputs differ.'}
          </p>
          {compatibility.mismatchedFields && (
            <div className="flex flex-wrap gap-2">
              <span className="text-xs font-bold text-status-warning/70 uppercase tracking-wider mt-1">Mismatched Fields:</span>
              {compatibility.mismatchedFields.map(field => (
                <span key={field} className="px-2 py-1 bg-black/40 text-status-warning text-xs font-mono rounded border border-status-warning/20">
                  {field}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
