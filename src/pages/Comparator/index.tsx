import { useState } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { RunSelectorCard } from '../../components/comparator/RunSelectorCard';
import { CompatibilityCard } from '../../components/comparator/CompatibilityCard';
import { MetricDeltaTable } from '../../components/comparator/MetricDeltaTable';
import { FindingChanges } from '../../components/comparator/FindingChanges';
import { ComparatorSummary } from '../../components/comparator/ComparatorSummary';
import { ConfigComparison } from '../../components/comparator/ConfigComparison';
import { demoComparatorCompatible, demoComparatorIncompatible } from '../../services/demoComparator';
import { ExternalLink, ShieldAlert } from 'lucide-react';

export function Comparator() {
  const [isCompatibleDemo, setIsCompatibleDemo] = useState(true);
  const context = isCompatibleDemo ? demoComparatorCompatible : demoComparatorIncompatible;

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <SectionHeader 
          title="Assurance Comparator"
          description="Compare assurance results against a compatible baseline."
        />
        
        {/* Toggle just for demo purposes to show both states */}
        <button 
          onClick={() => setIsCompatibleDemo(!isCompatibleDemo)}
          className="flex items-center self-start px-3 py-1.5 bg-black/40 border border-white/10 rounded text-xs text-ng-text-muted hover:text-white transition-colors"
        >
          <ShieldAlert className="w-3 h-3 mr-2" />
          Toggle Demo State: {isCompatibleDemo ? 'Compatible' : 'Incompatible'}
        </button>
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
