import { ArrowDown } from 'lucide-react';
import type { ProvenanceEntry } from '../../types';
import clsx from 'clsx';

interface LedgerTimelineProps {
  entries: ProvenanceEntry[];
  onSelectEntry: (entry: ProvenanceEntry) => void;
  selectedEntryId?: string;
}

export function LedgerTimeline({ entries, onSelectEntry, selectedEntryId }: LedgerTimelineProps) {
  return (
    <div className="space-y-4 relative">
      {/* Visual chain line */}
      <div className="absolute left-[2.25rem] top-8 bottom-8 w-px bg-white/10" />

      {entries.map((entry, idx) => (
        <div key={entry.runId} className="relative flex items-start group">
          
          <div className="flex-shrink-0 w-20 pt-4 flex flex-col items-center">
            <div className={clsx(
              "w-4 h-4 rounded-full border-2 z-10 transition-colors",
              entry.isValid ? "bg-ng-panel-bg border-status-pass" : "bg-status-fail border-status-fail",
              selectedEntryId === entry.runId && "ring-4 ring-white/10"
            )} />
            {idx !== entries.length - 1 && (
              <ArrowDown className="w-4 h-4 text-white/20 mt-4 group-hover:text-white/40 transition-colors" />
            )}
          </div>

          <div 
            onClick={() => onSelectEntry(entry)}
            className={clsx(
              "flex-1 bg-ng-panel-bg border rounded-lg p-5 cursor-pointer transition-all hover:border-white/30",
              selectedEntryId === entry.runId ? "border-ng-accent bg-black/40" : "border-ng-border"
            )}
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center space-x-3 mb-1">
                  <span className="text-xs font-bold text-white bg-white/10 px-2 py-0.5 rounded">
                    #{String(entry.sequence).padStart(3, '0')}
                  </span>
                  <span className="font-mono text-white text-sm">{entry.runId}</span>
                </div>
                <div className="text-xs text-ng-text-secondary">
                  {new Date(entry.timestamp).toLocaleString()} UTC
                </div>
              </div>
              
              <div className={clsx(
                "flex items-center px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border",
                entry.isValid ? "text-status-pass bg-status-pass/10 border-status-pass/20" : "text-status-fail bg-status-fail/10 border-status-fail/20"
              )}>
                {entry.isValid ? 'VALID' : 'INVALID'}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="bg-black/30 p-2 rounded border border-white/5 truncate">
                <span className="text-ng-text-muted mr-2">Prev:</span>
                <span className="text-ng-text-secondary">{entry.previousHash}</span>
              </div>
              <div className={clsx("bg-black/30 p-2 rounded border border-white/5 truncate", !entry.isValid && "border-status-fail/50 text-status-fail")}>
                <span className="text-ng-text-muted mr-2">Curr:</span>
                <span className={entry.isValid ? "text-white" : "text-status-fail"}>{entry.currentHash}</span>
              </div>
            </div>
          </div>
          
        </div>
      ))}
    </div>
  );
}
