import { Copy, Hash, User, Clock, CheckCircle2, GitCommit } from 'lucide-react';
import { useState } from 'react';
import type { ProvenanceEntry } from '../../types';

export function ProvenanceEntryDetails({ entry }: { entry: ProvenanceEntry }) {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const handleCopy = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const HashRow = ({ label, hash }: { label: string, hash: string }) => (
    <div className="flex flex-col mb-4 last:mb-0">
      <span className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-1">{label}</span>
      <div className="flex items-center bg-black/30 p-2 rounded border border-white/5">
        <Hash className="w-3 h-3 text-ng-text-muted mr-2 flex-shrink-0" />
        <span className="font-mono text-sm text-white flex-1 truncate">{hash}</span>
        <button 
          onClick={() => handleCopy(hash)}
          className="ml-2 p-1.5 hover:bg-white/10 rounded transition-colors"
          title="Copy Hash"
        >
          {copiedHash === hash ? <CheckCircle2 className="w-4 h-4 text-status-pass" /> : <Copy className="w-4 h-4 text-ng-text-muted" />}
        </button>
      </div>
    </div>
  );

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-hidden flex flex-col h-full shadow-2xl">
      <div className="p-6 border-b border-white/5 bg-black/20">
        <h2 className="text-lg font-bold text-white mb-1">Entry Details</h2>
        <div className="flex items-center space-x-3 text-sm text-ng-text-secondary">
          <span className="font-mono bg-white/5 px-2 py-0.5 rounded">#{String(entry.sequence).padStart(3, '0')}</span>
          <span className="font-mono">{entry.runId}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {/* Artifact Hashes */}
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 border-b border-white/5 pb-2">Artifact References</h3>
          <HashRow label="Dataset Hash" hash={entry.datasetHash} />
          <HashRow label="Model Artifact Hash" hash={entry.modelHash} />
          <HashRow label="Configuration Hash" hash={entry.configHash} />
          <HashRow label="Findings Summary Hash" hash={entry.summaryHash} />
        </div>

        {/* Ledger Chain */}
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 border-b border-white/5 pb-2">Cryptographic Chain</h3>
          <HashRow label="Previous Entry Hash" hash={entry.previousHash} />
          <HashRow label="Current Entry Hash" hash={entry.currentHash} />
        </div>

        {/* Metadata */}
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 border-b border-white/5 pb-2">Metadata</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center text-white">
              <Clock className="w-4 h-4 text-ng-text-muted mr-3" />
              {new Date(entry.timestamp).toLocaleString()}
            </div>
            <div className="flex items-center text-white">
              <User className="w-4 h-4 text-ng-text-muted mr-3" />
              {entry.actorLabel}
            </div>
            {entry.baselineRunId && (
              <div className="flex flex-col mt-4 p-3 bg-black/20 rounded border border-white/5">
                <div className="text-[10px] uppercase font-bold text-ng-text-muted tracking-wider mb-2">Baseline Relationship</div>
                <div className="flex items-center space-x-2 font-mono text-xs text-white">
                  <span>{entry.baselineRunId}</span>
                  <GitCommit className="w-4 h-4 text-ng-accent" />
                  <span>{entry.runId}</span>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
