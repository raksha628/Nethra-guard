import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import clsx from 'clsx';

interface HashDisplayProps {
  hash: string;
  className?: string;
}

export function HashDisplay({ hash, className }: HashDisplayProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const truncatedHash = `${hash.slice(0, 4)}...${hash.slice(-4)}`;

  return (
    <div className={clsx("flex items-center space-x-2", className)}>
      <div 
        className="text-xs font-mono bg-black/30 px-2 py-1 rounded border border-white/5 text-ng-text-secondary cursor-help"
        title={hash}
      >
        {truncatedHash}
      </div>
      <button 
        onClick={handleCopy}
        className="p-1 text-ng-text-muted hover:text-white transition-colors hover:bg-white/5 rounded"
        title="Copy Hash"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-status-pass" /> : <Copy className="w-3.5 h-3.5" />}
      </button>
    </div>
  );
}
