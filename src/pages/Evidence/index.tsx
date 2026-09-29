import { useState, useMemo } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { EvidenceViewer } from '../../components/findings/EvidenceViewer';
import { comprehensiveDemoFindings } from '../../services/demoFindings';
import type { ComprehensiveFinding } from '../../types';
import { Image as ImageIcon } from 'lucide-react';

export function Evidence() {
  const [selectedFinding, setSelectedFinding] = useState<ComprehensiveFinding | null>(null);

  // Flatten all findings that have evidence
  const evidenceList = useMemo(() => {
    return comprehensiveDemoFindings.filter(f => f.evidenceSamples && f.evidenceSamples.length > 0);
  }, []);

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <SectionHeader 
        title="Evidence Gallery"
        description="Inspect supporting artifacts and samples flagged during assurance runs."
      />

      {evidenceList.length === 0 ? (
        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-12 text-center text-ng-text-secondary">
          No visual evidence has been captured in the current run.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {evidenceList.map(finding => {
            const sample = finding.evidenceSamples![0];
            return (
              <div 
                key={finding.id}
                onClick={() => setSelectedFinding(finding)}
                className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-hidden group cursor-pointer hover:border-ng-accent transition-colors flex flex-col"
              >
                <div className="aspect-video bg-black/60 relative flex items-center justify-center overflow-hidden">
                  <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]"></div>
                  {sample.imageUrl ? (
                    <img src={sample.imageUrl} alt={sample.sampleId} className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-500" />
                  ) : (
                    <div className="flex flex-col items-center">
                      <ImageIcon className="w-10 h-10 text-ng-text-muted mb-2 group-hover:scale-110 group-hover:text-ng-accent transition-all" />
                      <span className="text-xs font-mono text-ng-text-muted">Sample Preview</span>
                    </div>
                  )}
                  {/* Overlay */}
                  <div className="absolute inset-0 bg-ng-accent/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="bg-black/80 text-white text-xs font-bold px-3 py-1.5 rounded uppercase tracking-wider shadow-xl">
                      View Gallery ({finding.evidenceSamples!.length})
                    </span>
                  </div>
                </div>
                
                <div className="p-4 flex-1 flex flex-col border-t border-white/5">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-white bg-white/10 px-2 py-0.5 rounded uppercase tracking-wider">{finding.category}</span>
                    <span className="font-mono text-xs text-ng-text-muted">{finding.id}</span>
                  </div>
                  <h3 className="text-sm font-medium text-white mb-2 leading-tight flex-1">{finding.description}</h3>
                  <div className="flex items-center justify-between text-xs mt-auto">
                    <span className="text-ng-text-secondary">{sample.evidenceType}</span>
                    <span className="font-mono text-status-warning font-bold">{sample.score}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedFinding && (
        <EvidenceViewer 
          isOpen={true} 
          onClose={() => setSelectedFinding(null)} 
          finding={selectedFinding} 
        />
      )}
    </div>
  );
}
