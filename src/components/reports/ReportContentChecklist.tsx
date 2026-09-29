import { Check } from 'lucide-react';

const checklistItems = [
  'Project/version',
  'Run ID',
  'Timestamp',
  'Asset hashes',
  'Configuration',
  'Checks executed',
  'Checks skipped',
  'Metric definitions',
  'Summary',
  'Findings',
  'Evidence references',
  'Provenance chain status',
  'Software versions',
  'Limitations'
];

export function ReportContentChecklist() {
  return (
    <div className="bg-black/30 border border-white/5 rounded-lg p-6">
      <h3 className="text-sm font-bold text-white mb-4 tracking-wide uppercase">Report Contents</h3>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-y-3 gap-x-6">
        {checklistItems.map(item => (
          <li key={item} className="flex items-center text-xs text-ng-text-secondary">
            <Check className="w-4 h-4 text-status-pass mr-2 flex-shrink-0" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
