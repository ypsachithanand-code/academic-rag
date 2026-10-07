import React, { useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import type { NavView } from './components/layout/Sidebar';
import { DashboardView } from './components/dashboard/DashboardView';
import { DocumentLibrary } from './components/library/DocumentLibrary';
import { UploadModal } from './components/library/UploadModal';
import { DocumentDetailModal } from './components/detail/DocumentDetailModal';
import { ConfirmDialog } from './components/common/ConfirmDialog';
import { ChatView } from './components/chat/ChatView';
import { useDocuments } from './hooks/useDocuments';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<NavView>('dashboard');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  // Deletion Dialog State
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const {
    documents,
    total,
    loading,
    error,
    uploadFile,
    deleteDocument,
    retryDocument,
    refresh,
  } = useDocuments();

  const handleConfirmDelete = async () => {
    if (!deleteTargetId) return;
    setIsDeleting(true);
    try {
      await deleteDocument(deleteTargetId);
      setDeleteTargetId(null);
      if (selectedDocId === deleteTargetId) {
        setSelectedDocId(null);
      }
    } catch {
      // Handled in hook
    } finally {
      setIsDeleting(false);
    }
  };

  const targetDocToDelete = documents.find((d) => d.id === deleteTargetId);

  return (
    <AppShell
      currentView={currentView}
      onNavigate={setCurrentView}
      onOpenUpload={() => setIsUploadOpen(true)}
    >
      {currentView === 'dashboard' ? (
        <DashboardView
          documents={documents}
          total={total}
          loading={loading}
          error={error}
          onOpenUpload={() => setIsUploadOpen(true)}
          onNavigateToLibrary={() => setCurrentView('library')}
          onSelectDocument={setSelectedDocId}
          onRefresh={refresh}
        />
      ) : currentView === 'library' ? (
        <DocumentLibrary
          documents={documents}
          total={total}
          loading={loading}
          error={error}
          onOpenUpload={() => setIsUploadOpen(true)}
          onSelectDocument={setSelectedDocId}
          onDeleteDocument={setDeleteTargetId}
          onRetryDocument={retryDocument}
          onRefresh={refresh}
        />
      ) : (
        <ChatView documents={documents} />
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={uploadFile}
      />

      {/* Document Inspector Modal */}
      <DocumentDetailModal
        documentId={selectedDocId}
        onClose={() => setSelectedDocId(null)}
        onDeleteDocument={setDeleteTargetId}
        onRetryDocument={retryDocument}
      />

      {/* Deletion Confirm Dialog */}
      <ConfirmDialog
        isOpen={!!deleteTargetId}
        title="Delete Document"
        message={
          targetDocToDelete
            ? `Are you sure you want to delete "${targetDocToDelete.original_filename}"? This will permanently remove the document metadata, extracted page text, semantic chunks, and vector embeddings from storage.`
            : 'Are you sure you want to delete this document?'
        }
        confirmLabel="Delete Document"
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTargetId(null)}
        isDeleting={isDeleting}
      />
    </AppShell>
  );
};

export default App;

