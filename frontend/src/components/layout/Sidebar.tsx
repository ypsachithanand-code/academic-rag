import React from 'react';
import { LayoutDashboard, Library, MessageSquare, UploadCloud } from 'lucide-react';

export type NavView = 'dashboard' | 'library' | 'chat';

interface SidebarProps {
  currentView: NavView;
  onNavigate: (view: NavView) => void;
  onOpenUpload: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onNavigate, onOpenUpload }) => {
  return (
    <aside className="app-sidebar">
      <div>
        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '0.75rem 1rem', marginBottom: '1rem', justifyContent: 'center' }}
          onClick={onOpenUpload}
        >
          <UploadCloud size={18} />
          <span>Upload Document</span>
        </button>

        <div className="nav-section-title">Workspace</div>
        <ul className="nav-list">
          <li>
            <button
              className={`nav-item-btn ${currentView === 'dashboard' ? 'active' : ''}`}
              onClick={() => onNavigate('dashboard')}
            >
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
            </button>
          </li>
          <li>
            <button
              className={`nav-item-btn ${currentView === 'library' ? 'active' : ''}`}
              onClick={() => onNavigate('library')}
            >
              <Library size={18} />
              <span>Document Library</span>
            </button>
          </li>
        </ul>
      </div>

      <div style={{ marginTop: 'auto' }}>
        <div className="nav-section-title">AI Research</div>
        <ul className="nav-list">
          <li>
            <button
              className={`nav-item-btn ${currentView === 'chat' ? 'active' : ''}`}
              onClick={() => onNavigate('chat')}
            >
              <MessageSquare size={18} />
              <span>Research Assistant</span>
            </button>
          </li>
        </ul>
      </div>
    </aside>
  );
};
