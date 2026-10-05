import { Info } from 'lucide-react';
import clsx from 'clsx';

interface ThresholdControlProps {
  label: string;
  value: string | number | boolean;
  type: 'select' | 'number' | 'toggle';
  options?: { label: string; value: string | boolean }[];
  onChange: (value: any) => void;
  description?: string;
  warning?: boolean;
}

export function ThresholdControl({ label, value, type, options, onChange, description, warning }: ThresholdControlProps) {
  return (
    <div className="flex flex-col py-3 border-b border-white/5 last:border-0">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-white flex items-center">
          {label}
          {warning && (
            <span className="ml-2 px-1.5 py-0.5 rounded bg-status-warning/10 text-status-warning text-[10px] font-bold uppercase">
              Demonstration Threshold
            </span>
          )}
        </label>
        
        {type === 'toggle' && (
          <button 
            onClick={() => onChange(!value)}
            className={clsx(
              "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
              value ? "bg-ng-accent" : "bg-ng-border"
            )}
          >
            <span className={clsx(
              "inline-block h-3 w-3 transform rounded-full bg-white transition-transform",
              value ? "translate-x-5" : "translate-x-1"
            )} />
          </button>
        )}

        {type === 'number' && (
          <input 
            type="number"
            value={value as number}
            onChange={(e) => onChange(parseFloat(e.target.value))}
            className="w-24 bg-black/30 border border-white/10 rounded px-2 py-1 text-sm text-white focus:border-ng-accent outline-none text-right font-mono"
          />
        )}

        {type === 'select' && options && (
          <select 
            value={String(value)}
            onChange={(e) => onChange(e.target.value)}
            className="bg-black/30 border border-white/10 rounded px-2 py-1 text-sm text-white focus:border-ng-accent outline-none"
          >
            {options.map(opt => (
              <option key={String(opt.value)} value={String(opt.value)}>{opt.label}</option>
            ))}
          </select>
        )}
      </div>

      {description && (
        <div className="text-xs text-ng-text-muted flex items-start mt-1">
          <Info className="w-3.5 h-3.5 mr-1.5 flex-shrink-0 mt-0.5" />
          <span>{description}</span>
        </div>
      )}
      
      {warning && (
        <div className="text-xs text-status-warning/80 italic mt-1 ml-5">
          These values are prototype thresholds and are not universal deployment thresholds.
        </div>
      )}
    </div>
  );
}
