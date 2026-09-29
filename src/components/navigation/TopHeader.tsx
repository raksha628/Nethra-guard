import { HelpCircle, Activity } from 'lucide-react';

export function TopHeader() {
  return (
    <header className="h-16 bg-ng-panel-bg border-b border-ng-border flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <span className="text-xs text-ng-text-muted uppercase tracking-wider font-semibold">Workspace</span>
          <span className="text-sm font-medium px-2 py-1 bg-white/5 rounded text-white">
            default-ws-01
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-ng-text-muted uppercase tracking-wider font-semibold">Run ID</span>
          <span className="text-sm font-medium px-2 py-1 bg-white/5 rounded text-ng-text-secondary font-mono">
            rn_8f92a1
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <button 
          onClick={() => window.location.reload()}
          className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-white bg-black/40 hover:bg-black/60 border border-white/10 rounded transition-colors"
        >
          Reset Demo
        </button>

        <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-status-warning/10 text-status-warning text-xs font-semibold border border-status-warning/20">
          <Activity className="w-3.5 h-3.5" />
          <span>PROTOTYPE / CONTROLLED DEMO</span>
        </div>
        
        <div className="flex items-center space-x-2 text-xs font-medium text-ng-text-secondary">
          <div className="w-2 h-2 rounded-full bg-status-pass" />
          <span>LOCAL / OFFLINE</span>
        </div>

        <button className="p-2 text-ng-text-muted hover:text-white transition-colors rounded-md hover:bg-white/5" aria-label="Help">
          <HelpCircle className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
