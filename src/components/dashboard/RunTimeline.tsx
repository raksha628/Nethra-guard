import clsx from 'clsx';
import { CheckCircle2, Clock, CircleDot, AlertCircle } from 'lucide-react';
import type { TimelineEvent } from '../../types';

interface RunTimelineProps {
  events: TimelineEvent[];
}

export function RunTimeline({ events }: RunTimelineProps) {
  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-5">
      <h3 className="text-sm font-bold tracking-wide text-white mb-6">Run Timeline</h3>
      
      <div className="relative border-l border-white/10 ml-3 space-y-6">
        {events.map((event) => {
          let Icon = CircleDot;
          let color = 'text-ng-text-muted';
          let bgColor = 'bg-ng-panel-bg';

          if (event.status === 'COMPLETED') {
            Icon = CheckCircle2;
            color = 'text-status-pass';
          } else if (event.status === 'IN_PROGRESS') {
            Icon = Clock;
            color = 'text-ng-accent';
          } else if (event.status === 'ERROR') {
            Icon = AlertCircle;
            color = 'text-status-fail';
          }

          return (
            <div key={event.id} className="relative pl-6">
              <div className={clsx("absolute -left-[11px] p-0.5", bgColor, color)}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <div className={clsx(
                  "text-sm font-medium",
                  event.status === 'PENDING' ? 'text-ng-text-muted' : 'text-white'
                )}>
                  {event.label}
                </div>
                <div className="text-xs font-mono text-ng-text-muted mt-1">
                  {event.timestamp}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
