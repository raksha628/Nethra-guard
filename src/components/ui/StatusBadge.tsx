import { CheckCircle2, AlertTriangle, XCircle, MinusCircle } from 'lucide-react';
import clsx from 'clsx';

export type AssuranceStatus = 'PASS' | 'WARNING' | 'FAIL' | 'NOT RUN';

interface StatusBadgeProps {
  status: AssuranceStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = {
    'PASS': {
      color: 'text-status-pass bg-status-pass/10 border-status-pass/20',
      icon: CheckCircle2,
    },
    'WARNING': {
      color: 'text-status-warning bg-status-warning/10 border-status-warning/20',
      icon: AlertTriangle,
    },
    'FAIL': {
      color: 'text-status-fail bg-status-fail/10 border-status-fail/20',
      icon: XCircle,
    },
    'NOT RUN': {
      color: 'text-status-notrun bg-status-notrun/10 border-status-notrun/20',
      icon: MinusCircle,
    },
  };

  const { color, icon: Icon } = config[status];

  return (
    <div
      className={clsx(
        'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border',
        color,
        className
      )}
    >
      <Icon className="w-3.5 h-3.5 mr-1.5" />
      {status}
    </div>
  );
}
