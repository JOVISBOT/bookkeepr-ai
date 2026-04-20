import { Outlet } from "react-router-dom";
import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

interface LayoutProps {
  onSync?: () => void;
  isSyncing?: boolean;
  children?: ReactNode;
}

export function Layout({ onSync, isSyncing }: LayoutProps) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 lg:ml-64">
        <Header onSync={onSync} isSyncing={isSyncing} />
        <main className="p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
