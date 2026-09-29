import { useState } from 'react';
import { ChevronDown, ChevronRight, FileJson } from 'lucide-react';

interface ConfigComparisonProps {
  baselineConfig: Record<string, any>;
  currentConfig: Record<string, any>;
}

export function ConfigComparison({ baselineConfig, currentConfig }: ConfigComparisonProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-hidden">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-black/20 hover:bg-black/40 transition-colors"
      >
        <div className="flex items-center text-white font-bold text-sm">
          <FileJson className="w-4 h-4 mr-2 text-ng-text-muted" />
          Configuration Details
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4 text-ng-text-muted" /> : <ChevronRight className="w-4 h-4 text-ng-text-muted" />}
      </button>
      
      {isOpen && (
        <div className="p-4 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-4 bg-black/10">
          <div>
            <div className="text-xs text-ng-text-muted uppercase tracking-wider mb-2">Baseline Config</div>
            <div className="bg-black/30 rounded border border-white/5 h-[300px] overflow-auto p-4">
              <pre className="text-xs font-mono text-ng-text-secondary whitespace-pre-wrap">
                {JSON.stringify(baselineConfig, null, 2)}
              </pre>
            </div>
          </div>
          <div>
            <div className="text-xs text-ng-text-muted uppercase tracking-wider mb-2">Current Config</div>
            <div className="bg-black/30 rounded border border-white/5 h-[300px] overflow-auto p-4">
              <pre className="text-xs font-mono text-ng-text-secondary whitespace-pre-wrap">
                {JSON.stringify(currentConfig, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
