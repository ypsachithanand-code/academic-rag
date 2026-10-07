import React, { useMemo, useState } from 'react';
import { RefreshCw, Search, UploadCloud, Grid, List } from 'lucide-react';
import type { DocumentMetadata } from '../../types/document';
import { DocumentCard } from './DocumentCard';
import { EmptyState } from './EmptyState';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

interface DocumentLibraryProps {
  documents: DocumentMetadata[];
  total: number;
  loading: boolean;
  error: string | null;
  onOpenUpload: () => void;
  onSelectDocument: (id: string) => void;
  onDeleteDocument: (id: string) => void;
  onRetryDocument: (id: string) => void;
  onRefresh: () => void;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  loading,
  error,
  onOpenUpload,
  onSelectDocument,
  onDeleteDocument,
  onRetryDocument,
  onRefresh,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'processing' | 'failed'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Search filter
      const matchesSearch =
        doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.id.toLowerCase().includes(searchQuery.toLowerCase());

      // Status filter
      let matchesStatus = true;
      if (statusFilter === 'completed') {
        matchesStatus = doc.status === 'completed';
      } else if (statusFilter === 'processing') {
        matchesStatus = ['uploaded', 'processing', 'chunking', 'embedding'].includes(doc.status);
      } else if (statusFilter === 'failed') {
        matchesStatus = doc.status === 'failed' || doc.status === 'no_text';
      }

      return matchesSearch && matchesStatus;
    });
  }, [documents, searchQuery, statusFilter]);

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Academic Document Library</h1>
          <p className="page-subtitle">
            Browse and inspect your stored papers, extracted pages, semantic chunks, and vector status.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={onRefresh} title="Refresh documents list">
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
          <button className="btn btn-primary" onClick={onOpenUpload}>
            <UploadCloud size={18} />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {error && <ErrorAlert title="Failed to load document library" message={error} onRetry={onRefresh} />}

      {/* Library Controls */}
      <div className="library-controls">
        <div className="search-input-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search papers by filename or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-pills">
          <button
            className={`filter-pill ${statusFilter === 'all' ? 'active' : ''}`}
            onClick={() => setStatusFilter('all')}
          >
            All ({documents.length})
          </button>
          <button
            className={`filter-pill ${statusFilter === 'completed' ? 'active' : ''}`}
            onClick={() => setStatusFilter('completed')}
          >
            Completed ({documents.filter((d) => d.status === 'completed').length})
          </button>
          <button
            className={`filter-pill ${statusFilter === 'processing' ? 'active' : ''}`}
            onClick={() => setStatusFilter('processing')}
          >
            Processing ({documents.filter((d) => ['uploaded', 'processing', 'chunking', 'embedding'].includes(d.status)).length})
          </button>
          <button
            className={`filter-pill ${statusFilter === 'failed' ? 'active' : ''}`}
            onClick={() => setStatusFilter('failed')}
          >
            Failed ({documents.filter((d) => d.status === 'failed' || d.status === 'no_text').length})
          </button>
        </div>

        <div style={{ display: 'flex', gap: '0.25rem', background: 'var(--bg-surface)', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
          <button
            className="btn-icon"
            style={{ background: viewMode === 'grid' ? 'var(--bg-surface-elevated)' : 'transparent', border: 'none' }}
            onClick={() => setViewMode('grid')}
            title="Grid view"
          >
            <Grid size={16} />
          </button>
          <button
            className="btn-icon"
            style={{ background: viewMode === 'table' ? 'var(--bg-surface-elevated)' : 'transparent', border: 'none' }}
            onClick={() => setViewMode('table')}
            title="Table view"
          >
            <List size={16} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <LoadingSpinner label="Loading document library..." size={28} />
      ) : documents.length === 0 ? (
        <EmptyState onOpenUpload={onOpenUpload} />
      ) : filteredDocuments.length === 0 ? (
        <div className="empty-state">
          <h3>No matching documents</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
            No papers match your search "{searchQuery}" and selected filters.
          </p>
          <button className="btn btn-secondary" style={{ marginTop: '1rem' }} onClick={() => { setSearchQuery(''); setStatusFilter('all'); }}>
            Reset Filters
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="document-grid">
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              onSelect={onSelectDocument}
              onDelete={onDeleteDocument}
              onRetry={onRetryDocument}
            />
          ))}
        </div>
      ) : (
        /* Table View */
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-sidebar)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <th style={{ padding: '0.85rem 1.25rem' }}>Document Name</th>
                <th style={{ padding: '0.85rem 1rem' }}>Status</th>
                <th style={{ padding: '0.85rem 1rem' }}>Pages</th>
                <th style={{ padding: '0.85rem 1rem' }}>Size</th>
                <th style={{ padding: '0.85rem 1rem' }}>Uploaded</th>
                <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.map((doc) => (
                <tr
                  key={doc.id}
                  style={{ borderBottom: '1px solid var(--border-color)', transition: 'var(--transition-fast)' }}
                  className="table-row-hover"
                >
                  <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {doc.original_filename}
                  </td>
                  <td style={{ padding: '0.85rem 1rem' }}>
                    <span style={{ fontSize: '0.75rem' }}>{doc.status}</span>
                  </td>
                  <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>
                    {doc.page_count || '-'}
                  </td>
                  <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>
                    {formatFileSize(doc.file_size)}
                  </td>
                  <td style={{ padding: '0.85rem 1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {formatDate(doc.created_at)}
                  </td>
                  <td style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                      onClick={() => onSelectDocument(doc.id)}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
