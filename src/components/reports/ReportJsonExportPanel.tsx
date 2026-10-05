import { Download, Copy, CheckCircle2, FileJson } from 'lucide-react';
import { useState } from 'react';
import type { DemoReportPayload } from '../../types';

export function ReportJsonExportPanel({ report }: { report: DemoReportPayload }) {
  const [copied, setCopied] = useState(false);

  const rawJson = JSON.stringify(report, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(rawJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(rawJson);
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `netra_guard_report_${report.metadata.runId}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center text-white font-bold">
          <FileJson className="w-5 h-5 mr-2 text-ng-accent" />
          JSON Report Export
        </div>
        <div className="text-[10px] uppercase tracking-wider font-bold bg-ng-accent/20 text-ng-accent px-2 py-1 rounded">
          Demo JSON Report
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <button 
          onClick={handleCopy}
          className="flex items-center justify-center px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/5 rounded text-sm text-white transition-colors"
        >
          {copied ? <CheckCircle2 className="w-4 h-4 mr-2 text-status-pass" /> : <Copy className="w-4 h-4 mr-2" />}
          {copied ? 'Copied to Clipboard' : 'Copy JSON'}
        </button>
        <button 
          onClick={handleDownload}
          className="flex items-center justify-center px-4 py-3 bg-ng-accent hover:bg-ng-accent-hover text-white text-sm font-bold rounded transition-colors shadow-lg shadow-ng-accent/20"
        >
          <Download className="w-4 h-4 mr-2" />
          Download JSON
        </button>
      </div>

      <div className="pt-6 mt-6 border-t border-white/5 text-center">
        <div className="inline-flex items-center text-xs font-bold text-ng-text-muted uppercase tracking-wider mb-2">
          Alternative Formats
        </div>
        <p className="text-xs text-ng-text-secondary bg-black/20 p-3 rounded border border-white/5">
          HTML / PDF — Stretch Goal
        </p>
      </div>
    </div>
  );
}
