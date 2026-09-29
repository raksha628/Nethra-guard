import { SectionHeader } from '../../components/ui/SectionHeader';
import { ShiftSummary } from '../../components/distribution/ShiftSummary';
import { CaveatPanel } from '../../components/distribution/CaveatPanel';
import { DistributionChart } from '../../components/distribution/DistributionChart';
import { MetricComparisonTable } from '../../components/distribution/MetricComparisonTable';
import { demoDistributionContext } from '../../services/demoDistribution';

export function DistributionShift() {
  const context = demoDistributionContext;

  return (
    <div className="space-y-8 max-w-[1400px] pb-12">
      <SectionHeader 
        title="Distribution Shift"
        description="Compare reference and current image batches to detect covariant shifts in inference data."
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 space-y-8">
          
          <div>
            <h2 className="text-lg font-bold text-white mb-4">Metric Comparison</h2>
            <MetricComparisonTable metrics={context.metricsTable} />
          </div>

          <div className="space-y-6">
            <h2 className="text-lg font-bold text-white mb-4">Distribution Visualizations</h2>
            
            <div className="grid grid-cols-1 gap-6">
              <DistributionChart 
                title="Brightness Distribution" 
                data={context.brightnessDistribution}
                xAxisLabel="Pixel Intensity Range"
                yAxisLabel="Sample Count"
              />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <DistributionChart 
                  title="RGB Statistics (Mean)" 
                  data={context.rgbDistribution}
                  yAxisLabel="Intensity Value"
                />
                <DistributionChart 
                  title="Image Dimensions" 
                  data={context.dimensionsDistribution}
                  yAxisLabel="Sample Count"
                />
              </div>
            </div>
          </div>

        </div>

        <div className="xl:col-span-1 space-y-6">
          <div className="sticky top-6 space-y-6">
            <h2 className="text-lg font-bold text-white mb-4">Shift Evaluation</h2>
            <ShiftSummary context={context} />
            <CaveatPanel 
              isControlledDemo={context.isControlledDemo}
              demoConditionName={context.demoConditionName}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
