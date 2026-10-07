import React, { useEffect, useState } from 'react';
import { BookOpen, Moon, Sun, Server } from 'lucide-react';
import { documentsApi } from '../../api/documents';

interface HeaderProps {
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({ theme, onToggleTheme }) => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [appVersion, setAppVersion] = useState<string>('0.1.0');

  useEffect(() => {
    let isMounted = true;
    const checkServerHealth = async () => {
      try {
        const data = await documentsApi.checkHealth();
        if (isMounted) {
          setIsOnline(data.status === 'healthy' || data.status === 'running');
          if (data.version) setAppVersion(data.version);
        }
      } catch {
        if (isMounted) setIsOnline(false);
      }
    };

    checkServerHealth();
    const interval = setInterval(checkServerHealth, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="header-brand-logo">
          <BookOpen size={20} />
        </div>
        <div>
          <span className="header-brand-title">Academic RAG</span>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginLeft: '0.5rem', fontWeight: 600 }}>
            v{appVersion}
          </span>
        </div>
      </div>

      <div className="header-actions">
        <div className={`health-badge ${isOnline ? 'online' : 'offline'}`} title={isOnline ? 'Backend API operational' : 'Backend API unavailable'}>
          <span className="indicator" />
          <Server size={14} style={{ color: 'var(--text-muted)' }} />
          <span>{isOnline ? 'API Connected' : 'API Offline'}</span>
        </div>

        <button
          className="btn-icon"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
};
