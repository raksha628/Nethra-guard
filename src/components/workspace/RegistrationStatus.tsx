import { CheckCircle2, Clock, XCircle } from 'lucide-react';


interface RegistrationStatusProps {
  status: 'READY' | 'NOT_READY' | 'ERROR';
}

export function RegistrationStatus({ status }: RegistrationStatusProps) {
  if (status === 'READY') {
    return (
      <div className="flex items-center text-xs font-semibold text-status-pass bg-status-pass/10 px-2 py-1 rounded border border-status-pass/20 w-fit">
        <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
        REGISTERED
      </div>
    );
  }

  if (status === 'ERROR') {
    return (
      <div className="flex items-center text-xs font-semibold text-status-fail bg-status-fail/10 px-2 py-1 rounded border border-status-fail/20 w-fit">
        <XCircle className="w-3.5 h-3.5 mr-1.5" />
        ERROR
      </div>
    );
  }

  return (
    <div className="flex items-center text-xs font-semibold text-ng-text-secondary bg-white/5 px-2 py-1 rounded border border-white/10 w-fit">
      <Clock className="w-3.5 h-3.5 mr-1.5" />
      PENDING
    </div>
  );
}
