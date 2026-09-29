import clsx from 'clsx';
import { AlertOctagon, AlertTriangle, Info } from 'lucide-react';

interface SeverityBadgeProps {
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const config = {
    'CRITICAL': {
      color: 'text-status-fail bg-status-fail/10 border-status-fail/20',
      icon: AlertOctagon,
    },
    'WARNING': {
      color: 'text-status-warning bg-status-warning/10 border-status-warning/20',
      icon: AlertTriangle,
    },
    'INFO': {
      color: 'text-ng-accent bg-ng-accent/10 border-ng-accent/20',
      icon: Info,
    }
  };

  const { color, icon: Icon } = config[severity];

  return (
    <div
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border',
        color,
        className
      )}
    >
      <Icon className="w-3 h-3 mr-1" />
      {severity}
    </div>
  );
}
