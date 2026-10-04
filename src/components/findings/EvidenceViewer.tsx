import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import type { ComprehensiveFinding } from '../../types';

interface EvidenceViewerProps {
  isOpen: boolean;
  onClose: () => void;
  finding: ComprehensiveFinding | null;
}

export function EvidenceViewer({ isOpen, onClose, finding }: EvidenceViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [detailedEvidence, setDetailedEvidence] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'BOTH' | 'PREDICTIONS' | 'GROUND_TRUTH'>('BOTH');

  const imgRef = useRef<HTMLImageElement>(null);
  const [imgDims, setImgDims] = useState({ w: 0, h: 0 });

  useEffect(() => {
    if (!isOpen || !finding || !finding.evidenceSamples || finding.evidenceSamples.length === 0) return;
    const sample = finding.evidenceSamples[currentIndex];
    
    async function loadDetails() {
      setIsLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/runs/${finding!.runId}/evidence/${sample.id}`);
        const data = await res.json();
        setDetailedEvidence(data);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    loadDetails();
  }, [isOpen, finding, currentIndex]);

  if (!isOpen || !finding || !finding.evidenceSamples || finding.evidenceSamples.length === 0) return null;

  const samples = finding.evidenceSamples;
  const currentSample = samples[currentIndex];

  const handleNext = () => setCurrentIndex((prev) => (prev + 1) % samples.length);
  const handlePrev = () => setCurrentIndex((prev) => (prev - 1 + samples.length) % samples.length);

  const predictions = detailedEvidence?.details?.predictions || [];
  const groundTruth = detailedEvidence?.details?.ground_truth || [];
  const provenance = detailedEvidence?.details?.provenance || {};

  return (
    <div className="fixed inset-0 z-[60] flex bg-black/95 backdrop-blur-sm animate-in fade-in duration-200">
      
      {/* MAIN VIEWER */}
      <div className="flex-1 flex flex-col relative">
        <div className="absolute top-4 left-4 z-10 flex items-center space-x-3">
          <button 
            onClick={onClose}
            className="p-2 text-white bg-white/10 hover:bg-white/20 rounded backdrop-blur transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="text-white font-mono text-sm px-3 py-1.5 bg-black/50 rounded backdrop-blur border border-white/10">
            {finding.id} / {currentSample.sampleId}
          </div>
          
          {(predictions.length > 0 || groundTruth.length > 0) && (
            <div className="flex bg-black/50 rounded backdrop-blur border border-white/10 p-1">
              <button onClick={() => setViewMode('BOTH')} className={`px-3 py-1 text-xs font-bold rounded ${viewMode === 'BOTH' ? 'bg-ng-accent text-white' : 'text-ng-text-muted hover:text-white'}`}>BOTH</button>
              <button onClick={() => setViewMode('PREDICTIONS')} className={`px-3 py-1 text-xs font-bold rounded ${viewMode === 'PREDICTIONS' ? 'bg-ng-accent text-white' : 'text-ng-text-muted hover:text-white'}`}>PREDICTIONS</button>
              <button onClick={() => setViewMode('GROUND_TRUTH')} className={`px-3 py-1 text-xs font-bold rounded ${viewMode === 'GROUND_TRUTH' ? 'bg-ng-accent text-white' : 'text-ng-text-muted hover:text-white'}`}>GROUND TRUTH</button>
            </div>
          )}
        </div>

        <div className="flex-1 flex items-center justify-center p-12 relative group">
          <div className="w-full h-full max-w-5xl max-h-[85vh] bg-ng-panel-bg border border-white/10 rounded-lg flex items-center justify-center relative overflow-hidden shadow-2xl">
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]"></div>
            
            {currentSample.imageUrl ? (
              <div className="relative inline-block max-w-full max-h-full">
                <img 
                  ref={imgRef}
                  src={currentSample.imageUrl} 
                  alt={currentSample.sampleId} 
                  className="max-w-full max-h-full object-contain" 
                  onLoad={(e) => {
                    const img = e.currentTarget;
                    setImgDims({ w: img.clientWidth, h: img.clientHeight });
                  }}
                />
                
                {/* SVG Overlay for Bounding Boxes */}
                {imgRef.current && (
                  <svg 
                    className="absolute inset-0 pointer-events-none" 
                    width={imgDims.w} 
                    height={imgDims.h} 
                    viewBox={`0 0 ${imgRef.current.naturalWidth} ${imgRef.current.naturalHeight}`}
                    preserveAspectRatio="none"
                  >
                    {(viewMode === 'BOTH' || viewMode === 'GROUND_TRUTH') && groundTruth.map((gt: any, i: number) => {
                       const [x1, y1, x2, y2] = gt.bbox;
                       return (
                         <g key={`gt-${i}`}>
                           <rect x={x1} y={y1} width={x2-x1} height={y2-y1} fill="none" stroke="#22c55e" strokeWidth="3" />
                           <text x={x1} y={y1 > 20 ? y1 - 5 : y1 + 15} fill="#22c55e" fontSize="16" fontWeight="bold" style={{ textShadow: '1px 1px 2px black' }}>
                             {gt.class}
                           </text>
                         </g>
                       );
                    })}

                    {(viewMode === 'BOTH' || viewMode === 'PREDICTIONS') && predictions.map((p: any, i: number) => {
                       const [x1, y1, x2, y2] = p.bbox;
                       return (
                         <g key={`pred-${i}`}>
                           <rect x={x1} y={y1} width={x2-x1} height={y2-y1} fill="none" stroke="#ef4444" strokeWidth="3" />
                           <text x={x1} y={y1 > 20 ? y1 - 5 : y1 + 15} fill="#ef4444" fontSize="16" fontWeight="bold" style={{ textShadow: '1px 1px 2px black' }}>
                             {p.class} · {p.confidence.toFixed(2)}
                           </text>
                         </g>
                       );
                    })}
                  </svg>
                )}
              </div>
            ) : (
              <div className="text-center">
                <div className="w-32 h-32 border-4 border-dashed border-white/20 rounded-lg flex items-center justify-center mx-auto mb-4 bg-black/40">
                  <span className="text-white/20 font-bold">NO IMAGE</span>
                </div>
                <p className="text-ng-text-secondary font-mono text-xs">Image preview not available for this sample.</p>
              </div>
            )}
          </div>

          {samples.length > 1 && (
            <>
              <button onClick={handlePrev} className="absolute left-8 p-3 bg-black/50 hover:bg-white/10 text-white rounded-full transition-colors opacity-0 group-hover:opacity-100">
                <ChevronLeft className="w-6 h-6" />
              </button>
              <button onClick={handleNext} className="absolute right-8 p-3 bg-black/50 hover:bg-white/10 text-white rounded-full transition-colors opacity-0 group-hover:opacity-100">
                <ChevronRight className="w-6 h-6" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* SIDEBAR */}
      <div className="w-[400px] bg-ng-panel-bg border-l border-white/10 flex flex-col shadow-2xl">
        <div className="p-6 border-b border-white/10">
          <h2 className="text-lg font-bold text-white mb-1">Evidence Traceability</h2>
          <p className="text-xs text-ng-text-secondary">Sample {currentIndex + 1} of {samples.length}</p>
        </div>

        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          {isLoading ? (
            <div className="text-white text-sm">Loading evidence lineage...</div>
          ) : (
            <>
              <div>
                <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Finding</div>
                <div className="text-sm font-bold text-status-warning">{provenance.finding || finding.findingType}</div>
              </div>
              
              <div>
                <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Evidence Reference</div>
                <div className="inline-flex px-2 py-1 bg-white/5 border border-white/10 text-xs text-white rounded font-medium">
                  {provenance.evidence || currentSample.evidenceType}
                </div>
              </div>

              <div>
                <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Dataset</div>
                <div className="text-sm text-white font-mono">{provenance.dataset || 'N/A'}</div>
              </div>

              <div>
                <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Model</div>
                <div className="text-sm text-white font-mono">{provenance.model || 'N/A'}</div>
              </div>

              <div>
                <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Run ID</div>
                <div className="text-xs font-mono text-white break-all">{provenance.run || finding.runId}</div>
              </div>

              {(predictions.length > 0 || groundTruth.length > 0) && (
                <div className="border-t border-white/10 pt-4 mt-4">
                  <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-3">Annotation Legend</div>
                  <div className="space-y-3">
                    {predictions.length > 0 && (
                      <div className="flex items-start">
                        <div className="w-3 h-3 rounded-full bg-red-500 mt-1 mr-2 flex-shrink-0"></div>
                        <div className="text-xs text-white">
                          <span className="font-bold">Model Predictions ({predictions.length})</span>
                          <p className="text-ng-text-muted mt-1 text-[10px]">Predicted by YOLOv8 Nano ONNX. Values indicate class and confidence score.</p>
                        </div>
                      </div>
                    )}
                    {groundTruth.length > 0 && (
                      <div className="flex items-start">
                        <div className="w-3 h-3 rounded-full bg-green-500 mt-1 mr-2 flex-shrink-0"></div>
                        <div className="text-xs text-white">
                          <span className="font-bold">Ground Truth ({groundTruth.length})</span>
                          <p className="text-ng-text-muted mt-1 text-[10px]">Reference COCO JSON annotation.</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
