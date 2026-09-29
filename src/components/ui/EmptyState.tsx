import { FileSearch } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  primaryAction?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ title, description, primaryAction, secondaryAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-ng-border rounded-lg bg-black/10">
      <div className="bg-white/5 p-4 rounded-full mb-4 text-ng-text-muted">
        <FileSearch className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-sm text-ng-text-secondary max-w-sm mb-6">
        {description}
      </p>
      
      <div className="flex items-center space-x-4">
        {primaryAction && (
          <button 
            onClick={primaryAction.onClick}
            className="px-4 py-2 bg-ng-accent hover:bg-ng-accent-hover text-white text-sm font-medium rounded transition-colors"
          >
            {primaryAction.label}
          </button>
        )}
        {secondaryAction && (
          <button 
            onClick={secondaryAction.onClick}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded transition-colors border border-white/10"
          >
            {secondaryAction.label}
          </button>
        )}
      </div>
    </div>
  );
}
