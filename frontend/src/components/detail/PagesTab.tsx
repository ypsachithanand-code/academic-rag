import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import type { ProcessedDocumentData } from '../../types/document';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface PagesTabProps {
  data: ProcessedDocumentData | null;
  loading: boolean;
}

export const PagesTab: React.FC<PagesTabProps> = ({ data, loading }) => {
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [copied, setCopied] = useState<boolean>(false);

  if (loading) return <LoadingSpinner label="Extracting page text..." />;

  if (!data || data.pages.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        No extracted page text available for this document.
      </div>
    );
  }

  const activePage = data.pages.find((p) => p.page_number === selectedPageNum) || data.pages[0];

  const handleCopyText = () => {
    if (activePage?.text) {
      navigator.clipboard.writeText(activePage.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Page Selector Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Select Page:</label>
          <select
            value={activePage.page_number}
            onChange={(e) => setSelectedPageNum(Number(e.target.value))}
            style={{
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
              fontWeight: 600,
              outline: 'none',
            }}
          >
            {data.pages.map((p) => (
              <option key={p.page_number} value={p.page_number}>
                Page {p.page_number} of {data.total_pages}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {activePage.text.length.toLocaleString()} characters
          </span>
          <button className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }} onClick={handleCopyText}>
            {copied ? <Check size={14} style={{ color: '#10b981' }} /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy Page Text'}</span>
          </button>
        </div>
      </div>

      {/* Page Content View */}
      <div
        style={{
          background: 'var(--bg-app)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '1.5rem',
          fontFamily: 'var(--font-family)',
          fontSize: '0.9rem',
          lineHeight: 1.6,
          color: 'var(--text-primary)',
          whiteSpace: 'pre-wrap',
          maxHeight: '420px',
          overflowY: 'auto',
        }}
      >
        {activePage.text || <em style={{ color: 'var(--text-muted)' }}>[Empty page text]</em>}
      </div>
    </div>
  );
};
