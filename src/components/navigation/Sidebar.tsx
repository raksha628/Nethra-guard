import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Briefcase, 
  PlayCircle, 
  AlertTriangle, 
  FileSearch, 
  GitCompare, 
  Network, 
  FileText 
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'Workspace', path: '/workspace', icon: Briefcase },
  { name: 'Run Assurance', path: '/run-assurance', icon: PlayCircle },
  { name: 'Findings', path: '/findings', icon: AlertTriangle },
  { name: 'Evidence', path: '/evidence', icon: FileSearch },
  { name: 'Dist. Shift', path: '/distribution-shift', icon: Network },
  { name: 'Comparator', path: '/comparator', icon: GitCompare },
  { name: 'Provenance', path: '/provenance', icon: FileText },
  { name: 'Reports', path: '/reports', icon: FileText },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-ng-panel-bg border-r border-ng-border flex flex-col h-full flex-shrink-0">
      <div className="p-6 border-b border-ng-border">
        <h1 className="text-xl font-bold tracking-wider text-white">
          NETRA<span className="text-ng-accent">-GUARD</span>
        </h1>
        <div className="mt-2 text-xs font-mono text-ng-text-muted">
          Unified CV Assurance
        </div>
      </div>

      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-ng-accent/10 text-ng-accent'
                      : 'text-ng-text-secondary hover:bg-white/5 hover:text-white'
                  )
                }
              >
                <item.icon className="w-4 h-4 mr-3" />
                {item.name}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-ng-border space-y-2">
        <div className="flex items-center justify-center py-1.5 px-3 bg-white/5 rounded text-xs font-semibold text-ng-text-secondary border border-white/10">
          <div className="w-2 h-2 rounded-full bg-status-pass mr-2" />
          OFFLINE / LOCAL
        </div>
        <div className="flex items-center justify-center py-1.5 px-3 bg-status-warning/10 text-status-warning rounded text-xs font-semibold border border-status-warning/20 uppercase tracking-widest">
          Prototype
        </div>
      </div>
    </aside>
  );
}
