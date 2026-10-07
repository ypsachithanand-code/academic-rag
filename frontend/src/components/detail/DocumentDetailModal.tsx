import React from 'react';
import { BookOpen, FileText, Layers, Sparkles, X } from 'lucide-react';
import { useDocumentDetail } from '../../hooks/useDocumentDetail';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { OverviewTab } from './OverviewTab';
import { PagesTab } from './PagesTab';
import { ChunksTab } from './ChunksTab';
import { SummaryTab } from './SummaryTab';

interface DocumentDetailModalProps {
  documentId: string | null;
  onClose: () => void;
  onDeleteDocument: (id: string) => void;
  onRetryDocument: (id: string) => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  documentId,
  onClose,
  onDeleteDocument,
  onRetryDocument,
}) => {
  const {
    document: doc,
    pagesData,
    chunksData,
    summaryData,
    activeTab,
    setActiveTab,
    loadingDoc,
    loadingTab,
    error,
    summaryError,
    generateSummary,
    reloadMetadata,
  } = useDocumentDetail(documentId);

  if (!documentId) return null;

  const handleDelete = () => {
    onDeleteDocument(documentId);
    onClose();
  };

  const handleRetry = async () => {
    await onRetryDocument(documentId);
    reloadMetadata();
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" style={{ maxWidth: '900px', height: '88vh' }} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div style={{ minWidth: 0, paddingRight: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {doc ? doc.original_filename : 'Document Inspector'}
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {documentId}</span>
          </div>
          <button className="btn-icon" onClick={onClose} aria-label="Close detail modal">
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="tab-header">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <FileText size={16} style={{ display: 'inline', marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Overview & Status
          </button>
          <button
            className={`tab-btn ${activeTab === 'pages' ? 'active' : ''}`}
            onClick={() => setActiveTab('pages')}
          >
            <BookOpen size={16} style={{ display: 'inline', marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Extracted Pages {doc?.page_count ? `(${doc.page_count})` : ''}
          </button>
          <button
            className={`tab-btn ${activeTab === 'chunks' ? 'active' : ''}`}
            onClick={() => setActiveTab('chunks')}
          >
            <Layers size={16} style={{ display: 'inline', marginRight: '0.4rem', verticalAlign: 'middle' }} />
            Semantic Chunks & BGE-M3
          </button>
          <button
            className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
            onClick={() => setActiveTab('summary')}
          >
            <Sparkles size={16} style={{ display: 'inline', marginRight: '0.4rem', verticalAlign: 'middle' }} />
            AI Grounded Summary
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {loadingDoc ? (
            <LoadingSpinner label="Loading document details..." size={28} />
          ) : error ? (
            <ErrorAlert title="Document Metadata Error" message={error} onRetry={reloadMetadata} />
          ) : !doc ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Document not found.</div>
          ) : (
            <>
              {activeTab === 'overview' && (
                <OverviewTab document={doc} onRetry={handleRetry} onDelete={handleDelete} />
              )}
              {activeTab === 'pages' && <PagesTab data={pagesData} loading={loadingTab} />}
              {activeTab === 'chunks' && <ChunksTab data={chunksData} loading={loadingTab} />}
              {activeTab === 'summary' && (
                <SummaryTab
                  summaryData={summaryData}
                  loading={loadingTab}
                  error={summaryError}
                  onGenerateSummary={generateSummary}
                />
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '0.85rem 1.5rem', borderTop: '1px solid var(--border-color)', background: 'var(--bg-sidebar)', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
