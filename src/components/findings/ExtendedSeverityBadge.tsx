import clsx from 'clsx';
import { AlertOctagon, AlertTriangle, Info, AlertCircle, Shield } from 'lucide-react';
import type { FindingSeverity } from '../../types';

interface ExtendedSeverityBadgeProps {
  severity: FindingSeverity;
  className?: string;
}

export function ExtendedSeverityBadge({ severity, className }: ExtendedSeverityBadgeProps) {
  const config = {
    'Critical': {
      color: 'text-status-fail bg-status-fail/10 border-status-fail/20',
      icon: AlertOctagon,
    },
    'High': {
      color: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
      icon: AlertCircle,
    },
    'Medium': {
      color: 'text-status-warning bg-status-warning/10 border-status-warning/20',
      icon: AlertTriangle,
    },
    'Low': {
      color: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
      icon: Shield,
    },
    'Informational': {
      color: 'text-ng-text-secondary bg-white/5 border-white/10',
      icon: Info,
    }
  };

  const { color, icon: Icon } = config[severity] || config['Informational'];

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
