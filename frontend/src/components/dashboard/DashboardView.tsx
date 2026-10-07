import React from 'react';
import { ArrowRight, CheckCircle2, FileText, Layers, Loader2, UploadCloud } from 'lucide-react';
import type { DocumentMetadata } from '../../types/document';
import { StatusBadge } from '../common/StatusBadge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { MetricCard } from './MetricCard';

interface DashboardViewProps {
  documents: DocumentMetadata[];
  total: number;
  loading: boolean;
  error: string | null;
  onOpenUpload: () => void;
  onNavigateToLibrary: () => void;
  onSelectDocument: (id: string) => void;
  onRefresh: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  documents,
  total,
  loading,
  error,
  onOpenUpload,
  onNavigateToLibrary,
  onSelectDocument,
  onRefresh,
}) => {
  const completedCount = documents.filter((d) => d.status === 'completed').length;
  const processingCount = documents.filter((d) =>
    ['uploaded', 'processing', 'chunking', 'embedding'].includes(d.status)
  ).length;
  const totalPages = documents.reduce((acc, curr) => acc + (curr.page_count || 0), 0);

  const recentDocs = [...documents].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 5);

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(2)} MB`;
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Research Workspace</h1>
          <p className="page-subtitle">
            Upload, inspect, and manage your academic document corpus for grounded RAG research.
          </p>
        </div>
        <button className="btn btn-primary" onClick={onOpenUpload}>
          <UploadCloud size={18} />
          <span>Upload Academic PDF</span>
        </button>
      </div>

      {error && <ErrorAlert title="Backend Connection Issue" message={error} onRetry={onRefresh} />}

      {/* Metrics Row */}
      <div className="metrics-grid">
        <MetricCard
          label="Total Academic Documents"
          value={total}
          icon={<FileText size={24} />}
          iconBgColor="rgba(99, 102, 241, 0.15)"
          iconColor="#6366f1"
        />
        <MetricCard
          label="Completed & Indexed"
          value={completedCount}
          icon={<CheckCircle2 size={24} />}
          iconBgColor="rgba(16, 185, 129, 0.15)"
          iconColor="#10b981"
        />
        <MetricCard
          label="Currently Processing"
          value={processingCount}
          icon={<Loader2 size={24} className={processingCount > 0 ? 'spinner' : ''} />}
          iconBgColor="rgba(245, 158, 11, 0.15)"
          iconColor="#f59e0b"
        />
        <MetricCard
          label="Total Extracted Pages"
          value={totalPages}
          icon={<Layers size={24} />}
          iconBgColor="rgba(56, 189, 248, 0.15)"
          iconColor="#38bdf8"
        />
      </div>

      {/* Quick Start / Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
        {/* Upload Banner Card */}
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(56, 189, 248, 0.08))',
            border: '1px solid var(--border-accent)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.75rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.5rem' }}>
              <UploadCloud size={16} /> QUICK INGESTION
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.5rem' }}>Add New Papers to Library</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              Ingest PDF papers to extract clean page text, build semantic chunks, and generate 1024-dim BGE-M3 vector embeddings.
            </p>
          </div>
          <button className="btn btn-primary" onClick={onOpenUpload} style={{ width: 'fit-content' }}>
            <UploadCloud size={16} /> Choose PDF File
          </button>
        </div>

        {/* Recent Documents Section */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            backdropFilter: 'blur(12px)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Recent Upload Activity</h3>
            {total > 0 && (
              <button
                onClick={onNavigateToLibrary}
                style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
              >
                View Library <ArrowRight size={14} />
              </button>
            )}
          </div>

          {loading ? (
            <LoadingSpinner label="Loading document activity..." size={20} />
          ) : recentDocs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              No documents uploaded yet. Upload your first PDF to populate your library.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recentDocs.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => onSelectDocument(doc.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-color)',
                    cursor: 'pointer',
                    transition: 'var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--border-accent)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
                >
                  <div style={{ minWidth: 0, flex: 1, paddingRight: '1rem' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {doc.original_filename}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: '0.75rem', marginTop: '0.15rem' }}>
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{doc.page_count > 0 ? `${doc.page_count} pages` : 'Pending pages'}</span>
                    </div>
                  </div>
                  <StatusBadge status={doc.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
