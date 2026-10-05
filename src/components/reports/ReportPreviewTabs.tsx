import { useState } from 'react';
import clsx from 'clsx';
import type { DemoReportPayload } from '../../types';

export function ReportPreviewTabs({ report }: { report: DemoReportPayload }) {
  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'metrics', label: 'Metrics' },
    { id: 'findings', label: 'Findings' },
    { id: 'evidence', label: 'Evidence' },
    { id: 'provenance', label: 'Provenance' },
    { id: 'config', label: 'Configuration' },
    { id: 'limitations', label: 'Limitations' }
  ];

  const [activeTab, setActiveTab] = useState(tabs[0].id);

  const getTabContent = () => {
    switch (activeTab) {
      case 'summary':
        return JSON.stringify(report.metadata, null, 2);
      case 'metrics':
        return JSON.stringify({ executed: report.checksExecuted, skipped: report.checksSkipped }, null, 2);
      case 'findings':
        return JSON.stringify(report.findings, null, 2);
      case 'evidence':
        return "// Evidence references mapped to findings\n" + JSON.stringify(report.findings.filter(f => f.evidenceSamples), null, 2);
      case 'provenance':
        return JSON.stringify(report.provenance, null, 2);
      case 'config':
        return JSON.stringify(report.softwareVersions, null, 2);
      case 'limitations':
        return JSON.stringify(report.limitations, null, 2);
      default:
        return '{}';
    }
  };

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg overflow-hidden flex flex-col h-[500px]">
      <div className="flex overflow-x-auto border-b border-white/5 bg-black/20 hide-scrollbar">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              "px-4 py-3 text-xs font-bold uppercase tracking-wider whitespace-nowrap transition-colors border-b-2",
              activeTab === tab.id ? "text-ng-accent border-ng-accent" : "text-ng-text-muted border-transparent hover:text-white"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-auto p-4 bg-black/40">
        <pre className="text-xs font-mono text-ng-text-secondary">
          {getTabContent()}
        </pre>
      </div>
    </div>
  );
}
