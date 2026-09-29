import { useState } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { LedgerVerificationCard } from '../../components/provenance/LedgerVerificationCard';
import { LedgerTimeline } from '../../components/provenance/LedgerTimeline';
import { ProvenanceEntryDetails } from '../../components/provenance/ProvenanceEntryDetails';
import { TamperDemoPanel } from '../../components/provenance/TamperDemoPanel';
import { demoProvenanceEntries } from '../../services/demoProvenance';
import type { LedgerVerificationState, ProvenanceEntry } from '../../types';
import { Download } from 'lucide-react';

export function Provenance() {
  const [entries, setEntries] = useState<ProvenanceEntry[]>(demoProvenanceEntries);
  const [selectedEntryId, setSelectedEntryId] = useState<string>(demoProvenanceEntries[0].runId);
  const [verificationState, setVerificationState] = useState<LedgerVerificationState>({ status: 'VALID' });

  const selectedEntry = entries.find(e => e.runId === selectedEntryId) || entries[0];

  const handleSimulateTamper = () => {
    setVerificationState({ status: 'VERIFYING' });
    setTimeout(() => {
      // Simulate that entry 3 (RUN-2026-003) was tampered with, breaking the chain for entry 4.
      const tampered = entries.map(e => {
        if (e.sequence >= 4) {
          return { ...e, isValid: false }; // Entry 4 is invalid because 3 was altered.
        }
        return e;
      });
      setEntries(tampered);
      setVerificationState({
        status: 'FAILED',
        firstInvalidSequence: 4,
        reason: 'Hash chain broken. Current hash of sequence #003 does not match previous hash recorded in sequence #004.',
        timestamp: new Date().toISOString()
      });
    }, 1500);
  };

  const handleResetDemo = () => {
    setVerificationState({ status: 'VERIFYING' });
    setTimeout(() => {
      setEntries(demoProvenanceEntries);
      setVerificationState({ status: 'VALID' });
    }, 1000);
  };

  const handleExport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(entries, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "provenance_ledger_export.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <SectionHeader 
          title="Provenance Ledger"
          description="Trace assurance runs, assets, configurations and evidence history."
        />
        <button 
          onClick={handleExport}
          className="flex items-center self-start px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-sm text-white font-medium transition-colors"
        >
          <Download className="w-4 h-4 mr-2" />
          Export Provenance
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-6">
          <LedgerVerificationCard state={verificationState} />
          
          <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6">
            <h2 className="text-lg font-bold text-white mb-6">Ledger Timeline</h2>
            <LedgerTimeline 
              entries={entries} 
              onSelectEntry={(e) => setSelectedEntryId(e.runId)} 
              selectedEntryId={selectedEntryId}
            />
          </div>
        </div>

        <div className="xl:col-span-1 space-y-6">
          <div className="sticky top-6 space-y-6">
            <TamperDemoPanel 
              onSimulateTamper={handleSimulateTamper}
              onReset={handleResetDemo}
              isTampered={verificationState.status === 'FAILED'}
            />
            
            <div className="h-[600px]">
              <ProvenanceEntryDetails entry={selectedEntry} />
            </div>
            
            <div className="bg-black/20 p-4 rounded text-xs text-ng-text-secondary border border-white/5 text-center">
              Demo verification state. Cryptographic verification is simulated for prototype purposes.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
