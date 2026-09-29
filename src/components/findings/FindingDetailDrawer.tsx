import { X, Copy, ExternalLink, Image as ImageIcon, CheckCircle2, ShieldAlert, GitCommit } from 'lucide-react';
import { useState } from 'react';
import type { ComprehensiveFinding } from '../../types';
import { ExtendedSeverityBadge } from './ExtendedSeverityBadge';
import { EvidenceViewer } from './EvidenceViewer';
import clsx from 'clsx';

interface FindingDetailDrawerProps {
  finding: ComprehensiveFinding | null;
  onClose: () => void;
  onStatusChange: (id: string, newStatus: ComprehensiveFinding['status']) => void;
}

export function FindingDetailDrawer({ finding, onClose, onStatusChange }: FindingDetailDrawerProps) {
  const [copied, setCopied] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);

  if (!finding) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(finding.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasEvidence = finding.evidenceSamples && finding.evidenceSamples.length > 0;

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      
      <div className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-ng-panel-bg border-l border-ng-border z-50 flex flex-col shadow-2xl animate-in slide-in-from-right duration-300">
        
        {/* HEADER */}
        <div className="flex items-center justify-between p-6 border-b border-white/5 bg-black/20">
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-bold text-white font-mono">{finding.id}</h2>
            <button 
              onClick={handleCopy}
              className="p-1.5 text-ng-text-muted hover:text-white bg-black/30 rounded border border-white/10 transition-colors"
              title="Copy Finding ID"
            >
              {copied ? <CheckCircle2 className="w-4 h-4 text-status-pass" /> : <Copy className="w-4 h-4" />}
            </button>
            {finding.isControlledDemo && (
              <span className="flex items-center text-[9px] font-black bg-status-warning text-black px-2 py-0.5 rounded uppercase tracking-widest ml-4">
                <ShieldAlert className="w-3 h-3 mr-1" />
                Prototype Demo
              </span>
            )}
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-ng-text-muted hover:text-white bg-white/5 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* CONTENT */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          <div className="space-y-4">
            <h3 className="text-2xl font-bold text-white">{finding.description}</h3>
            <div className="flex flex-wrap gap-2">
              <ExtendedSeverityBadge severity={finding.severity} className="px-3 py-1 text-xs" />
              <span className={clsx(
                  "px-3 py-1 rounded text-xs font-bold uppercase tracking-wider border",
                  finding.status === 'New' && "text-blue-400 bg-blue-400/10 border-blue-400/20",
                  finding.status === 'Open' && "text-status-warning bg-status-warning/10 border-status-warning/20",
                  finding.status === 'Reviewed' && "text-purple-400 bg-purple-400/10 border-purple-400/20",
                  finding.status === 'Cleared' && "text-status-pass bg-status-pass/10 border-status-pass/20",
                  finding.status === 'NOT RUN' && "text-ng-text-muted bg-white/5 border-white/10"
                )}>
                  Status: {finding.status}
              </span>
              <span className="px-3 py-1 rounded text-xs font-bold text-ng-text-secondary bg-white/5 border border-white/10 uppercase tracking-wider">
                {finding.category}
              </span>
            </div>
            
            {finding.explanation && (
              <p className="text-sm text-ng-text-secondary leading-relaxed mt-4">
                {finding.explanation}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/30 p-4 rounded-lg border border-white/5">
              <div className="text-xs text-ng-text-muted uppercase tracking-wider mb-1">Observed Value</div>
              <div className="text-lg font-mono text-white break-all">{finding.observed}</div>
            </div>
            <div className="bg-black/30 p-4 rounded-lg border border-white/5">
              <div className="text-xs text-ng-text-muted uppercase tracking-wider mb-1">Threshold / Limit</div>
              <div className="text-lg font-mono text-ng-text-secondary break-all">{finding.threshold}</div>
            </div>
          </div>

          {/* METHOD & CERTAINTY */}
          <div className="space-y-4 bg-white/5 rounded-lg border border-white/10 p-5">
            <div>
              <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-1">Test Method</h4>
              <p className="text-sm text-white">{finding.testMethod || 'Standard assurance check.'}</p>
            </div>
            {finding.certainty && (
              <div>
                <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-1">Detection Certainty</h4>
                <div className="inline-flex px-2 py-1 bg-black/40 border border-white/5 rounded text-xs text-white font-mono">
                  {finding.certainty}
                </div>
              </div>
            )}
          </div>

          {/* EVIDENCE SECTION */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider border-b border-white/5 pb-2 flex justify-between items-center">
              <span>Evidence Sample</span>
              {hasEvidence && (
                <span className="text-ng-text-secondary font-mono">{finding.evidenceSamples?.length} samples available</span>
              )}
            </h4>
            
            {hasEvidence ? (
              <div 
                onClick={() => setShowEvidence(true)}
                className="aspect-video bg-black/50 border border-white/10 rounded-lg flex flex-col items-center justify-center text-ng-text-muted relative overflow-hidden group cursor-pointer hover:border-ng-accent transition-colors"
              >
                <ImageIcon className="w-8 h-8 mb-2 opacity-50 group-hover:scale-110 group-hover:text-ng-accent transition-all" />
                <span className="text-xs font-mono">Click to open Evidence Viewer</span>
                <span className="text-[10px] mt-2 bg-black/40 px-2 py-1 rounded">Sample: {finding.evidenceSamples![0].sampleId}</span>
              </div>
            ) : (
              <div className="p-4 bg-black/30 border border-white/5 rounded text-sm text-ng-text-secondary italic text-center">
                No visual evidence samples attached to this finding.
              </div>
            )}
          </div>

          {/* LIMITATIONS & REMEDIATION */}
          <div className="space-y-4">
            {finding.limitations && (
              <div className="p-4 bg-status-warning/5 border border-status-warning/20 rounded-lg">
                <h4 className="text-xs font-bold text-status-warning uppercase tracking-wider mb-1">Limitations</h4>
                <p className="text-sm text-ng-text-secondary leading-relaxed">{finding.limitations}</p>
              </div>
            )}
            
            {finding.remediation && (
              <div className="p-4 bg-status-pass/5 border border-status-pass/20 rounded-lg">
                <h4 className="text-xs font-bold text-status-pass uppercase tracking-wider mb-1">Suggested Remediation</h4>
                <p className="text-sm text-white leading-relaxed">{finding.remediation}</p>
              </div>
            )}
          </div>

          {/* LINKED RUN */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider border-b border-white/5 pb-2">Linked Run Context</h4>
            <div className="grid grid-cols-2 gap-4 text-sm bg-black/20 p-4 rounded border border-white/5">
              <div>
                <div className="text-ng-text-muted text-xs mb-1">Run ID</div>
                <div className="text-white font-mono">{finding.runId}</div>
              </div>
              <div>
                <div className="text-ng-text-muted text-xs mb-1">Baseline Config</div>
                <div className="text-white font-mono flex items-center">
                  <GitCommit className="w-3 h-3 mr-1" />
                  rn_7e81b0
                </div>
              </div>
              <div className="col-span-2">
                <div className="text-ng-text-muted text-xs mb-1">Execution Timestamp</div>
                <div className="text-white font-mono">{new Date(finding.timestamp).toLocaleString()}</div>
              </div>
            </div>
          </div>

        </div>

        {/* ACTIONS */}
        <div className="p-6 border-t border-white/5 bg-ng-dark-bg space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <button 
              onClick={() => onStatusChange(finding.id, finding.status === 'Reviewed' ? 'Open' : 'Reviewed')}
              className={clsx(
                "px-4 py-3 text-white text-sm font-bold rounded transition-colors",
                finding.status === 'Reviewed' 
                  ? "bg-white/10 hover:bg-white/20" 
                  : "bg-ng-accent hover:bg-ng-accent-hover"
              )}
            >
              {finding.status === 'Reviewed' ? 'Mark as Open' : 'Mark Reviewed'}
            </button>
            <button 
              onClick={() => { if(hasEvidence) setShowEvidence(true); }}
              disabled={!hasEvidence}
              className="px-4 py-3 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:hover:bg-white/5 text-white text-sm font-medium rounded transition-colors border border-white/10 flex items-center justify-center"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Evidence Viewer
            </button>
          </div>
        </div>

      </div>

      <EvidenceViewer 
        isOpen={showEvidence} 
        onClose={() => setShowEvidence(false)} 
        finding={finding} 
      />
    </>
  );
}
