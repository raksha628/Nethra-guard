import { SeverityBadge } from '../ui/SeverityBadge';
import type { EvidenceSample } from '../../types';

interface EvidenceCardProps {
  evidence: EvidenceSample;
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-hidden group">
      <div className="relative aspect-video w-full overflow-hidden bg-black/40 border-b border-white/5">
        <img 
          src={evidence.imageUrl} 
          alt={evidence.findingType} 
          className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
        />
        <div className="absolute top-2 right-2">
          <SeverityBadge severity={evidence.severity} />
        </div>
      </div>
      
      <div className="p-4 space-y-3">
        <div className="flex justify-between items-start">
          <div className="font-mono text-xs text-white">{evidence.sampleId}</div>
          {evidence.score && (
            <div className="text-xs font-mono text-ng-accent bg-ng-accent/10 px-1.5 py-0.5 rounded">
              {evidence.score}
            </div>
          )}
        </div>
        
        <div className="text-sm font-medium text-white truncate" title={evidence.findingType}>
          {evidence.findingType}
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-black/20 rounded p-2 border border-white/5">
            <div className="text-ng-text-muted mb-1 uppercase tracking-wider text-[10px]">Expected</div>
            <div className="text-ng-text-secondary truncate" title={evidence.expectedLabel}>
              {evidence.expectedLabel}
            </div>
          </div>
          <div className="bg-black/20 rounded p-2 border border-white/5">
            <div className="text-ng-text-muted mb-1 uppercase tracking-wider text-[10px]">Observed</div>
            <div className="text-status-warning truncate" title={evidence.observedLabel}>
              {evidence.observedLabel}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
