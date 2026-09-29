import { X } from 'lucide-react';
import type { RunConfigurationState } from '../../types';

interface JsonViewerProps {
  isOpen: boolean;
  onClose: () => void;
  config: RunConfigurationState;
}

export function JsonViewer({ isOpen, onClose, config }: JsonViewerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-ng-panel-bg border border-ng-border rounded-lg shadow-xl max-w-3xl w-full flex flex-col max-h-[80vh] animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between p-4 border-b border-white/5">
          <h3 className="text-sm font-bold text-white">run_config.json</h3>
          <button onClick={onClose} className="text-ng-text-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 overflow-y-auto flex-1 bg-black/40">
          <pre className="text-xs font-mono text-ng-text-secondary whitespace-pre-wrap">
            {JSON.stringify(config, null, 2)}
          </pre>
        </div>
        <div className="p-4 border-t border-white/5 bg-ng-panel-bg flex justify-end">
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-medium rounded transition-colors border border-white/10"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
