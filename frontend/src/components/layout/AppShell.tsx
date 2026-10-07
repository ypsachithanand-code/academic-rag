import React, { useState } from 'react';
import { Header } from './Header';
import type { NavView } from './Sidebar';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
  currentView: NavView;
  onNavigate: (view: NavView) => void;
  onOpenUpload: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  currentView,
  onNavigate,
  onOpenUpload,
}) => {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  // Chat view manages its own internal layout — no external padding/overflow
  const isChatView = currentView === 'chat';

  return (
    <div className="app-container">
      <Sidebar currentView={currentView} onNavigate={onNavigate} onOpenUpload={onOpenUpload} />
      <div className="main-wrapper">
        <Header theme={theme} onToggleTheme={toggleTheme} />
        <main
          className={isChatView ? 'content-area content-area--chat' : 'content-area'}
        >
          {children}
        </main>
      </div>
    </div>
  );
};

