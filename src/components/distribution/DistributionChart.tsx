import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { ChartDataPoint } from '../../types';

interface DistributionChartProps {
  title: string;
  data: ChartDataPoint[];
  xAxisLabel?: string;
  yAxisLabel?: string;
}

export function DistributionChart({ title, data, xAxisLabel, yAxisLabel }: DistributionChartProps) {
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col h-[350px]">
      <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-wider">{title}</h3>
      <div className="flex-1 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="name" 
              tick={{ fill: '#8b949e', fontSize: 11 }} 
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
              label={xAxisLabel ? { value: xAxisLabel, position: 'insideBottom', offset: -15, fill: '#8b949e', fontSize: 11 } : undefined}
            />
            <YAxis 
              tick={{ fill: '#8b949e', fontSize: 11 }} 
              axisLine={false}
              tickLine={false}
              label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft', offset: -10, fill: '#8b949e', fontSize: 11 } : undefined}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#161b22', borderColor: '#30363d', borderRadius: '6px', fontSize: '12px', color: '#fff' }}
              itemStyle={{ color: '#fff' }}
              cursor={{ fill: 'rgba(255,255,255,0.05)' }}
            />
            <Legend 
              wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              iconType="circle"
            />
            <Bar dataKey="reference" name="Reference Batch" fill="#8b949e" radius={[2, 2, 0, 0]} maxBarSize={40} />
            <Bar dataKey="current" name="Current Batch" fill="#58a6ff" radius={[2, 2, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
