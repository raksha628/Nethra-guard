import { useState, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { LedgerVerificationCard } from '../../components/provenance/LedgerVerificationCard';
import { LedgerTimeline } from '../../components/provenance/LedgerTimeline';
import { ProvenanceEntryDetails } from '../../components/provenance/ProvenanceEntryDetails';
import { api } from '../../services/api';
import type { LedgerVerificationState, ProvenanceEntry } from '../../types';
import { Download } from 'lucide-react';

export function Provenance() {
  const [entries, setEntries] = useState<ProvenanceEntry[]>([]);
  const [selectedEntryId, setSelectedEntryId] = useState<string>('');
  const [verificationState, setVerificationState] = useState<LedgerVerificationState>({ status: 'VERIFYING' });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const ledger = await api.getLedger();
        
        const mapped: ProvenanceEntry[] = ledger.entries.map((item: any) => ({
          sequence: item.sequence,
          runId: item.run_id,
          timestamp: item.timestamp,
          previousHash: item.previous_hash,
          currentHash: item.current_hash,
          isValid: ledger.verification.status === 'VALID' || item.sequence < (ledger.verification.firstInvalidSequence ?? 999999),
          datasetHash: item.dataset_hash,
          modelHash: item.model_hash,
          configHash: item.config_hash,
          summaryHash: item.summary_hash,
          actorLabel: item.actor_label
        }));

        setEntries(mapped);
        if (mapped.length > 0) setSelectedEntryId(mapped[0].runId);

        setVerificationState({
          status: ledger.verification.status,
          firstInvalidSequence: ledger.verification.first_invalid_sequence,
          reason: ledger.verification.reason,
          timestamp: new Date().toISOString()
        });
      } catch (err) {
        console.error(err);
        setVerificationState({ status: 'FAILED', reason: 'Failed to fetch ledger from backend.' });
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleVerify = async () => {
    setVerificationState({ status: 'VERIFYING' });
    try {
      const result = await api.verifyLedger();
      setVerificationState({
        status: result.status,
        firstInvalidSequence: result.first_invalid_sequence,
        reason: result.reason,
        timestamp: new Date().toISOString()
      });
    } catch(err) {
      setVerificationState({ status: 'FAILED', reason: 'Failed to verify ledger.' });
    }
  };

  const selectedEntry = entries.find(e => e.runId === selectedEntryId) || entries[0];

  const handleExport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(entries, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "provenance_ledger_export.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  if (isLoading) return <div className="p-8 text-white">Loading Provenance...</div>;

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
            <div className="flex justify-between items-center mb-6">
               <h2 className="text-lg font-bold text-white">Ledger Timeline</h2>
               <button onClick={handleVerify} className="px-3 py-1 bg-ng-accent text-white text-xs rounded hover:bg-ng-accent-hover">Re-Verify Ledger</button>
            </div>
            
            {entries.length > 0 ? (
              <LedgerTimeline 
                entries={entries} 
                onSelectEntry={(e) => setSelectedEntryId(e.runId)} 
                selectedEntryId={selectedEntryId}
              />
            ) : (
              <div className="text-center text-ng-text-secondary py-12">No ledger entries found.</div>
            )}
          </div>
        </div>

        <div className="xl:col-span-1 space-y-6">
          <div className="sticky top-6 space-y-6">
            <div className="h-[600px]">
              {selectedEntry ? <ProvenanceEntryDetails entry={selectedEntry} /> : <div className="text-ng-text-secondary">No entry selected</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
