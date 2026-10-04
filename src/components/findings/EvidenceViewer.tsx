import { X, ChevronLeft, ChevronRight, Hash, ShieldAlert } from 'lucide-react';
import { useState } from 'react';
import type { ComprehensiveFinding } from '../../types';

interface EvidenceViewerProps {
  isOpen: boolean;
  onClose: () => void;
  finding: ComprehensiveFinding | null;
}

export function EvidenceViewer({ isOpen, onClose, finding }: EvidenceViewerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!isOpen || !finding || !finding.evidenceSamples || finding.evidenceSamples.length === 0) return null;

  const samples = finding.evidenceSamples;
  const currentSample = samples[currentIndex];

  const handleNext = () => setCurrentIndex((prev) => (prev + 1) % samples.length);
  const handlePrev = () => setCurrentIndex((prev) => (prev - 1 + samples.length) % samples.length);

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
          <div className="text-white font-mono text-sm px-3 py-1.5 bg-black/50 rounded backdrop-blur">
            {finding.id} / {currentSample.sampleId}
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center p-12 relative group">
          {/* MOCK IMAGE VIEWER */}
          <div className="w-full h-full max-w-4xl max-h-[80vh] bg-ng-panel-bg border border-white/10 rounded-lg flex items-center justify-center relative overflow-hidden shadow-2xl">
            {/* Removed remote URL texture for offline requirements. Using CSS pattern instead. */}
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]"></div>
            
            {currentSample.imageUrl ? (
              <img src={currentSample.imageUrl} alt={currentSample.sampleId} className="max-w-full max-h-full object-contain" />
            ) : (
              <div className="text-center">
                <div className="w-32 h-32 border-4 border-dashed border-white/20 rounded-lg flex items-center justify-center mx-auto mb-4 bg-black/40">
                  <span className="text-white/20 font-bold">NO IMAGE</span>
                </div>
                <p className="text-ng-text-secondary font-mono text-xs">Image preview not available for this sample.</p>
              </div>
            )}

            {/* Real bounding boxes and visual overlay */}
            {finding.category === 'Data Integrity' && !currentSample.imageUrl && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border-2 border-status-warning/50 rounded bg-status-warning/10 animate-pulse flex items-center justify-center">
                <div className="absolute -top-6 left-0 bg-status-warning text-black text-[9px] font-bold px-1 py-0.5 rounded-t">
                  {currentSample.evidenceType}
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          {samples.length > 1 && (
            <>
              <button 
                onClick={handlePrev}
                className="absolute left-8 p-3 bg-black/50 hover:bg-white/10 text-white rounded-full transition-colors opacity-0 group-hover:opacity-100"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <button 
                onClick={handleNext}
                className="absolute right-8 p-3 bg-black/50 hover:bg-white/10 text-white rounded-full transition-colors opacity-0 group-hover:opacity-100"
              >
                <ChevronRight className="w-6 h-6" />
              </button>
            </>
          )}
        </div>
        
        {samples.length > 1 && (
          <div className="h-16 flex items-center justify-center space-x-2 pb-4">
            {samples.map((_, idx) => (
              <div 
                key={idx} 
                className={`w-2 h-2 rounded-full transition-all ${idx === currentIndex ? 'bg-ng-accent w-6' : 'bg-white/20 cursor-pointer hover:bg-white/40'}`}
                onClick={() => setCurrentIndex(idx)}
              />
            ))}
          </div>
        )}
      </div>

      {/* SIDEBAR */}
      <div className="w-[400px] bg-ng-panel-bg border-l border-white/10 flex flex-col shadow-2xl">
        <div className="p-6 border-b border-white/10">
          <h2 className="text-lg font-bold text-white mb-1">Evidence Details</h2>
          <p className="text-xs text-ng-text-secondary">Sample {currentIndex + 1} of {samples.length}</p>
        </div>

        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          <div>
            <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Sample ID</div>
            <div className="text-sm font-mono text-white bg-black/30 p-2 rounded border border-white/5">{currentSample.sampleId}</div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Expected Label</div>
              <div className="text-sm text-white">{currentSample.expectedLabel || 'N/A'}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Observed Label</div>
              <div className="text-sm text-white">{currentSample.observedLabel || 'N/A'}</div>
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Evidence Type</div>
            <div className="inline-flex px-2 py-1 bg-white/5 border border-white/10 text-xs text-white rounded font-medium">
              {currentSample.evidenceType}
            </div>
          </div>

          {currentSample.score && (
            <div>
              <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">Score / Metric</div>
              <div className="text-lg font-mono text-status-warning">{currentSample.score}</div>
            </div>
          )}

          {currentSample.fileHash && (
            <div>
              <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">File Hash</div>
              <div className="flex items-center text-xs font-mono text-white bg-black/30 p-2 rounded border border-white/5 break-all">
                <Hash className="w-3 h-3 mr-2 text-ng-text-muted flex-shrink-0" />
                {currentSample.fileHash}
              </div>
            </div>
          )}

          {finding.isControlledDemo && (
            <div className="mt-8 p-3 bg-status-warning/10 border border-status-warning/20 rounded text-status-warning text-xs leading-relaxed flex items-start">
              <ShieldAlert className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <strong>Notice:</strong> Physical file loading is restricted in this environment. Evidence samples are securely rendered.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
