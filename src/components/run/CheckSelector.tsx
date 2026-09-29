import { CheckSquare, Square, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';
import type { AssuranceCheckConfig } from '../../types';

interface CheckSelectorProps {
  check: AssuranceCheckConfig;
  onToggle: (id: string, enabled: boolean) => void;
}

export function CheckSelector({ check, onToggle }: CheckSelectorProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={clsx(
      "border rounded-lg transition-colors overflow-hidden",
      check.enabled ? "bg-ng-panel-bg border-ng-accent/50" : "bg-black/20 border-white/10 opacity-70"
    )}>
      <div 
        className="flex items-center p-4 cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => onToggle(check.id, !check.enabled)}
      >
        <div className="mr-4 text-ng-accent">
          {check.enabled ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5 text-ng-text-muted" />}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className={clsx("font-bold text-sm", check.enabled ? "text-white" : "text-ng-text-muted")}>
              {check.name}
            </h3>
            {check.enabled ? (
              <span className="text-xs font-semibold text-status-pass bg-status-pass/10 px-2 py-0.5 rounded border border-status-pass/20">
                ENABLED
              </span>
            ) : (
              <span className="text-xs font-semibold text-ng-text-muted bg-white/5 px-2 py-0.5 rounded border border-white/10">
                NOT RUN
              </span>
            )}
          </div>
          <p className="text-xs text-ng-text-secondary mt-1">{check.description}</p>
        </div>
        <button 
          className="ml-4 p-1 text-ng-text-muted hover:text-white"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {expanded && (
        <div className="p-4 bg-black/40 border-t border-white/5 text-sm">
          <div className="text-ng-text-muted uppercase text-[10px] tracking-wider mb-1">Configuration Summary</div>
          <div className="text-white font-mono text-xs">{check.summary}</div>
        </div>
      )}
    </div>
  );
}
