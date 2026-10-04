import { useState, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { EvidenceViewer } from '../../components/findings/EvidenceViewer';
import { api } from '../../services/api';
import type { ComprehensiveFinding } from '../../types';
import { Image as ImageIcon } from 'lucide-react';

export function Evidence() {
  const [selectedFinding, setSelectedFinding] = useState<ComprehensiveFinding | null>(null);
  const [evidenceList, setEvidenceList] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const runs = await api.getRuns();
        if (runs && runs.length > 0) {
          const run = runs[0];
          const rawFindings = await api.getFindings(run.id);
          const rawEvidence = await api.getEvidence(run.id);

          const findingsMap = new Map();
          for (const ev of rawEvidence) {
             const finding = rawFindings.find((f: any) => f.id === ev.finding_id);
             if (!finding) continue;
             
             if (!findingsMap.has(finding.id)) {
               findingsMap.set(finding.id, {
                 id: finding.id,
                 category: finding.category,
                 severity: finding.severity,
                 status: finding.status,
                 description: finding.description,
                 evidenceSamples: []
               });
             }
             
             findingsMap.get(finding.id).evidenceSamples.push({
                id: ev.id,
                sampleId: ev.sample_id,
                evidenceType: 'image',
                imageUrl: ev.asset_reference && ev.sample_id ? `http://localhost:8000/api/assets/${ev.asset_reference}/image/${ev.sample_id}` : null,
                score: ev.observed_value,
                fileHash: ev.metadata ? ev.metadata.hash : undefined
             });
          }
          setEvidenceList(Array.from(findingsMap.values()));
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  if (isLoading) return <div className="p-8 text-white">Loading Evidence...</div>;

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
