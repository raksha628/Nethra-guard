import { Database, Box, Trash2 } from 'lucide-react';
import { HashDisplay } from './HashDisplay';
import { RegistrationStatus } from './RegistrationStatus';
import type { AssetItem } from '../../types';

interface AssetCardProps {
  asset: AssetItem;
  onRemove?: () => void;
}

export function AssetCard({ asset, onRemove }: AssetCardProps) {
  const Icon = asset.type === 'DATASET' ? Database : Box;

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-black/20 rounded border border-white/5">
            <Icon className="w-5 h-5 text-ng-text-secondary" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white tracking-wide">{asset.name}</h4>
            <div className="text-xs text-ng-text-muted mt-0.5 uppercase tracking-wider">
              {asset.type} • {asset.format}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <RegistrationStatus status={asset.status} />
          {onRemove && (
            <button 
              onClick={onRemove}
              className="text-ng-text-muted hover:text-status-fail transition-colors"
              title="Remove Asset"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-4 border-t border-white/5">
        <div>
          <div className="text-[10px] text-ng-text-muted uppercase tracking-wider mb-1">Size</div>
          <div className="text-xs font-mono text-white">{asset.size}</div>
        </div>
        <div className="col-span-2">
          <div className="text-[10px] text-ng-text-muted uppercase tracking-wider mb-1">SHA-256</div>
          {asset.hash ? (
            <HashDisplay hash={asset.hash} />
          ) : (
            <div className="text-xs text-ng-text-muted font-mono">Pending computation...</div>
          )}
        </div>
        <div>
          <div className="text-[10px] text-ng-text-muted uppercase tracking-wider mb-1">Registered</div>
          <div className="text-xs font-mono text-white">{asset.registeredAt || '---'}</div>
        </div>
      </div>
    </div>
  );
}
