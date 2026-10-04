import { useState, useMemo, useEffect } from 'react';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { FindingsFilterBar } from '../../components/findings/FindingsFilterBar';
import { FindingsTable } from '../../components/findings/FindingsTable';
import { FindingDetailDrawer } from '../../components/findings/FindingDetailDrawer';
import { api } from '../../services/api';
import type { ComprehensiveFinding, FindingCategory, FindingSeverity, FindingStatus } from '../../types';

export function Findings() {
  const [localFindings, setLocalFindings] = useState<ComprehensiveFinding[]>([]);

  useEffect(() => {
    async function loadFindings() {
      try {
        const runs = await api.getRuns();
        if (runs && runs.length > 0) {
          const latestRun = runs[0];
          const raw = await api.getFindings(latestRun.id);
          const mapped: ComprehensiveFinding[] = raw.map((r: any) => ({
            id: r.id,
            category: r.category as FindingCategory,
            severity: r.severity as FindingSeverity,
            status: r.status as FindingStatus,
            findingType: r.title,
            description: r.description,
            observed: r.observed_value,
            threshold: r.threshold,
            artifact: r.affected_asset,
            runId: r.run_id,
            timestamp: new Date().toISOString(),
            testMethod: r.method,
            limitations: r.limitations,
            evidenceSamples: []
          }));
          setLocalFindings(mapped);
        }
      } catch (err) {
        console.error(err);
      }
    }
    loadFindings();
  }, []);

  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<FindingCategory | 'All'>('All');
  const [severityFilter, setSeverityFilter] = useState<FindingSeverity | 'All'>('All');
  const [statusFilter, setStatusFilter] = useState<FindingStatus | 'All'>('All');
  
  const [sortField, setSortField] = useState<keyof ComprehensiveFinding>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  const handleSort = (field: keyof ComprehensiveFinding) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc'); // Default to desc for new sorts
    }
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setCategoryFilter('All');
    setSeverityFilter('All');
    setStatusFilter('All');
  };

  const handleStatusChange = (id: string, newStatus: FindingStatus) => {
    setLocalFindings(prev => prev.map(f => f.id === id ? { ...f, status: newStatus } : f));
  };

  const filteredFindings = useMemo(() => {
    return localFindings.filter(finding => {
      if (categoryFilter !== 'All' && finding.category !== categoryFilter) return false;
      if (severityFilter !== 'All' && finding.severity !== severityFilter) return false;
      if (statusFilter !== 'All' && finding.status !== statusFilter) return false;
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        return (
          finding.id.toLowerCase().includes(term) ||
          finding.description.toLowerCase().includes(term) ||
          finding.artifact.toLowerCase().includes(term) ||
          finding.findingType.toLowerCase().includes(term)
        );
      }
      return true;
    }).sort((a, b) => {
      let aVal: any = a[sortField] ?? '';
      let bVal: any = b[sortField] ?? '';
      
      // Basic severity sort map
      if (sortField === 'severity') {
        const severityMap = { 'Critical': 5, 'High': 4, 'Medium': 3, 'Low': 2, 'Informational': 1 };
        aVal = severityMap[a.severity] ?? 0;
        bVal = severityMap[b.severity] ?? 0;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [localFindings, searchTerm, categoryFilter, severityFilter, statusFilter, sortField, sortDirection]);

  // Derived stats
  const stats = useMemo(() => {
    const s = {
      total: localFindings.length,
      critical: 0,
      warning: 0, 
      info: 0,    
      cleared: 0,
      new: 0
    };
    localFindings.forEach(f => {
      if (f.severity === 'Critical') s.critical++;
      if (f.severity === 'High' || f.severity === 'Medium') s.warning++;
      if (f.severity === 'Low' || f.severity === 'Informational') s.info++;
      if (f.status === 'Cleared') s.cleared++;
      if (f.status === 'New') s.new++;
    });
    return s;
  }, [localFindings]);

  const selectedFinding = useMemo(() => {
    return localFindings.find(f => f.id === selectedFindingId) || null;
  }, [localFindings, selectedFindingId]);

  return (
    <div className="space-y-8 max-w-[1600px] pb-12">
      <SectionHeader 
        title="Findings"
        description="Evidence-backed issues identified during assurance runs."
      />

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-4">
          <div className="text-xs text-ng-text-muted mb-1">Total Findings</div>
          <div className="text-2xl font-bold text-white">{stats.total}</div>
        </div>
        <div className="bg-ng-panel-bg border border-status-fail/30 rounded-lg p-4">
          <div className="text-xs text-status-fail mb-1">Critical</div>
          <div className="text-2xl font-bold text-white">{stats.critical}</div>
        </div>
        <div className="bg-ng-panel-bg border border-status-warning/30 rounded-lg p-4">
          <div className="text-xs text-status-warning mb-1">Warning</div>
          <div className="text-2xl font-bold text-white">{stats.warning}</div>
        </div>
        <div className="bg-ng-panel-bg border border-blue-400/30 rounded-lg p-4">
          <div className="text-xs text-blue-400 mb-1">Informational</div>
          <div className="text-2xl font-bold text-white">{stats.info}</div>
        </div>
        <div className="bg-ng-panel-bg border border-status-pass/30 rounded-lg p-4">
          <div className="text-xs text-status-pass mb-1">Cleared</div>
          <div className="text-2xl font-bold text-white">{stats.cleared}</div>
        </div>
        <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-4 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500/10 blur-2xl rounded-full" />
          <div className="text-xs text-blue-300 mb-1">New</div>
          <div className="text-2xl font-bold text-white">{stats.new}</div>
        </div>
      </div>

      <FindingsFilterBar 
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        categoryFilter={categoryFilter}
        onCategoryChange={setCategoryFilter}
        severityFilter={severityFilter}
        onSeverityChange={setSeverityFilter}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        onClearFilters={handleClearFilters}
      />

      <FindingsTable 
        findings={filteredFindings}
        onRowClick={(f) => setSelectedFindingId(f.id)}
        sortField={sortField}
        sortDirection={sortDirection}
        onSort={handleSort}
      />

      <FindingDetailDrawer 
        finding={selectedFinding}
        onClose={() => setSelectedFindingId(null)}
        onStatusChange={handleStatusChange}
      />
    </div>
  );
}
