import type { ReactNode } from 'react';
import { Sidebar } from '../navigation/Sidebar';
import { TopHeader } from '../navigation/TopHeader';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex h-screen bg-ng-dark-bg text-ng-text-primary overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopHeader />
        <main className="flex-1 overflow-y-auto p-6 bg-ng-dark-bg">
          {children}
        </main>
      </div>
    </div>
  );
}
