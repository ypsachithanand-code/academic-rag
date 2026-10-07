import React from 'react';
import { Calendar, Clock, FileText, Hash, HardDrive, RefreshCw, Trash2 } from 'lucide-react';
import type { DocumentMetadata } from '../../types/document';
import { StatusBadge } from '../common/StatusBadge';

interface OverviewTabProps {
  document: DocumentMetadata;
  onRetry: () => void;
  onDelete: () => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ document: doc, onRetry, onDelete }) => {
  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
    try {
      return new Date(isoString).toLocaleString();
    } catch {
      return isoString;
    }
  };

  const isFailed = doc.status === 'failed' || doc.status === 'no_text';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* File Summary Header */}
      <div style={{ padding: '1.25rem', background: 'var(--bg-surface-hover)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', minWidth: 0 }}>
          <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', background: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={24} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, wordBreak: 'break-word' }}>{doc.original_filename}</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.25rem' }}>
              <StatusBadge status={doc.status} />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {doc.id}</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {isFailed && (
            <button className="btn btn-secondary" onClick={onRetry} style={{ fontSize: '0.8rem' }}>
              <RefreshCw size={14} /> Retry Processing
            </button>
          )}
          <button className="btn btn-danger" onClick={onDelete} style={{ fontSize: '0.8rem' }}>
            <Trash2 size={14} /> Delete
          </button>
        </div>
      </div>

      {doc.error_message && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-md)', color: '#f87171', fontSize: '0.875rem' }}>
          <strong style={{ display: 'block', marginBottom: '0.25rem' }}>Processing Error:</strong>
          {doc.error_message}
        </div>
      )}

      {/* Metadata Detail Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, marginBottom: '0.35rem' }}>
            <HardDrive size={14} /> File Size & Pages
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 700 }}>{formatFileSize(doc.file_size)}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            {doc.page_count > 0 ? `${doc.page_count} Pages Extracted` : 'Page extraction pending'}
          </div>
        </div>

        <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, marginBottom: '0.35rem' }}>
            <Calendar size={14} /> Created & Updated
          </div>
          <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{formatDate(doc.created_at)}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            Last modified: {formatDate(doc.updated_at)}
          </div>
        </div>

        <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, marginBottom: '0.35rem' }}>
            <Clock size={14} /> Pipeline Timings
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Started: {formatDate(doc.processing_started_at)}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            Completed: {formatDate(doc.processing_completed_at)}
          </div>
        </div>

        <div style={{ padding: '1rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700, marginBottom: '0.35rem' }}>
            <Hash size={14} /> SHA-256 Digest
          </div>
          <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-family-mono)', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
            {doc.sha256}
          </div>
        </div>
      </div>
    </div>
  );
};
