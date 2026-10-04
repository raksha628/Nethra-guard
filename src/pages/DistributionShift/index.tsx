import { useState, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { ShiftSummary } from '../../components/distribution/ShiftSummary';
import { CaveatPanel } from '../../components/distribution/CaveatPanel';
import { MetricComparisonTable } from '../../components/distribution/MetricComparisonTable';
import { api } from '../../services/api';

export function DistributionShift() {
  const [context, setContext] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const runs = await api.getRuns();
        if (runs && runs.length > 0) {
          const run = runs[0];
          const rawFindings = await api.getFindings(run.id);
          const distFindings = rawFindings.filter((f: any) => f.category === 'DISTRIBUTION_SHIFT');

          let isShift = false;
          let metricsTable = [];
          
          if (distFindings.length > 0) {
            isShift = true;
            metricsTable = distFindings.map((f: any) => ({
              id: f.id,
              metricName: f.title,
              referenceValue: f.threshold,
              currentValue: f.observed_value,
              delta: 'N/A',
              status: f.severity === 'FAIL' || f.severity === 'WARNING' ? 'FAIL' : 'PASS'
            }));
          }

          setContext({
            isShiftDetected: isShift,
            shiftScore: isShift ? distFindings[0]?.observed_value : 0,
            shiftThreshold: isShift ? distFindings[0]?.threshold : 0,
            primaryMetric: 'Statistical Distance',
            affectedFeatures: distFindings.map((f: any) => f.title),
            isControlledDemo: true,
            demoConditionName: 'Real Backend Data',
            metricsTable,
            brightnessDistribution: [],
            rgbDistribution: [],
            dimensionsDistribution: []
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

  if (isLoading) return <div className="p-8 text-white">Loading Distribution Shift...</div>;

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <SectionHeader 
        title="Distribution Shift"
        description="Compare reference and current image batches to detect covariant shifts in inference data."
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-8">
          
          {context && context.metricsTable.length > 0 ? (
            <div>
              <h2 className="text-lg font-bold text-white mb-4">Metric Comparison</h2>
              <MetricComparisonTable metrics={context.metricsTable} />
            </div>
          ) : (
             <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-12 text-center text-ng-text-secondary">
               No distribution shift metrics recorded in the current run.
             </div>
          )}

        </div>

        <div className="xl:col-span-1 space-y-6">
          <div className="sticky top-6 space-y-6">
            <h2 className="text-lg font-bold text-white mb-4">Shift Evaluation</h2>
            {context && <ShiftSummary context={context} />}
            <CaveatPanel 
              isControlledDemo={true}
              demoConditionName="Real Data Mode"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
