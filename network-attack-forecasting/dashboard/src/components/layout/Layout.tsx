import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

interface LayoutProps {
  onRefresh?: () => void;
  isRefreshing?: boolean;
  lastUpdated?: Date;
}

export const Layout: React.FC<LayoutProps> = ({ onRefresh, isRefreshing, lastUpdated }) => {
  const [pollingInterval, setPollingInterval] = useState<number>(10000);

  return (
    <div className="flex min-h-screen bg-[#080d1a] text-slate-100 font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar
          onRefresh={onRefresh}
          isRefreshing={isRefreshing}
          lastUpdated={lastUpdated}
          pollingInterval={pollingInterval}
          onPollingIntervalChange={setPollingInterval}
        />

        {/* Main Workspace Content */}
        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
