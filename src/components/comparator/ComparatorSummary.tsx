import { AlertOctagon, Info } from 'lucide-react';
import type { ComparatorContext } from '../../types';

export function ComparatorSummary({ context }: { context: ComparatorContext }) {
  return (
    <div className="space-y-4">
      <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
        <div className="flex items-start">
          <Info className="w-5 h-5 text-blue-400 mr-3 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-white mb-2 tracking-wide">Comparison Summary</h3>
            <p className="text-sm text-ng-text-secondary leading-relaxed">
              {context.summary}
            </p>
          </div>
        </div>
      </div>

      {context.modelHashChanged && (
        <div className="bg-status-warning/10 border border-status-warning/30 rounded-lg p-6">
          <div className="flex items-start">
            <AlertOctagon className="w-5 h-5 text-status-warning mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-status-warning uppercase tracking-wider mb-2">Model Hash Mismatch</h3>
              <p className="text-sm text-status-warning/90 leading-relaxed">
                Model artifact differs from registered baseline. The hash mismatch is evidence of difference, not proof of malicious intent.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
