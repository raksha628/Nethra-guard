import { Search, Filter, X } from 'lucide-react';
import type { FindingCategory, FindingSeverity, FindingStatus } from '../../types';

interface FindingsFilterBarProps {
  searchTerm: string;
  onSearchChange: (val: string) => void;
  categoryFilter: FindingCategory | 'All';
  onCategoryChange: (val: FindingCategory | 'All') => void;
  severityFilter: FindingSeverity | 'All';
  onSeverityChange: (val: FindingSeverity | 'All') => void;
  statusFilter: FindingStatus | 'All';
  onStatusChange: (val: FindingStatus | 'All') => void;
  onClearFilters: () => void;
}

export function FindingsFilterBar({
  searchTerm, onSearchChange,
  categoryFilter, onCategoryChange,
  severityFilter, onSeverityChange,
  statusFilter, onStatusChange,
  onClearFilters
}: FindingsFilterBarProps) {
  
  const hasActiveFilters = categoryFilter !== 'All' || severityFilter !== 'All' || statusFilter !== 'All' || searchTerm !== '';

  return (
    <div className="bg-ng-panel-bg border border-ng-border rounded-lg p-4 flex flex-col md:flex-row gap-4 items-center">
      <div className="relative flex-1 w-full">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-ng-text-muted" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-3 py-2 border border-white/10 rounded-md leading-5 bg-black/20 text-white placeholder-ng-text-muted focus:outline-none focus:border-ng-accent focus:ring-1 focus:ring-ng-accent sm:text-sm transition-colors"
          placeholder="Search by ID, finding, or artifact..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="flex flex-wrap md:flex-nowrap items-center gap-3 w-full md:w-auto">
        <div className="flex items-center space-x-2 bg-black/20 px-3 py-1.5 rounded border border-white/5 text-sm">
          <Filter className="w-4 h-4 text-ng-text-muted" />
          <select 
            value={categoryFilter} 
            onChange={(e) => onCategoryChange(e.target.value as FindingCategory | 'All')}
            className="bg-transparent border-none text-white focus:outline-none focus:ring-0 cursor-pointer"
          >
            <option value="All">All Categories</option>
            <option value="Data Integrity">Data Integrity</option>
            <option value="Model Integrity">Model Integrity</option>
            <option value="Distribution Shift">Distribution Shift</option>
            <option value="Comparator">Comparator</option>
          </select>
        </div>

        <div className="flex items-center space-x-2 bg-black/20 px-3 py-1.5 rounded border border-white/5 text-sm">
          <select 
            value={severityFilter} 
            onChange={(e) => onSeverityChange(e.target.value as FindingSeverity | 'All')}
            className="bg-transparent border-none text-white focus:outline-none focus:ring-0 cursor-pointer"
          >
            <option value="All">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
            <option value="Informational">Informational</option>
          </select>
        </div>

        <div className="flex items-center space-x-2 bg-black/20 px-3 py-1.5 rounded border border-white/5 text-sm">
          <select 
            value={statusFilter} 
            onChange={(e) => onStatusChange(e.target.value as FindingStatus | 'All')}
            className="bg-transparent border-none text-white focus:outline-none focus:ring-0 cursor-pointer"
          >
            <option value="All">All Statuses</option>
            <option value="New">New</option>
            <option value="Open">Open</option>
            <option value="Reviewed">Reviewed</option>
            <option value="Cleared">Cleared</option>
            <option value="NOT RUN">NOT RUN</option>
          </select>
        </div>

        {hasActiveFilters && (
          <button 
            onClick={onClearFilters}
            className="p-2 text-ng-text-muted hover:text-white bg-white/5 rounded transition-colors border border-white/5"
            title="Clear filters"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
