import { useState, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { RunSelectorCard } from '../../components/comparator/RunSelectorCard';
import { CompatibilityCard } from '../../components/comparator/CompatibilityCard';
import { MetricDeltaTable } from '../../components/comparator/MetricDeltaTable';
import { FindingChanges } from '../../components/comparator/FindingChanges';
import { ComparatorSummary } from '../../components/comparator/ComparatorSummary';
import { ConfigComparison } from '../../components/comparator/ConfigComparison';
import { api } from '../../services/api';
import { ExternalLink } from 'lucide-react';
import type { ComparatorContext } from '../../types';

export function Comparator() {
  const [context, setContext] = useState<ComparatorContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const runs = await api.getRuns();
        if (runs && runs.length >= 2) {
          const current = runs[0];
          const baseline = runs[1]; // just use previous as baseline for demo
          
          const cmp = await api.getComparison(current.id, baseline.id);
          
          const baselineRunMeta = await api.getRun(baseline.id);
          const currentRunMeta = await api.getRun(current.id);

          setContext({
            baselineRun: {
              runId: baseline.id,
              dataset: baselineRunMeta.dataset?.asset_id || 'Unknown',
              model: baselineRunMeta.model?.asset_id || 'Unknown',
              preprocessing: 'Standard',
              configuration: baseline.configuration_hash || 'Unknown',
              timestamp: baseline.created_at || new Date().toISOString(),
              configJson: baselineRunMeta.configuration || {}
            },
            currentRun: {
              runId: current.id,
              dataset: currentRunMeta.dataset?.asset_id || 'Unknown',
              model: currentRunMeta.model?.asset_id || 'Unknown',
              preprocessing: 'Standard',
              configuration: current.configuration_hash || 'Unknown',
              timestamp: current.created_at || new Date().toISOString(),
              configJson: currentRunMeta.configuration || {}
            },
            compatibility: {
              isCompatible: cmp.compatibility.is_compatible,
              reason: cmp.compatibility.reason,
              mismatchedFields: cmp.compatibility.mismatched_fields
            },
            metricDeltas: cmp.metric_deltas.map((d: any) => ({
              metric: d.metric,
              baselineValue: d.baseline_value,
              currentValue: d.current_value,
              delta: d.delta,
              status: d.delta > 0 ? 'DEGRADED' : d.delta < 0 ? 'IMPROVED' : 'UNCHANGED'
            })),
            findingChanges: cmp.finding_changes.map((f: any) => ({
              findingId: f.finding_id,
              category: f.category,
              description: f.description,
              baselineStatus: f.baseline_status,
              currentStatus: f.current_status,
              type: f.type
            })),
            summary: cmp.summary,
            modelHashChanged: cmp.model_hash_changed
          });
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  if (isLoading) return <div className="p-8 text-white">Loading Comparator...</div>;

  if (!context) {
    return (
      <div className="space-y-8 max-w-[1400px] pb-12">
        <SectionHeader 
          title="Assurance Comparator"
          description="Compare assurance results against a compatible baseline."
        />
        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-12 text-center text-ng-text-secondary">
          Not enough runs available for comparison. You need at least 2 runs.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <SectionHeader 
          title="Assurance Comparator"
          description="Compare assurance results against a compatible baseline."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RunSelectorCard label="Baseline Run" run={context.baselineRun} />
        <RunSelectorCard label="Current Run" run={context.currentRun} />
      </div>

      <CompatibilityCard compatibility={context.compatibility} />

      {context.compatibility.isCompatible && (
        <>
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white mb-4">Metric Deltas</h3>
                <MetricDeltaTable deltas={context.metricDeltas} />
              </div>
              
              <div>
                <h3 className="text-lg font-bold text-white mb-4">Finding Changes</h3>
                <FindingChanges changes={context.findingChanges} />
              </div>

              <div>
                <h3 className="text-lg font-bold text-white mb-4">Configuration Match</h3>
                <ConfigComparison 
                  baselineConfig={context.baselineRun.configJson} 
                  currentConfig={context.currentRun.configJson} 
                />
              </div>
            </div>

            <div className="xl:col-span-1 space-y-6">
              <div className="sticky top-6 space-y-6">
                <ComparatorSummary context={context} />
                
                <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-6 space-y-3">
                  <h3 className="text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-4">Actions</h3>
                  <button className="w-full flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded text-sm text-white transition-colors">
                    View Baseline Run
                    <ExternalLink className="w-4 h-4 text-ng-text-muted" />
                  </button>
                  <button className="w-full flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded text-sm text-white transition-colors">
                    View Current Run
                    <ExternalLink className="w-4 h-4 text-ng-text-muted" />
                  </button>
                  <button className="w-full flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded text-sm text-white transition-colors">
                    View Findings Detail
                    <ExternalLink className="w-4 h-4 text-ng-text-muted" />
                  </button>
                  <button className="w-full flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded text-sm text-white transition-colors">
                    View Provenance Ledger
                    <ExternalLink className="w-4 h-4 text-ng-text-muted" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
