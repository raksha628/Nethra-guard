import type { ReactNode } from 'react';
import clsx from 'clsx';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: string;
    direction: 'up' | 'down' | 'neutral';
  };
  className?: string;
}

export function MetricCard({ title, value, icon, trend, className }: MetricCardProps) {
  return (
    <div className={clsx("bg-ng-panel-bg border border-ng-border rounded-lg p-5 flex flex-col", className)}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-ng-text-secondary tracking-wide">{title}</h3>
        {icon && <div className="text-ng-text-muted">{icon}</div>}
      </div>
      <div className="mt-auto flex items-end justify-between">
        <div className="text-3xl font-bold text-white tracking-tight">{value}</div>
        {trend && (
          <div
            className={clsx(
              "text-sm font-medium",
              trend.direction === 'up' && "text-status-pass",
              trend.direction === 'down' && "text-status-fail",
              trend.direction === 'neutral' && "text-ng-text-muted"
            )}
          >
            {trend.value}
          </div>
        )}
      </div>
    </div>
  );
}
