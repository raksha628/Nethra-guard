import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  description?: string;
  children?: ReactNode;
}

export function SectionHeader({ title, description, children }: SectionHeaderProps) {
  return (
    <div className="flex items-center justify-between pb-4 border-b border-ng-border mb-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-white">{title}</h2>
        {description && (
          <p className="text-sm text-ng-text-muted mt-1">{description}</p>
        )}
      </div>
      {children && (
        <div className="flex items-center space-x-3">
          {children}
        </div>
      )}
    </div>
  );
}
