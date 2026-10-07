import React from 'react';
import { Eye, FileText, RefreshCw, Trash2 } from 'lucide-react';
import type { DocumentMetadata } from '../../types/document';
import { StatusBadge } from '../common/StatusBadge';

interface DocumentCardProps {
  document: DocumentMetadata;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onRetry: (id: string) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document: doc,
  onSelect,
  onDelete,
  onRetry,
}) => {
  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  const isFailed = doc.status === 'failed' || doc.status === 'no_text';

  return (
    <div className="doc-card">
      <div className="doc-card-header">
        <div className="doc-file-icon">
          <FileText size={22} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 className="doc-title" title={doc.original_filename}>
            {doc.original_filename}
          </h3>
          <div className="doc-meta" style={{ marginTop: '0.25rem' }}>
            <span>{formatFileSize(doc.file_size)}</span>
            <span>•</span>
            <span>{doc.page_count > 0 ? `${doc.page_count} ${doc.page_count === 1 ? 'page' : 'pages'}` : 'Pending pages'}</span>
            <span>•</span>
            <span>{formatDate(doc.created_at)}</span>
          </div>
        </div>
      </div>

      <div style={{ margin: '0.25rem 0' }}>
        <StatusBadge status={doc.status} />
        {doc.error_message && (
          <p
            style={{
              fontSize: '0.75rem',
              color: '#f87171',
              marginTop: '0.5rem',
              lineHeight: 1.3,
              background: 'rgba(239, 68, 68, 0.1)',
              padding: '0.35rem 0.5rem',
              borderRadius: 'var(--radius-sm)',
            }}
          >
            {doc.error_message}
          </p>
        )}
      </div>

      <div className="doc-card-actions">
        <button
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
          onClick={() => onSelect(doc.id)}
        >
          <Eye size={14} /> Inspect Document
        </button>

        <div style={{ display: 'flex', gap: '0.35rem' }}>
          {isFailed && (
            <button
              className="btn-icon"
              title="Retry document processing"
              onClick={(e) => {
                e.stopPropagation();
                onRetry(doc.id);
              }}
            >
              <RefreshCw size={14} />
            </button>
          )}
          <button
            className="btn-icon"
            title="Delete document"
            style={{ color: '#f87171' }}
            onClick={(e) => {
              e.stopPropagation();
              onDelete(doc.id);
            }}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
