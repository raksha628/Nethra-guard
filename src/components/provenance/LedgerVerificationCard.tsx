import { CheckCircle2, XCircle, ShieldAlert, Loader2 } from 'lucide-react';
import type { LedgerVerificationState } from '../../types';
export function LedgerVerificationCard({ state }: { state: LedgerVerificationState }) {
  if (state.status === 'VERIFYING') {
    return (
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6 flex items-center justify-between">
        <div className="flex items-center">
          <Loader2 className="w-6 h-6 text-blue-400 mr-4 animate-spin" />
          <div>
            <h3 className="text-sm font-bold text-blue-400 tracking-wide uppercase">Verifying Ledger</h3>
            <p className="text-xs text-blue-400/80 mt-1">Recomputing cryptographic hash chains...</p>
          </div>
        </div>
      </div>
    );
  }

  if (state.status === 'VALID') {
    return (
      <div className="bg-status-pass/10 border border-status-pass/20 rounded-lg p-6 flex items-center justify-between">
        <div className="flex items-center">
          <CheckCircle2 className="w-6 h-6 text-status-pass mr-4" />
          <div>
            <h3 className="text-sm font-bold text-status-pass tracking-wide uppercase">Ledger Status: Valid</h3>
            <p className="text-xs text-status-pass/80 mt-1">All displayed ledger entries are currently verified.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-status-fail/10 border border-status-fail/20 rounded-lg p-6">
      <div className="flex items-start">
        <XCircle className="w-6 h-6 text-status-fail mr-4 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="text-sm font-bold text-status-fail tracking-wide uppercase">Ledger Status: Verification Failed</h3>
          <p className="text-sm text-status-fail/90 mt-2 leading-relaxed font-bold">
            {state.reason || 'Cryptographic chain broken. Invalid hash sequence detected.'}
          </p>
          
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="bg-black/30 p-3 rounded border border-status-fail/20">
              <div className="text-[10px] text-status-fail/70 uppercase tracking-wider mb-1">First Invalid Sequence</div>
              <div className="text-lg font-mono text-status-fail">#{String(state.firstInvalidSequence).padStart(3, '0')}</div>
            </div>
            <div className="bg-black/30 p-3 rounded border border-status-fail/20">
              <div className="text-[10px] text-status-fail/70 uppercase tracking-wider mb-1">Detection Timestamp</div>
              <div className="text-sm font-mono text-status-fail/90">{state.timestamp}</div>
            </div>
          </div>
          
          <div className="mt-4 flex items-center text-status-fail/80 text-xs">
            <ShieldAlert className="w-4 h-4 mr-2" />
            Warning: Do not trust run evidence following the broken sequence.
          </div>
        </div>
      </div>
    </div>
  );
}
