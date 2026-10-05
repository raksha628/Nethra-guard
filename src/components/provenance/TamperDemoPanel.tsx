import { ShieldAlert, RefreshCw } from 'lucide-react';

interface TamperDemoPanelProps {
  onSimulateTamper: () => void;
  onReset: () => void;
  isTampered: boolean;
}

export function TamperDemoPanel({ onSimulateTamper, onReset, isTampered }: TamperDemoPanelProps) {
  return (
    <div className="bg-status-warning/10 border border-status-warning/30 rounded-lg p-6">
      <div className="flex items-center mb-3">
        <ShieldAlert className="w-5 h-5 text-status-warning mr-2" />
        <h3 className="font-bold text-sm tracking-wide uppercase text-status-warning">
          Controlled Verification Demonstration
        </h3>
      </div>
      
      <p className="text-sm text-status-warning/90 leading-relaxed mb-4">
        This demonstration represents verification against a modified test copy. The live ledger is not silently altered. It illustrates how the system detects broken cryptographic chains.
      </p>

      {isTampered ? (
        <button 
          onClick={onReset}
          className="flex items-center px-4 py-2 bg-black/40 hover:bg-black/60 text-white text-sm font-bold rounded transition-colors border border-white/10"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Reset Demo State
        </button>
      ) : (
        <button 
          onClick={onSimulateTamper}
          className="flex items-center px-4 py-2 bg-status-fail hover:bg-status-fail/80 text-white text-sm font-bold rounded transition-colors"
        >
          View Tampered Test Copy
        </button>
      )}
    </div>
  );
}
