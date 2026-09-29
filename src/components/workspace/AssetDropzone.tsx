import { UploadCloud } from 'lucide-react';
import clsx from 'clsx';

interface AssetDropzoneProps {
  label: string;
  accept: string;
  onDrop?: () => void;
  className?: string;
}

export function AssetDropzone({ label, accept, onDrop, className }: AssetDropzoneProps) {
  return (
    <div 
      className={clsx(
        "border-2 border-dashed border-ng-border rounded-lg bg-black/10 hover:bg-black/20 hover:border-white/20 transition-colors p-8 flex flex-col items-center justify-center text-center cursor-pointer group",
        className
      )}
      onClick={onDrop}
    >
      <div className="p-3 bg-white/5 rounded-full mb-4 text-ng-text-muted group-hover:text-white transition-colors">
        <UploadCloud className="w-6 h-6" />
      </div>
      <div className="text-sm font-medium text-white mb-1">
        Click or drag to upload {label}
      </div>
      <div className="text-xs text-ng-text-secondary">
        Accepted: {accept}
      </div>
    </div>
  );
}
